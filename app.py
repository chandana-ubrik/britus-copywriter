import streamlit as st
import anthropic
import base64
from pathlib import Path

# ── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Britus Copywriter",
    page_icon="✏️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Base */
  [data-testid="stAppViewContainer"] { background: #F5F0E8; }
  [data-testid="stSidebar"] { background: #021831 !important; }
  [data-testid="stSidebar"] * { color: #E8EFF5 !important; }
  [data-testid="stSidebar"] .sidebar-wordmark { color: #098CFF !important; }

  /* Sidebar text */
  .sidebar-wordmark {
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #098CFF;
    margin-bottom: 4px;
  }
  .sidebar-meta {
    font-size: 11px;
    color: #5C7A96 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .sidebar-rule {
    border: none;
    border-top: 1px solid #2A3F55;
    margin: 14px 0;
  }
  .sidebar-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #5C7A96 !important;
    margin-bottom: 6px;
  }
  .sidebar-pill {
    display: inline-block;
    background: #1A3250;
    border: 1px solid #2A3F55;
    color: #98B0C4 !important;
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 3px;
    margin: 2px 2px 2px 0;
  }

  /* Main */
  .page-title {
    font-size: 28px;
    font-weight: 800;
    color: #021831;
    letter-spacing: -0.02em;
    margin-bottom: 4px;
  }
  .page-sub {
    font-size: 14px;
    color: #5C7A96;
    margin-bottom: 0;
  }

  /* Output area */
  .output-wrap {
    background: #FFFFFF;
    border: 1px solid #C8D8E5;
    border-radius: 6px;
    overflow: hidden;
    margin-top: 8px;
  }
  .output-header {
    background: #021831;
    padding: 10px 18px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #5C7A96;
  }
  .output-copy {
    padding: 24px;
    font-size: 16px;
    line-height: 1.7;
    color: #021831;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .output-copy[dir="rtl"] {
    font-family: 'Segoe UI', Tahoma, Arial, sans-serif;
    font-size: 17px;
    line-height: 1.9;
  }

  /* Thinking expander */
  .thinking-row {
    font-size: 13px;
    color: #4A6070;
    margin-bottom: 6px;
    line-height: 1.6;
  }
  .thinking-label {
    font-weight: 600;
    color: #021831;
  }

  /* Buttons */
  [data-testid="baseButton-primary"] {
    background: #098CFF !important;
    border: none !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
  }
  [data-testid="baseButton-secondary"] {
    border-color: #C8D8E5 !important;
  }

  /* Input labels */
  label { font-weight: 600 !important; font-size: 13px !important; color: #021831 !important; }

  /* Dividers */
  hr { border-color: #C8D8E5 !important; }
</style>
""", unsafe_allow_html=True)


# ── SYSTEM PROMPT ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are the Britus Education copywriter at Ubrik, the brand agency responsible for Britus Education's marketing and admissions communications.

Your job is to write original, on-brand copy for Britus Education and its schools. Not rewrite or translate existing copy. The user gives you a school, pillar, format, platform, language, funnel stage, audience, and angle. You write the copy from scratch, ready to use or adapt.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ABOUT BRITUS EDUCATION

Britus Education is a private school group with 10 schools across Saudi Arabia, the UAE, Bahrain and Tunisia.

Two levels:
- Group brand: Britus Education. Internal positioning: "To know a child is to change everything possible for them." Public tagline: "Learning Without Limits."
- Each school has its own name, community, and character. The voice is shared. The personality belongs to each school.

The ten schools:
- Education Castle International School (ECIS), Riyadh, KSA
- Leadership International School (LIS), Riyadh, KSA
- Britus Al Olaya (BISO), Riyadh, KSA
- Education Gate International School (EGIS), Riyadh, KSA
- Belvedere British School, Abu Dhabi, UAE
- BISB, Bahrain
- BISSE, Bahrain (specialist SEN school)
- BIST, Tunis, Tunisia
- Sheffield Private School, Dubai, UAE
- Rowad Al Farabi, Riyadh, KSA

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THE THREE PILLARS

Pillar 1: Every Child Is Known
Core question this answers: "Will my child be seen here?"
Topics: teacher relationships, personalised learning, student care, wellbeing, admissions experience, parent communication, inclusion, individual attention.

Pillar 2: Skills for the World Ahead
Core question this answers: "Will my child be stretched and prepared for what comes next?"
Topics: academic results, university destinations, named programmes, enrichment, innovation, critical thinking, character development, digital literacy.

Pillar 3: Roots That Last a Lifetime
Core question this answers: "Will we belong somewhere?"
Topics: multicultural community, parent partnership, belonging, alumni, family atmosphere, continuity, safety, a school that stays part of a child's story.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THE BRITUS VOICE

Three words: warm, approachable, personal.

Warm:
- Write to one person, not an audience
- Use "you" and "your child" throughout
- Name the specific thing: the programme, the person, the event
- Short sentences. Read it aloud. If it sounds like a person talking, it works.

Approachable:
- Never open with a stat, ranking, or award
- No jargon without a specific example behind it
- The voice opens a door. It does not push anyone through it.
- Avoid passive voice when it hides who is doing what
- Use passive voice when it keeps focus on the child, not the school

Personal:
- Never say "prospective families" or "stakeholders"
- Never say "learners" or "the next generation"
- Open with a specific truth, not a claim
- Each school sounds like itself

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WRITING STYLE

Write like a human copywriter. Not like AI.

Banned constructions:
- No em dashes anywhere. Use a comma, a full stop, or rewrite the sentence.
- No "it is not just X, it is Y"
- No "not only... but also"
- No "where every child..." as an opener
- No "discover" as a CTA verb
- No "journey" when you mean school experience
- No "holistic" without a specific example
- No "nurturing environment"
- No "dedicated team"
- No "committed to excellence"
- No "world-class"
- No "innovative approach"
- No "state-of-the-art"
- No rhetorical questions that answer themselves
- No copy that sounds like it was written by a committee
- No passive constructions that hide who is doing what
- Do not pad. Do not repeat. Do not summarise what you just said.
- If a sentence does not earn its place, cut it.

Write the way a sharp, experienced school copywriter would write. Specific. Direct. Warm without being sentimental. Confident without being boastful.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT ALL PARENTS SHARE

- University outcomes are the north star for every parent
- Belonging matters as much as results
- Word of mouth drives more decisions than any ad
- The decision starts before the school knows the family exists

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FUNNEL STAGE GUIDANCE

Awareness (TOFU):
- Parent may not know Britus at all
- Lead with emotion and belonging, not facts
- No hard CTA. Soft close or no CTA.
- Build curiosity, not urgency

Consideration (MOFU):
- Parent is comparing schools
- Lead with a specific proof point or differentiator
- Soft CTA: book a tour, learn more, visit us
- Address a specific concern they likely have

Decision / Conversion (BOFU):
- Parent is ready to act or nearly ready
- Lead with urgency or a clear benefit
- Direct CTA: apply now, register today, secure your place
- Remove friction, answer the final objection

Retargeting:
- Parent has already shown interest
- Acknowledge they have been looking
- Remind them what makes this school right for their child
- Clear CTA, low pressure

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

FORMAT GUIDANCE

Social caption, Instagram static post:
2 to 4 short sentences. One idea. Strong opening line. End with a soft CTA or a question.

Social caption, Instagram carousel:
Slide 1: one line hook. Slides 2 to 4: one idea per slide, 1 to 2 sentences. Final slide: CTA or closing statement. Label each slide: Slide 1, Slide 2 etc.

Social caption, Instagram Reel:
1 to 2 lines max. Energy led. Present tense. Optional hashtags at the end.

Social caption, Instagram Story text:
1 line. Max 8 words. Works over an image or video. Optional CTA sticker text.

Social caption, Facebook post:
3 to 5 sentences. Slightly more context than Instagram. One CTA at the end.

LinkedIn post:
Opening line hooks without clickbait. 3 to 5 short paragraphs. One idea each. Thought leadership tone. Confident, not salesy. Attributed to school leadership or Britus group. End with a question or forward-looking statement.

Meta ad, primary text:
1 to 3 sentences. Lead with the parent's concern, not the school's offer. No jargon. No superlatives without proof. Soft CTA at the end.

Meta ad, headline:
Max 27 characters. One clear promise.

Meta ad, description:
1 sentence. Supports the headline. Adds one specific detail.

Meta ad, image text:
Write 3 options. Each option = main text + sub-line. Label them: Option 1, Option 2, Option 3.
Main image text: max 5 to 6 words. Works instantly at a glance. Emotional or benefit led.
Sub-line (optional): max 8 to 10 words. Adds one specific detail or CTA.

Google display ad:
Headline: max 30 characters. Direct. Benefit led.
Description: max 90 characters. One proof point or reassurance.

Google search ad:
Headline 1 (30 chars): keyword + school name or location.
Headline 2 (30 chars): key benefit or differentiator.
Headline 3 (30 chars): CTA.
Description 1 (90 chars): expand on the benefit. Specific.
Description 2 (90 chars): social proof or urgency. Honest.
Label each line clearly.

Website hero:
Headline: 6 to 10 words. Names the audience or the promise.
Sub-line: 1 to 2 sentences. The school's one-sentence identity.
CTA 1 (primary): action verb + what they get.
CTA 2 (secondary): softer alternative.

Landing page hero:
Headline: campaign specific. Speaks to one parent concern.
Sub-line: 1 sentence. Backs up the headline with a specific detail.
CTA: clear, direct, single action.

Website section copy:
Section label (optional, 2 to 4 words).
Heading: 6 to 10 words.
Body: 2 to 3 sentences. One proof point. No lists unless essential.

Meta title and description (SEO):
Title: max 60 characters. School name + keyword + location.
Meta description: max 155 characters. One benefit + one CTA.
Label each.

Email, admissions:
Subject line: max 50 characters. Curiosity or benefit led.
Preview text: 1 sentence, max 90 characters.
Body: Para 1: acknowledge where the parent is in the decision. Para 2: what the school offers, specific and relevant. Para 3: what happens next, simple, no pressure.
Sign off: warm, named if possible. CTA: one clear action.

Email subject line only:
3 to 6 words. Benefit or curiosity led. No clickbait. Write 3 options.

WhatsApp message:
Max 3 sentences. Direct. Warm. Conversational. No formal language. No jargon.

SMS:
Max 160 characters including spaces. One message + one link.

Brochure panel:
Heading: 4 to 8 words. Bold, specific, human.
Body: 2 to 3 sentences max. One named proof point.

Pull quote or OOH tagline:
5 to 10 words. Works with no context. Standalone impact. Write 3 options.

Event banner headline:
3 to 6 words. Warm, not corporate. Write 2 options: one awareness, one conversion.

Video script:
Opening (0–3s): hook. Works with visuals.
Body (3–25s): 3 to 4 short statements. Spoken, not written.
Closing (25–30s): CTA or emotional close.
Label timecodes. Write for the ear.

Video caption:
1 line. Describes or teases the video. Present tense. Warm.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ARABIC WRITING RULES

When the output language is Arabic, apply all the above AND:

Language and register:
- Write in Modern Standard Arabic (MSA), formal but warm
- For KSA and Bahrain schools: formal MSA, not Gulf dialect
- For BIST Tunisia: clean MSA unless specified otherwise
- Never translate English copy word for word. Write as a native Arabic speaker would say it to a parent.

Tone in Arabic:
- Directness is warmth in Arabic. Avoid flowery language.
- Use "طفلك" and "أنت" throughout
- Short sentences. Do not write long nested sentences.
- Sounds like a trusted school talking to a parent. Not a government office.

Arabic hard rules:
- No "أفضل مدرسة" without specific proof
- No "متميز" as a standalone claim
- No "نخبة"
- No statistics as openers
- No corporate Arabic that reads like a press release
- CTAs should be direct: "احجز زيارتك" not a long polite construction

Arabic format notes:
- Social captions: emojis are fine and widely used
- WhatsApp: very conversational. Short.
- Ad headlines: aim for 5 to 7 words max. Arabic script takes more space.
- Email: "عزيزي ولي الأمر" for formal, "أهلاً" for warmer open
- Write in Arabic script only. No transliteration.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

OUTPUT FORMAT

Structure your response in exactly two parts, in this order:

PART 1: COPY
Write the final copy first. Nothing else in this section.
No commentary. No meta-labels other than what the format itself requires (e.g. "Slide 1:", "Headline:", "CTA:").
If Arabic output: write in Arabic script only.
If English and Arabic: write English first, then a blank line, then Arabic.

PART 2: THINKING
Show your craft notes after the copy. Format exactly like this (one line each):

School read: [this school's voice and character in one sentence]
Audience: [who you wrote for and what they care about most]
Pillar: [which pillar you led with and why]
Funnel stage: [how the stage shaped the copy, or "not specified"]
Format: [what the format demanded structurally]
Language approach: [register and tone decisions made]
Angle: [what the user wanted to say, distilled to one sentence]
TOV choices: [specific voice rules that guided the copy]
What was avoided: [what you ruled out and why]
"""

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    try:
        logo_path = Path("ubrik_logo.png")
        if logo_path.exists():
            logo_data = base64.b64encode(logo_path.read_bytes()).decode()
            st.markdown(
                f'<img src="data:image/png;base64,{logo_data}" width="110" style="margin-bottom:16px">',
                unsafe_allow_html=True,
            )
    except Exception:
        pass

    st.markdown('<div class="sidebar-wordmark">Britus Education</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-meta">Copy Studio</div>', unsafe_allow_html=True)
    st.markdown('<hr class="sidebar-rule">', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">Voice</div>', unsafe_allow_html=True)
    for word in ["Warm", "Approachable", "Personal"]:
        st.markdown(f'<span class="sidebar-pill">{word}</span>', unsafe_allow_html=True)

    st.markdown('<hr class="sidebar-rule">', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">Messaging Pillars</div>', unsafe_allow_html=True)
    for p in ["Every Child Is Known", "Skills for the World Ahead", "Roots That Last a Lifetime"]:
        st.markdown(f'<span class="sidebar-pill">{p}</span>', unsafe_allow_html=True)

    st.markdown('<hr class="sidebar-rule">', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-label">Positioning</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:12px;color:#98B0C4;font-style:italic;line-height:1.6">'
        '"To know a child is to change everything possible for them."'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<hr class="sidebar-rule">', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:11px;color:#5C7A96">Britus × Ubrik · 2026</div>',
        unsafe_allow_html=True,
    )


# ── MAIN ─────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">Britus Copywriter</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-sub">Fill in the brief. Get copy in the Britus voice, ready to use.</div>',
    unsafe_allow_html=True,
)
st.divider()

# Row 1
col1, col2 = st.columns(2)
with col1:
    school = st.selectbox(
        "School",
        [
            "Group / Britus Education",
            "Education Castle International School (ECIS)",
            "Leadership International School (LIS)",
            "Britus Al Olaya (BISO)",
            "Education Gate International School (EGIS)",
            "Belvedere British School",
            "BISB Bahrain",
            "BISSE Bahrain",
            "BIST Tunisia",
            "Sheffield Private School",
            "Rowad Al Farabi",
        ],
    )
with col2:
    pillar = st.selectbox(
        "Messaging pillar",
        [
            "Decide based on the angle",
            "Pillar 1: Every Child Is Known",
            "Pillar 2: Skills for the World Ahead",
            "Pillar 3: Roots That Last a Lifetime",
        ],
    )

# Row 2
col3, col4 = st.columns(2)
with col3:
    content_format = st.selectbox(
        "Format",
        [
            "── Social ──",
            "Social caption — Instagram static post",
            "Social caption — Instagram carousel",
            "Social caption — Instagram Reel",
            "Social caption — Instagram Story text",
            "Social caption — Facebook post",
            "LinkedIn post",
            "── Paid Media ──",
            "Meta ad — primary text",
            "Meta ad — headline",
            "Meta ad — description",
            "Meta ad — image text (3 options)",
            "Google Display ad",
            "Google Search ad",
            "── Website ──",
            "Website hero",
            "Landing page hero",
            "Website section copy",
            "Meta title + description (SEO)",
            "── Email ──",
            "Email — admissions (full)",
            "Email — subject line (3 options)",
            "Newsletter intro paragraph",
            "── Messaging ──",
            "WhatsApp message",
            "SMS",
            "── Print / Collateral ──",
            "Brochure panel",
            "Pull quote / OOH tagline (3 options)",
            "Event banner headline (2 options)",
            "── Video ──",
            "Video script (30 sec)",
            "Video caption",
        ],
    )
with col4:
    platform = st.selectbox(
        "Platform",
        [
            "Instagram",
            "Facebook",
            "Instagram and Facebook",
            "LinkedIn",
            "Google",
            "WhatsApp",
            "SMS",
            "Email",
            "Website",
            "Landing page",
            "Print / Brochure",
            "Outdoor / OOH",
            "Video / YouTube",
            "TikTok",
        ],
    )

# Row 3
col5, col6 = st.columns(2)
with col5:
    language = st.selectbox(
        "Language",
        ["English", "Arabic", "English and Arabic"],
    )
with col6:
    funnel_stage = st.selectbox(
        "Funnel stage",
        [
            "Not specified",
            "Awareness (TOFU)",
            "Consideration (MOFU)",
            "Decision / Conversion (BOFU)",
            "Retargeting",
        ],
    )

# Row 4 — audience + angle
audience = st.text_input(
    "Audience (optional)",
    placeholder="e.g. Saudi national families, South Asian expat parents in Riyadh, Arabic-speaking parents...",
)

angle = st.text_area(
    "What do you want to say?",
    height=110,
    placeholder=(
        "Describe the angle, the key message, or the feeling you want to leave the reader with.\n"
        "e.g. Highlight the open-door teacher policy. Warm tone. No hard sell. "
        "Mention that admissions are open for 2026–27."
    ),
)

generate = st.button("Write copy", type="primary", use_container_width=False)

# ── GENERATION ───────────────────────────────────────────────────────────────
if generate:
    if not angle.strip():
        st.warning("Tell the tool what you want to say first.")
        st.stop()

    # Guard against section dividers selected as format
    if content_format.startswith("──"):
        st.warning("Please select a specific format, not a section header.")
        st.stop()

    user_message = f"""Write copy for the following brief:

School: {school}
Messaging pillar: {pillar}
Content format: {content_format}
Platform: {platform}
Output language: {language}
Funnel stage: {funnel_stage}
Audience: {audience.strip() if audience.strip() else "Not specified — use your judgement based on the school, format, and angle."}
What to say / angle: {angle.strip()}"""

    st.divider()

    # Output containers
    output_header = st.markdown(
        '<div class="output-wrap"><div class="output-header">Generated copy</div></div>',
        unsafe_allow_html=True,
    )
    copy_placeholder = st.empty()
    thinking_placeholder = st.empty()

    # Streaming call
    client = anthropic.Anthropic()
    full_text = ""

    is_arabic = language == "Arabic"
    dir_attr = 'dir="rtl"' if is_arabic else ""

    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for delta in stream.text_stream:
            full_text += delta

            # Split live as text arrives
            if "PART 2: THINKING" in full_text:
                copy_part = full_text.split("PART 2: THINKING")[0]
                copy_clean = copy_part.replace("PART 1: COPY", "").strip()
            else:
                copy_clean = full_text.replace("PART 1: COPY", "").strip()

            copy_placeholder.markdown(
                f'<div class="output-wrap">'
                f'<div class="output-header">Generated copy</div>'
                f'<div class="output-copy" {dir_attr}>{copy_clean}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Final split
    if "PART 2: THINKING" in full_text:
        parts = full_text.split("PART 2: THINKING")
        copy_final = parts[0].replace("PART 1: COPY", "").strip()
        thinking_raw = parts[1].strip()
    else:
        copy_final = full_text.replace("PART 1: COPY", "").strip()
        thinking_raw = ""

    # Render final copy cleanly
    copy_placeholder.markdown(
        f'<div class="output-wrap">'
        f'<div class="output-header">Generated copy</div>'
        f'<div class="output-copy" {dir_attr}>{copy_final}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Copy-to-clipboard via code block
    st.code(copy_final, language=None)
    st.caption("Use the copy icon above to copy the text.")

    # Thinking expander
    if thinking_raw:
        with st.expander("How the copy was built", expanded=False):
            lines = [ln.strip() for ln in thinking_raw.splitlines() if ln.strip()]
            for line in lines:
                if ":" in line:
                    label, _, rest = line.partition(":")
                    st.markdown(
                        f'<div class="thinking-row">'
                        f'<span class="thinking-label">{label.strip()}:</span> {rest.strip()}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(f'<div class="thinking-row">{line}</div>', unsafe_allow_html=True)

    st.divider()

    # Feedback row
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("✓  This works", key="fb_good"):
            st.success("Good to hear.")
    with c2:
        if st.button("✗  Not quite", key="fb_bad"):
            st.text_area(
                "What was off?",
                placeholder="Tell us what to adjust — tone, angle, length, specifics...",
                key="feedback_text",
            )
