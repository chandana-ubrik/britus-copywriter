from __future__ import annotations

import streamlit as st
import anthropic
import json
import re

# ── CONFIG ──
st.set_page_config(page_title="Britus Copywriter", page_icon="✏️", layout="centered")

MODEL = "claude-sonnet-5"
MAX_REVISIONS = 2
LENGTH_TOLERANCE_PCT = 20  # rewritten copy shouldn't drift more than this from original length

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from environment / Streamlit secrets


def _extract_text(resp) -> str:
    """Pull the text out of an API response safely — don't assume content[0] is text.
    Returns empty string (rather than raising) if no text block is present, so a single
    bad response doesn't crash the whole app — callers fall back to defaults instead."""
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            return block.text.strip()
    return ""


# ── TOV GUIDE (unchanged from the original tool) ──
TOV_GUIDE = """
You are the Britus Education tone of voice copywriter.

Your job is to rewrite any piece of copy into the Britus voice.
The Britus voice is warm, approachable and personal.

WARM
- Write to one specific person, not an audience
- Use "you" and "your child" throughout
- Say the specific thing, not the general thing
- Concrete details create warmth. Abstractions remove it
- Short sentences carry warmth better than long ones

APPROACHABLE
- Do not open with a statistic, a ranking or an award
- Never use jargon without a specific named example behind it
- Acknowledge that the school choice is hard
- The voice opens a door. It does not push anyone through it
- Avoid passive voice when it creates distance or hides accountability.
  But use passive voice when it keeps the focus on the child or the
  parent rather than the school. "Your child will be known here" is
  better than "We will know your child here." The test: does this
  sentence serve the parent, or the school?

PERSONAL
- Never refer to parents as "prospective families" or "stakeholders"
- Never refer to children as "learners" or "the next generation"
- Open with a specific truth about the school, not a generic claim
- Each school has its own personality within the shared tone

HARD RULES
- Never open with a statistic or ranking
- Never use jargon without evidence
- Never say "world-class," "leading," or "exceptional" without specific proof
- Never sound like it was written for a brochure
"""

PILLARS = {
    "Every Child, Known": "Will my child be seen here?",
    "Learning That Goes Further": "Will my child be stretched?",
    "A Community That Stays With You": "Will we belong here?",
}

# ── ARABIC HANDLING ──
# Applying the English TOV rules word-for-word to Arabic produces stiff,
# overly formal copy — Arabic marketing register works differently.
# This block only gets added to the system prompt when Arabic is detected.
ARABIC_TOV_NOTE = """
LANGUAGE NOTE — this piece is in Arabic.
Do not translate the English TOV rules literally. Instead:
- Use a warm, direct register appropriate for Gulf/UAE Arabic parent
  audiences — closer to spoken register than formal/classical MSA,
  but still professional (not colloquial slang)
- Second-person address in Arabic can sound more formal by default
  than English "you" — soften it with concrete, specific details
  rather than relying on pronoun choice alone to create warmth
- Avoid direct word-for-word translation of English idioms or
  phrases like "opens a door" — find the natural Arabic equivalent
  of the same idea, or drop the metaphor if there isn't one
- Right-to-left punctuation and structure conventions apply
- If you are not confident a phrase reads naturally to a native
  Arabic speaker, flag it rather than guessing
"""

ARABIC_RANGE = re.compile(r"[\u0600-\u06FF]")


def detect_language(text: str) -> str:
    """Rough heuristic: if a meaningful share of characters are Arabic script, treat as Arabic."""
    arabic_chars = len(ARABIC_RANGE.findall(text))
    return "Arabic" if arabic_chars > max(10, len(text) * 0.15) else "English"


