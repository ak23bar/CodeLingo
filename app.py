import os
import json
import time
import urllib.parse
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CodeLingo",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── API key ───────────────────────────────────────────────────────────────────
def get_api_key() -> str:
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        load_dotenv()
        return os.getenv("GROQ_API_KEY", "")

GROQ_API_KEY = get_api_key()

# ── Section colors ────────────────────────────────────────────────────────────
SECTION_META = [
    ("### Human Translation",       "#3B82F6", "Human Translation"),
    ("### Line-by-Line Explanation", "#7C3AED", "Line-by-Line Explanation"),
    ("### Step-by-Step Execution",   "#0D9488", "Step-by-Step Execution"),
    ("### Why This Code Exists",     "#6366F1", "Why This Code Exists"),
    ("### Common Beginner Mistakes", "#F59E0B", "Common Beginner Mistakes"),
    ("### Key Concepts",             "#10B981", "Key Concepts"),
]
SECTION_COLORS = {h: c for h, c, _ in SECTION_META}

# ── Custom CSS ────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
<style>
/* ── HIDE streamlit chrome, keep sidebar toggle ── */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
/* Hide deploy button and streamlit branding in header, but NOT the sidebar toggle */
header [data-testid="stToolbar"] { visibility: hidden; }
header [data-testid="stDecoration"] { display: none; }
/* Ensure the collapsed sidebar arrow is always visible */
[data-testid="collapsedControl"] {
    visibility: visible !important;
    display: flex !important;
    opacity: 1 !important;
}
section[data-testid="stSidebarCollapsedControl"] {
    visibility: visible !important;
    display: flex !important;
}

/* ── Hero ── */
.hero-title {
    font-size: 2.6rem;
    font-weight: 900;
    background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.2;
}
.hero-sub {
    color: #94A3B8;
    font-size: 1.1rem;
    margin: 0.3rem 0 0 0;
}
.hero-bar {
    margin-bottom: 1.5rem;
}

/* ── Section cards ── */
.section-card {
    border-radius: 10px;
    padding: 1.1rem 1.4rem 0.8rem 1.4rem;
    margin-bottom: 1rem;
    border-left: 4px solid;
    background: #1A1D27;
}
.section-badge {
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 0 0 0.55rem 0;
    opacity: 0.8;
}
.section-content {
    color: #E2E8F0;
    line-height: 1.7;
    margin: 0;
}

/* ── Quiz cards ── */
.quiz-card {
    background: #1A1D27;
    border-radius: 10px;
    padding: 1rem 1.4rem;
    margin-bottom: 0.75rem;
    border-left: 4px solid #7C3AED;
}
.quiz-q {
    font-weight: 600;
    color: #F1F5F9;
    margin-bottom: 0.5rem;
}

/* ── Action bar ── */
.action-bar {
    display: flex;
    gap: 0.6rem;
    align-items: center;
    margin-bottom: 1rem;
}

