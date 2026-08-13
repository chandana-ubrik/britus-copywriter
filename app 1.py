import streamlit as st
import anthropic
import base64

st.set_page_config(
    page_title="Meta Ad Copy Evaluator",
    page_icon="📊",
    layout="centered"
)

# ── UBRIK LOGO ──
def load_logo(path):
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return data

try:
    logo_data = load_logo("ubrik_logo.png")
    st.sidebar.markdown(
        f'<img src="data:image/png;base64,{logo_data}" width="120">',
        unsafe_allow_html=True
    )
except:
    st.sidebar.markdown("**ubrik**")

st.sidebar.markdown("---")
st.sidebar.markdown("### Meta Ad Copy Evaluator")
st.sidebar.markdown("Paste your ad copy and get a score with tips to improve.")
st.sidebar.markdown("---")
st.sidebar.markdown("**Evaluated against**")
st.sidebar.markdown("- Hook strength")
st.sidebar.markdown("- Clarity of offer")
st.sidebar.markdown("- Benefit-first framing")
st.sidebar.markdown("- Call to action")
st.sidebar.markdown("- Length and readability")
st.sidebar.markdown("- Emotional appeal")
st.sidebar.markdown("- Specificity")
st.sidebar.markdown("- Audience relevance")

# ── SYSTEM PROMPT ──
SYSTEM_PROMPT = """
You are an expert Meta (Facebook and Instagram) ad copy evaluator.

Your job is to evaluate ad copy against the eight best practices for
Meta ads in 2026 and return a structured score with specific
improvement tips.

THE EIGHT BEST PRACTICES YOU EVALUATE AGAINST:

1. HOOK STRENGTH
The first line must stop the scroll within 1.5 seconds on mobile.
It should speak directly to a pain point, desire or curiosity.
It should not start with the brand name or a generic greeting.

2. BENEFIT-FIRST FRAMING
Copy should lead with what the product or service does FOR the
person, not what it IS. Features describe the product. Benefits
describe the outcome for the reader.

3. CLARITY OF OFFER
The reader should immediately understand what is being offered,
who it is for, and what they need to do next. Vague offers lose
clicks even with strong hooks.

4. SPECIFICITY
Specific numbers, named outcomes and concrete details outperform
vague claims. "98% of parents recommend us" is stronger than
"parents love us." "3 schools in Riyadh" is stronger than
"multiple locations."

5. CALL TO ACTION
The CTA must match the intent. "Learn More" fits awareness.
"Book Now" fits high intent. "Apply Now" fits a decision-ready
audience. A weak or mismatched CTA wastes a strong hook.

6. LENGTH AND READABILITY
Primary text should ideally be under 125 characters for mobile
feeds. Longer copy is acceptable for complex offers but must use
short sentences and line breaks. Copy that looks like a wall of
text gets skipped.

7. EMOTIONAL APPEAL
The best performing Meta ads connect emotionally before they
inform rationally. Fear of missing out, pride, belonging, relief,
aspiration — name the emotion the copy is targeting and whether
it lands.

8. AUDIENCE RELEVANCE
The copy should feel written for one specific person, not a
general audience. "You" should appear more than "we" or "our."
The reader should feel the ad is speaking directly to their
situation.

HOW TO SCORE:

Score each best practice out of 10.
Calculate an overall score out of 100.
Use this rating scale for the overall score:
90-100: Excellent — ready to run
70-89: Good — minor improvements needed
50-69: Average — needs work before running
Below 50: Needs significant rewrite

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:

OVERALL SCORE: [X/100] — [Rating label]

---

1. Hook Strength: [X/10]
[One sentence on what works or does not work. One specific tip.]

2. Benefit-First Framing: [X/10]
[One sentence on what works or does not work. One specific tip.]

3. Clarity of Offer: [X/10]
[One sentence on what works or does not work. One specific tip.]

4. Specificity: [X/10]
[One sentence on what works or does not work. One specific tip.]

5. Call to Action: [X/10]
[One sentence on what works or does not work. One specific tip.]

6. Length and Readability: [X/10]
[One sentence on what works or does not work. One specific tip.]

7. Emotional Appeal: [X/10]
[One sentence on what works or does not work. One specific tip.]

8. Audience Relevance: [X/10]
[One sentence on what works or does not work. One specific tip.]

---

TOP 3 IMPROVEMENTS:
1. [Most important change to make]
2. [Second most important change]
3. [Third most important change]

---

REWRITTEN VERSION:
[Rewrite the ad copy applying all the improvements above.]

Keep your feedback direct and specific. Never use vague phrases
like "consider improving" — say exactly what to change and how.
"""

# ── MAIN UI ──
st.title("Meta Ad Copy Evaluator")
st.caption(
    "Paste your Meta ad copy below and get a score, "
    "detailed feedback and a rewritten version."
)

st.divider()

ad_copy = st.text_area(
    "Your ad copy",
    height=200,
    placeholder="Paste your Facebook or Instagram ad copy here..."
)

objective = st.selectbox(
    "Campaign objective (optional)",
    ["Not sure",
     "Awareness",
     "Traffic",
     "Engagement",
     "Leads",
     "App promotion",
     "Sales"]
)

audience = st.text_input(
    "Target audience (optional)",
    placeholder="e.g. Parents of school-age children in Riyadh"
)

if st.button("Evaluate ad copy", type="primary"):
    if not ad_copy.strip():
        st.warning("Please paste your ad copy first.")
    else:
        context = ""
        if objective != "Not sure":
            context += f"Campaign objective: {objective}\n"
        if audience.strip():
            context += f"Target audience: {audience}\n"
        if context:
            context = f"Context:\n{context}\n"

        user_message = (
            f"{context}Evaluate this Meta ad copy:\n\n{ad_copy}"
        )

        with st.spinner("Evaluating..."):
            client = anthropic.Anthropic()
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            output = message.content[0].text

        st.divider()
        st.subheader("Evaluation")
        st.write(output)

        st.divider()
        st.caption("Was this helpful?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, helpful"):
                st.success("Glad it helped.")
        with col2:
            if st.button("Not quite"):
                st.text_area(
                    "What was off?",
                    placeholder="Tell us what could be better...",
                    key="feedback"
                )