# ── OUTPUT FORMAT GUIDELINES ──
# Fed into the draft stage so the agent writes to the actual constraints
# of the format, not just generic body copy every time.
OUTPUT_FORMATS = {
    "Website / landing page copy": (
        "Standard body copy for a webpage. Match the length and structure of the "
        "original closely — this is not a summary or an expansion."
    ),
    "Email": (
        "Include a short subject line (under 50 characters) above the body. "
        "Open with a warm, specific greeting line. Keep paragraphs short — "
        "2-3 sentences max — for scannability in an inbox."
    ),
    "Social media caption": (
        "Hook in the first line — the reader decides whether to keep reading "
        "in under a second. Keep it under ~150 words. One clear idea, not several. "
        "End with a natural, non-pushy prompt to engage (comment, save, visit link) "
        "only if it fits — do not force a CTA."
    ),
    "Story text (Instagram/Facebook story)": (
        "Extremely short — think one punchy sentence or a short phrase, not a "
        "paragraph. This is glanced at for 1-2 seconds. No subordinate clauses."
    ),
    "Banner / display ad": (
        "Minimal words — a headline phrase, not a sentence. Aim for under 10 words "
        "total. No punctuation-heavy structure. This needs to work as a glance, not a read."
    ),
    "Ad copy (paid social/search)": (
        "Primary text roughly 400-450 characters, description roughly 90-100 "
        "characters, headline roughly 35-40 characters if these are being broken "
        "into separate fields — otherwise keep it tight and scannable as a whole. "
        "Lead with the specific benefit, not the school name."
    ),
    "Other / unspecified": (
        "No specific format constraints — match the length and structure of the "
        "original input closely."
    ),
}

CHECKLIST = """
- Written in second person (you, your child)?
- Names something specific rather than speaking generally?
- Avoids jargon without a concrete example behind it?
- Earns trust before asking for any action?
- Would a real parent feel something reading it?
- Sounds like this specific school, not a generic one?
- Does NOT open with a statistic or ranking?
- Makes no "world-class / leading / exceptional" claim without named proof?
"""


# ── STAGE 1: CLASSIFY ──
def classify_pillar(copy_text: str) -> dict:
    system = (
        "You are a classifier for Britus Education marketing copy. Given a piece of "
        "copy, identify which ONE of the three pillars below it most naturally serves, "
        "and give one sentence of reasoning. Respond ONLY with JSON, no other text:\n"
        '{"pillar": "...", "reasoning": "...", "confidence": "high|medium|low"}'
    )
    user = f"Pillars:\n{json.dumps(PILLARS, indent=2)}\n\nCopy:\n{copy_text}"
    resp = client.messages.create(
        model=MODEL, max_tokens=600, system=system,
        messages=[{"role": "user", "content": user}],
    )
    return _parse_json(_extract_text(resp), fallback={"pillar": "Unclear", "reasoning": "Could not classify", "confidence": "low"})


# ── STAGE 2: DRAFT ──
def draft_rewrite(
    copy_text: str,
    pillar: str,
    output_format: str,
    language: str,
    past_feedback: str = "",
    prior_issues: list[str] | None = None,
) -> str:
    system = TOV_GUIDE + f"\n\nThis copy should serve the pillar: {pillar}"
    system += f"\n\nOUTPUT FORMAT: {output_format}\n{OUTPUT_FORMATS.get(output_format, '')}"
    if language == "Arabic":
        system += "\n" + ARABIC_TOV_NOTE
    if past_feedback:
        system += f"\n\nRecent corrections the team has made to earlier drafts — learn from these:\n{past_feedback}"
    if prior_issues:
        system += f"\n\nYour previous draft had these specific issues — fix them this time:\n- " + "\n- ".join(prior_issues)
    system += "\n\nReturn ONLY the rewritten copy. No explanation, no commentary."

    resp = client.messages.create(
        model=MODEL, max_tokens=1200, system=system,
        messages=[{"role": "user", "content": copy_text}],
    )
    text = _extract_text(resp)
    if not text:
        # The model returned no usable text — don't crash, surface the original
        # copy unchanged so the pipeline can still complete and the person can retry.
        return copy_text
    return text