/* ── Sidebar brand ── */
.sidebar-brand {
    font-size: 1.45rem;
    font-weight: 900;
    background: linear-gradient(135deg, #7C3AED, #3B82F6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
}
.sidebar-sub {
    color: #64748B;
    font-size: 0.85rem;
    margin: 0.1rem 0 0 0;
}

/* ── Code input ── */
textarea[data-testid] {
    font-family: 'JetBrains Mono', 'Fira Code', monospace !important;
    font-size: 0.87rem !important;
}
</style>
"""

# ── Examples ──────────────────────────────────────────────────────────────────
EXAMPLES = {
    "Python — for loop": {
        "lang": "Python",
        "code": (
            'fruits = ["apple", "banana", "cherry"]\n'
            "for fruit in fruits:\n"
            '    print(f"I love {fruit}!")\n'
        ),
    },
    "JavaScript — async fetch": {
        "lang": "JavaScript",
        "code": (
            "async function getUser(id) {\n"
            "  const response = await fetch(`https://api.example.com/users/${id}`);\n"
            "  const data = await response.json();\n"
            "  return data;\n"
            "}\n"
        ),
    },
    "Java — class & method": {
        "lang": "Java",
        "code": (
            "public class Calculator {\n"
            "    public int add(int a, int b) {\n"
            "        return a + b;\n"
            "    }\n\n"
            "    public static void main(String[] args) {\n"
            "        Calculator calc = new Calculator();\n"
            "        System.out.println(calc.add(3, 5));\n"
            "    }\n"
            "}\n"
        ),
    },
}

REQUIRED_HEADINGS = [
    "### Human Translation",
    "### Line-by-Line Explanation",
    "### Step-by-Step Execution",
    "### Why This Code Exists",
    "### Common Beginner Mistakes",
    "### Key Concepts",
]

LEVEL_MODIFIERS = {
    "Beginner": (
        "Use zero jargon. Imagine you are explaining this to a curious 12-year-old "
        "who has never programmed before. Use simple analogies and everyday comparisons."
    ),
    "Student": (
        "Assume the reader has basic programming knowledge. Use correct terminology "
        "but explain it when introduced. Relate concepts to things a typical CS student would know."
    ),
    "Teacher": (
        "Assume the reader is a programming teacher. Include pedagogical notes, "
        "common student misconceptions to watch for, curriculum connections, "
        "and teaching suggestions alongside the explanation."
    ),
}

# ── Prompt builder ────────────────────────────────────────────────────────────
STEP_BY_STEP_INSTRUCTIONS = {
    "Beginner": (
        "For '### Step-by-Step Execution': Walk through EVERY line or logical step one at a time, "
        "numbered (Step 1, Step 2, ...). For each step quote the line of code in a code block, "
        "then explain in plain English what happens — no jargon, use real-world analogies. "
        "Imagine the reader has never run code before."
    ),
    "Student": (
        "For '### Step-by-Step Execution': Walk through EVERY line or logical step one at a time, "
        "numbered (Step 1, Step 2, ...). For each step quote the line in a code block, "
        "then explain what executes, what values change, and why. Use correct terminology "
        "and note any important edge cases a student should be aware of."
    ),
    "Teacher": (
        "For '### Step-by-Step Execution': Walk through EVERY line or logical step one at a time, "
        "numbered (Step 1, Step 2, ...). For each step quote the line in a code block, "
        "explain execution in detail including memory/state changes, then add a brief "
        "'Teaching note:' on common student confusion points or how to frame this step in class."
    ),
}

def build_prompt(code: str, language: str, level: str) -> str:
    modifier = LEVEL_MODIFIERS[level]
    step_instruction = STEP_BY_STEP_INSTRUCTIONS[level]
    headings_list = "\n".join(REQUIRED_HEADINGS)
    return f"""A user has submitted the following {language} code:

```{language.lower()}
{code}
```

Explanation level: **{level}**
{modifier}

{step_instruction}

For all other sections, match the same explanation level depth and vocabulary.

Respond ONLY with these exact 6 Markdown headings in order, each immediately followed \
by your explanation content. Do not add any preamble, extra headings, or closing remarks.

{headings_list}"""

SYSTEM_PROMPT = (
    "You are an expert programming teacher who explains code clearly and pedagogically. "
    "Always respond using exactly the Markdown headings requested — no more, no less. "
    "Never skip a heading. Never add a preamble or closing remark."
)

# ── Streaming Groq call ───────────────────────────────────────────────────────
def get_missing_headings(text: str) -> list:
    return [h for h in REQUIRED_HEADINGS if h not in text]

def stream_groq(code: str, language: str, level: str):
    """Generator: yields text chunks from Groq streaming API."""
    client = Groq(api_key=GROQ_API_KEY)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": build_prompt(code, language, level)},
    ]
    with client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.3,
        max_tokens=2048,
        stream=True,
    ) as stream:
        for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            if token:
                yield token
                time.sleep(0.03)

# ── Quiz generator ────────────────────────────────────────────────────────────
QUIZ_PROMPT = """Based on the following {language} code and its {level}-level explanation, \
generate exactly 3 multiple-choice comprehension questions to test understanding.

Code:
```{language_lower}
{code}
```

Return ONLY valid JSON — no other text, no markdown fences:
{{"questions": [
  {{"q": "Question text?", "options": ["A", "B", "C", "D"], "answer": 0}},
  {{"q": "Question text?", "options": ["A", "B", "C", "D"], "answer": 2}},
  {{"q": "Question text?", "options": ["A", "B", "C", "D"], "answer": 1}}
]}}
The "answer" field is the 0-based index of the correct option.
Make questions appropriate for {level} level."""

def generate_quiz(code: str, language: str, level: str) -> list | None:
    """Returns list of question dicts or None on failure."""
    try:
        client = Groq(api_key=GROQ_API_KEY)
        prompt = QUIZ_PROMPT.format(
            language=language,
            language_lower=language.lower(),
            level=level,
            code=code,
        )
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a quiz generator. Return only valid JSON."},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.4,
            max_tokens=1024,
        )
        raw = response.choices[0].message.content.strip()
        # Strip accidental markdown fences
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        data = json.loads(raw)
        return data.get("questions", [])
    except Exception:
        return None

# ── Section parser & styled renderer ─────────────────────────────────────────
def parse_sections(text: str) -> list[tuple]:
    """Returns list of (heading, color, badge_label, content) for each found section."""
    results = []
    for heading, color, badge in SECTION_META:
        if heading not in text:
            continue
        start = text.index(heading) + len(heading)
        # Find where next heading starts
        end = len(text)
        for other_heading, _, _ in SECTION_META:
            if other_heading == heading:
                continue
            if other_heading in text:
                pos = text.index(other_heading)
                if pos > text.index(heading) and pos < end:
                    end = pos
        content = text[start:end].strip()
        results.append((heading, color, badge, content))
    return results

def render_sections(text: str):
    """Render each section as a styled card."""
    sections = parse_sections(text)
    if not sections:
        st.markdown(text)
        return
    for _, color, badge, content in sections:
        st.markdown(
            f'<div class="section-card" style="border-color:{color}">'
            f'<p class="section-badge" style="color:{color}">{badge}</p>',
            unsafe_allow_html=True,
        )
        st.markdown(content)
        st.markdown("</div>", unsafe_allow_html=True)

def extract_section(text: str, heading: str) -> str:
    """Extract a single section's content string."""
    if heading not in text:
        return ""
    start = text.index(heading)
    after = text[start:]
    lines = after.split("\n")
    section_lines = [lines[0]]
    for line in lines[1:]:
        if line.startswith("### ") and line.strip() != heading.strip():
            break
        section_lines.append(line)
    return "\n".join(section_lines)

# ── Session state init ────────────────────────────────────────────────────────
DEFAULTS = {
    "code_input": "", "selected_lang": "Python", "last_output": "",
    "quiz": None, "quiz_answers": {}, "quiz_checked": False, "share_triggered": False,
}
for key, default in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Inject CSS ────────────────────────────────────────────────────────────────
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── URL param: pre-load shared snippet ───────────────────────────────────────
params = st.query_params
if "code" in params and not st.session_state["last_output"]:
    raw_code = urllib.parse.unquote(params["code"])
    raw_lang = urllib.parse.unquote(params.get("lang", "Python"))
    if raw_code and raw_code != st.session_state["code_input"]:
        st.session_state["code_input"] = raw_code
        if raw_lang in ["Python", "JavaScript", "Java"]:
            st.session_state["selected_lang"] = raw_lang

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="sidebar-brand">🌐 CodeLingo</p>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-sub">Translate code into human reasoning.</p>', unsafe_allow_html=True)
    st.divider()

    st.markdown("**Try an example:**")
    for label, example in EXAMPLES.items():
        if st.button(label, use_container_width=True):
            st.session_state["code_input"] = example["code"]
            st.session_state["selected_lang"] = example["lang"]
            st.session_state["last_output"] = ""
            st.session_state["quiz"] = None
            st.session_state["quiz_answers"] = {}
            st.session_state["quiz_checked"] = False
            st.rerun()

    st.divider()
    with st.expander("About CodeLingo"):
        st.markdown(
            """
**CodeLingo** was built for students who can write code but struggle to *read* it.

Learning to program is like learning a new language — you need translation before fluency.

CodeLingo bridges that gap by turning code snippets into structured, human-readable
explanations tailored to your experience level.

Built with CodeHS students and teachers in mind.
"""
        )

# ── Main UI ───────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="hero-bar">'
    '<p class="hero-title">🌐 CodeLingo</p>'
    '<p class="hero-sub">Translate code into human reasoning.</p>'
    '</div>',
    unsafe_allow_html=True,
)
st.divider()

