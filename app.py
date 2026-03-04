import os
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
def build_prompt(code: str, language: str, level: str) -> str:
    modifier = LEVEL_MODIFIERS[level]
    headings_list = "\n".join(REQUIRED_HEADINGS)
    return f"""A user has submitted the following {language} code:

```{language.lower()}
{code}
```

Explanation level: **{level}**
{modifier}

Respond ONLY with these exact 6 Markdown headings in order, each immediately followed \
by your explanation content. Do not add any preamble, extra headings, or closing remarks.

{headings_list}"""

# ── Groq call with retry / fallback ──────────────────────────────────────────
def get_missing_headings(text: str) -> list:
    return [h for h in REQUIRED_HEADINGS if h not in text]

def call_groq(code: str, language: str, level: str) -> str:
    if not GROQ_API_KEY:
        return (
            "### Human Translation\n\n"
            "⚠️ **No API key found.** Add `GROQ_API_KEY` to your `.env` file or Streamlit secrets "
            "and restart the app."
        )

    system_msg = (
        "You are an expert programming teacher who explains code clearly and pedagogically. "
        "Always respond using exactly the Markdown headings requested — no more, no less. "
        "Never skip a heading."
    )

    try:
        client = Groq(api_key=GROQ_API_KEY)
        prompt = build_prompt(code, language, level)

        def _call(messages):
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.3,
            )
            return response.choices[0].message.content

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ]

        # First attempt
        text = _call(messages)

        # Check for missing headings — one automatic retry
        missing = get_missing_headings(text)
        if missing:
            missing_str = ", ".join(missing)
            messages.append({"role": "assistant", "content": text})
            messages.append({
                "role": "user",
                "content": (
                    f"You missed these required headings: {missing_str}. "
                    "Return the COMPLETE output again with ALL 6 headings present and in order."
                ),
            })
            text = _call(messages)
            missing = get_missing_headings(text)

        # Final fallback — wrap raw output so UI never breaks
        if missing:
            text = "### Human Translation\n\n" + text

        return text

    except Exception as e:
        return (
            "### Human Translation\n\n"
            f"⚠️ **Something went wrong while contacting the AI:** `{e}`\n\n"
            "Please check your API key and try again."
        )

# ── Section extractor (for misconceptions toggle) ─────────────────────────────
def extract_section(text: str, heading: str) -> str:
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
for key, default in [("code_input", ""), ("selected_lang", "Python"), ("last_output", "")]:
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🌐 CodeLingo")
    st.markdown("*Translate code into human reasoning.*")
    st.divider()

    st.markdown("**Try an example:**")
    for label, example in EXAMPLES.items():
        if st.button(label, use_container_width=True):
            st.session_state["code_input"] = example["code"]
            st.session_state["selected_lang"] = example["lang"]
            st.session_state["last_output"] = ""
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
st.markdown("# 🌐 CodeLingo")
st.markdown("##### Translate code into human reasoning.")
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
    )

# ── Run translation ───────────────────────────────────────────────────────────
if translate_btn:
    if not code_input.strip():
        st.warning("Paste some code first, then click Translate.")
    else:
        with st.spinner("Translating your code..."):
            output = call_groq(code_input.strip(), selected_lang, level)
        st.session_state["last_output"] = output
        st.session_state["code_input"] = code_input

# ── Output ────────────────────────────────────────────────────────────────────
if st.session_state["last_output"]:
    st.divider()

    action_col, spacer = st.columns([1, 4])
    with action_col:
        misconceptions_only = st.toggle("Misconceptions only", value=False)
        st.download_button(
            label="⬇ Save as .md",
            data=st.session_state["last_output"],
            file_name="codelingo_explanation.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.markdown("")

    if misconceptions_only:
        section = extract_section(
            st.session_state["last_output"], "### Common Beginner Mistakes"
        )
        if section:
            st.markdown(section)
        else:
            st.info("No misconceptions section found in the last output.")
    else:
        st.markdown(st.session_state["last_output"])