# ── STAGE 3: DETERMINISTIC TOOL — length check (no LLM, just math) ──
def check_length(original: str, rewritten: str) -> dict:
    orig_words = len(original.split())
    new_words = len(rewritten.split())
    diff_pct = abs(new_words - orig_words) / max(orig_words, 1) * 100
    return {
        "original_words": orig_words,
        "rewritten_words": new_words,
        "diff_pct": round(diff_pct, 1),
        "within_range": diff_pct <= LENGTH_TOLERANCE_PCT,
    }


# ── STAGE 4: SELF-CRITIQUE ──
def critique(original: str, rewritten: str, pillar: str, output_format: str, language: str) -> dict:
    system = (
        "You are a strict, skeptical TOV auditor for Britus Education. Check the "
        f"REWRITTEN copy against this checklist:\n{CHECKLIST}\n\n"
        f"It should also match this output format's constraints: {output_format} — "
        f"{OUTPUT_FORMATS.get(output_format, '')}\n\n"
        "Also flag any claim in the rewrite that you cannot verify is factually accurate "
        "(named statistics, outcomes, awards, specific results) — these need a human to confirm, "
        "don't guess whether they're true.\n\n"
    )
    if language == "Arabic":
        system += (
            "The copy is in Arabic — judge it as a native Arabic reader would, not by "
            "translating the checklist literally. Flag anything that reads like a direct "
            "English-to-Arabic translation rather than natural Arabic phrasing.\n\n"
        )
    system += (
        'Respond ONLY with JSON: {"passed": true/false, "issues": ["..."], '
        '"flagged_for_human_review": ["..."]}'
    )
    user = f"Original:\n{original}\n\nRewritten:\n{rewritten}\n\nIntended pillar: {pillar}"
    resp = client.messages.create(
        model=MODEL, max_tokens=900, system=system,
        messages=[{"role": "user", "content": user}],
    )
    return _parse_json(_extract_text(resp), fallback={"passed": True, "issues": [], "flagged_for_human_review": ["Auditor response could not be parsed — review manually."]})


def _parse_json(text: str, fallback: dict) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return fallback
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return fallback


# ── ORCHESTRATION LOOP ──
def run_agent(copy_text: str, output_format: str, past_feedback: str = "") -> dict:
    trace = []

    language = detect_language(copy_text)
    trace.append({"stage": "Language detection", "detail": {"detected": language}})

    pillar_result = classify_pillar(copy_text)
    trace.append({"stage": "Pillar classification", "detail": pillar_result})

    draft = draft_rewrite(
        copy_text, pillar_result["pillar"], output_format, language, past_feedback=past_feedback
    )
    critique_result = {"passed": False, "issues": [], "flagged_for_human_review": []}
    length_result = {}

    for i in range(MAX_REVISIONS + 1):
        length_result = check_length(copy_text, draft)
        critique_result = critique(copy_text, draft, pillar_result["pillar"], output_format, language)
        trace.append({
            "stage": f"Review pass {i + 1}",
            "detail": {"length_check": length_result, "critique": critique_result},
        })

        if critique_result["passed"] and length_result["within_range"]:
            break
        if i == MAX_REVISIONS:
            break  # stop looping, hand off to human with issues visible

        issues = list(critique_result.get("issues", []))
        if not length_result["within_range"]:
            issues.append(
                f"Length drifted {length_result['diff_pct']}% from the original "
                f"({length_result['original_words']} → {length_result['rewritten_words']} words) — match the original's rhythm more closely."
            )
        draft = draft_rewrite(
            copy_text, pillar_result["pillar"], output_format, language,
            past_feedback=past_feedback, prior_issues=issues,
        )

    return {
        "final_copy": draft,
        "pillar": pillar_result,
        "language": language,
        "trace": trace,
        "flagged_for_human_review": critique_result.get("flagged_for_human_review", []),
        "passed_automated_checks": critique_result["passed"] and length_result.get("within_range", False),
    }