col_code, col_controls = st.columns([3, 1], gap="large")

with col_code:
    st.markdown("**Paste your code:**")
    code_input = st.text_area(
        label="code_area",
        label_visibility="collapsed",
        value=st.session_state["code_input"],
        height=280,
        placeholder="# Paste any Python, JavaScript, or Java snippet here...",
    )

with col_controls:
    st.markdown("**Language**")
    lang_options = ["Python", "JavaScript", "Java"]
    try:
        lang_index = lang_options.index(st.session_state.get("selected_lang", "Python"))
    except ValueError:
        lang_index = 0
    selected_lang = st.selectbox(
        label="language",
        label_visibility="collapsed",
        options=lang_options,
        index=lang_index,
    )

    st.markdown("**Explanation Level**")
    level = st.radio(
        label="level",
        label_visibility="collapsed",
        options=["Beginner", "Student", "Teacher"],
        index=0,
    )

    st.markdown("")
    translate_btn = st.button(
        "🔍 Translate Code",
        use_container_width=True,
        type="primary",
        disabled=not GROQ_API_KEY,
    )
    if not GROQ_API_KEY:
        st.caption("⚠️ GROQ_API_KEY not set")

# ── Run translation (streaming) ───────────────────────────────────────────────
if translate_btn:
    if not code_input.strip():
        st.warning("Paste some code first, then click Translate.")
    else:
        st.session_state["code_input"] = code_input
        st.session_state["last_output"] = ""
        st.session_state["quiz"] = None
        st.session_state["quiz_answers"] = {}
        st.session_state["quiz_checked"] = False
        st.session_state["share_triggered"] = False
        st.divider()
        streamed = st.write_stream(stream_groq(code_input.strip(), selected_lang, level))
        full_output = streamed if isinstance(streamed, str) else "".join(streamed)
        # Post-stream structural check
        missing = get_missing_headings(full_output)
        if missing:
            st.warning(
                f"The AI skipped sections: {', '.join(missing)}. "
                "Click Translate again to retry."
            )
        st.session_state["last_output"] = full_output
        st.rerun()

# ── Output ────────────────────────────────────────────────────────────────────
if st.session_state["last_output"]:
    st.divider()

    # ── Action bar ──
    a1, a2, a3, spacer = st.columns([1.2, 1.2, 1.4, 4])
    with a1:
        misconceptions_only = st.toggle("Misconceptions only", value=False)
    with a2:
        st.download_button(
            label="⬇ Save as .md",
            data=st.session_state["last_output"],
            file_name="codelingo_explanation.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with a3:
        if st.button("🔗 Share snippet", use_container_width=True):
            st.session_state["share_triggered"] = True
            encoded_code = urllib.parse.quote(st.session_state["code_input"])
            encoded_lang = urllib.parse.quote(st.session_state.get("selected_lang", "Python"))
            st.query_params.update({"code": encoded_code, "lang": encoded_lang})

    if st.session_state.get("share_triggered"):
        st.info(
            "✅ **Shareable link ready!** Copy the URL from your browser's address bar — "
            "anyone visiting it will have this snippet pre-loaded.",
            icon="🔗",
        )

    st.markdown("")

    # ── Main explanation output ──
    if misconceptions_only:
        section = extract_section(
            st.session_state["last_output"], "### Common Beginner Mistakes"
        )
        if section:
            content = section.replace("### Common Beginner Mistakes", "").strip()
            st.markdown(
                '<div class="section-card" style="border-color:#F59E0B">'
                '<p class="section-badge" style="color:#F59E0B">Common Beginner Mistakes</p>',
                unsafe_allow_html=True,
            )
            st.markdown(content)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No misconceptions section found in the last output.")
    else:
        render_sections(st.session_state["last_output"])

    # ── Quiz Me ───────────────────────────────────────────────────────────────
    st.divider()
    quiz_col, _ = st.columns([1, 3])
    with quiz_col:
        if st.button("🧠 Quiz Me", use_container_width=True, type="secondary"):
            with st.spinner("Generating quiz questions..."):
                questions = generate_quiz(
                    st.session_state["code_input"],
                    st.session_state.get("selected_lang", selected_lang),
                    level,
                )
            if questions:
                st.session_state["quiz"] = questions
                st.session_state["quiz_answers"] = {}
                st.session_state["quiz_checked"] = False
            else:
                st.warning("Couldn't generate quiz questions. Try again.")

    if st.session_state["quiz"]:
        st.markdown("### 🧠 Test Your Understanding")
        questions = st.session_state["quiz"]
        for i, q in enumerate(questions):
            st.markdown(
                f'<div class="quiz-card">'
                f'<p class="quiz-q">Q{i+1}. {q["q"]}</p></div>',
                unsafe_allow_html=True,
            )
            chosen = st.radio(
                label=f"q{i}",
                label_visibility="collapsed",
                options=q["options"],
                key=f"quiz_radio_{i}",
                index=None,
            )
            if chosen is not None:
                st.session_state["quiz_answers"][i] = q["options"].index(chosen)

        check_col, _ = st.columns([1, 4])
        with check_col:
            if st.button("✅ Check Answers", use_container_width=True, type="primary"):
                st.session_state["quiz_checked"] = True

        if st.session_state["quiz_checked"]:
            score = 0
            for i, q in enumerate(questions):
                user_ans = st.session_state["quiz_answers"].get(i)
                correct = q["answer"]
                if user_ans is None:
                    st.warning(f"Q{i+1}: Not answered")
                elif user_ans == correct:
                    score += 1
                    st.success(f"Q{i+1}: ✓ Correct — {q['options'][correct]}")
                else:
                    st.error(
                        f"Q{i+1}: ✗ You chose *{q['options'][user_ans]}* — "
                        f"correct answer: **{q['options'][correct]}**"
                    )
            answered = len(st.session_state["quiz_answers"])
            st.markdown(f"**Score: {score}/{answered if answered else len(questions)}**")