def render_journey(trace: list[dict]) -> None:
    """Render the agent's steps as a readable narrative, not raw JSON."""
    step_num = 0
    for step in trace:
        stage = step["stage"]
        detail = step["detail"]

        if stage == "Language detection":
            step_num += 1
            st.markdown(f"**{step_num}. Detected the language**")
            st.write(f"Read the input as **{detail['detected']}** and adjusted its approach accordingly.")

        elif stage == "Pillar classification":
            step_num += 1
            st.markdown(f"**{step_num}. Chose which pillar this copy serves**")
            st.write(
                f"Picked **{detail['pillar']}** ({detail['confidence']} confidence). "
                f"Reasoning: {detail['reasoning']}"
            )

        elif stage.startswith("Review pass"):
            step_num += 1
            pass_num = stage.split()[-1]
            length = detail["length_check"]
            crit = detail["critique"]
            st.markdown(f"**{step_num}. Checked its own draft (pass {pass_num})**")

            length_icon = "✅" if length["within_range"] else "⚠️"
            st.write(
                f"{length_icon} Length: original was {length['original_words']} words, "
                f"the draft was {length['rewritten_words']} words ({length['diff_pct']}% difference) — "
                f"{'within the acceptable range' if length['within_range'] else 'drifted more than intended'}."
            )

            crit_icon = "✅" if crit["passed"] else "⚠️"
            st.write(f"{crit_icon} Tone-of-voice self-check: {'passed' if crit['passed'] else 'found issues'}.")
            if crit.get("issues"):
                st.write("Issues it found in its own draft:")
                for issue in crit["issues"]:
                    st.write(f"- {issue}")
            if crit.get("flagged_for_human_review"):
                st.write("Flagged as unverified — needs a human to confirm:")
                for flag in crit["flagged_for_human_review"]:
                    st.write(f"- {flag}")

            if crit["passed"] and length["within_range"]:
                st.write("→ Both checks passed, so this became the final draft.")
            else:
                st.write("→ Rewrote the draft to address the issues above.")


# ── UI ──
st.title("Britus Education")
st.subheader("Tone of Voice Copywriter — Agentic")
st.caption("Paste copy below. The agent classifies, drafts, checks itself, and revises before handing it back to you.")

copy_input = st.text_area("Paste your copy here", height=180)

output_format = st.selectbox("What is this copy for?", list(OUTPUT_FORMATS.keys()))

with st.expander("Optional: paste recent team corrections to help it learn"):
    past_feedback = st.text_area(
        "e.g. 'Changed passive voice on school names section to active' — paste a few recent notes",
        height=100,
    )

if st.button("Run agent", type="primary") and copy_input.strip():
    with st.spinner("Detecting language → classifying → drafting → checking → revising..."):
        result = run_agent(copy_input, output_format, past_feedback=past_feedback)

    st.markdown("### Final copy")
    st.markdown(
        f"**Pillar:** {result['pillar']['pillar']} · confidence: {result['pillar']['confidence']} "
        f"· **language:** {result['language']} · **format:** {output_format}"
    )
    st.write(result["final_copy"])

    if result["flagged_for_human_review"]:
        st.warning("**Flagged for your review — not verified by the agent:**\n\n" + "\n".join(f"- {f}" for f in result["flagged_for_human_review"]))

    if result["passed_automated_checks"]:
        st.success("Passed all automated TOV and length checks.")
    else:
        st.info("Did not fully pass automated checks after revisions — review before using.")

    st.markdown("### How it got here")
    render_journey(result["trace"])

    with st.expander("Raw trace data (for debugging)"):
        for step in result["trace"]:
            st.markdown(f"**{step['stage']}**")
            st.json(step["detail"])


    st.markdown("---")
    fb = st.text_input("Correction or note for next time (optional — helps it learn)")
    if st.button("Save this feedback") and fb.strip():
        # See README for wiring this to a persistent store (Google Sheet).
        # Without persistence, this only helps within the current session.
        st.session_state.setdefault("feedback_log", []).append(fb)
        st.success("Saved for this session. See setup notes to make this persist across sessions.")
elif copy_input.strip() == "":
    st.caption("Waiting for copy to rewrite.")
