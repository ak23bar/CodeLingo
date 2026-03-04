# 🌐 CodeLingo

**Translate code into human reasoning.**

CodeLingo is an AI-powered tool that turns code snippets into structured, plain-English explanations — built for students who can *write* code but struggle to *read* it.

---

## Why CodeLingo?

Learning to program is like learning a new language. Most beginner tools focus on teaching students to write code, but very few help them understand code they encounter. This gap prevents students from debugging, learning from examples, or building a mental model of how programs actually execute.

CodeLingo bridges that gap. Paste any snippet, choose your level, and get a structured breakdown — from a plain-English translation to common beginner mistakes — instantly.

Built with CodeHS students and teachers in mind, where Python, JavaScript, and Java are the primary languages.

---

## Features

- **3 explanation levels** — Beginner, Student, Teacher (each adjusts depth and vocabulary)
- **3 supported languages** — Python, JavaScript, Java
- **Structured output** — always returns 6 consistent Markdown sections:
  - Human Translation
  - Line-by-Line Explanation
  - Step-by-Step Execution
  - Why This Code Exists
  - Common Beginner Mistakes
  - Key Concepts
- **Misconceptions only toggle** — isolate the "Common Beginner Mistakes" section for quick classroom use
- **Save as .md** — download any explanation as a Markdown file
- **Example snippets** — 3 one-click examples (one per language) to demo the tool instantly
- **Retry + fallback logic** — if the AI drifts from the required format, the app retries automatically and never shows broken output

---

## Tech Stack

| Layer | Choice |
|---|---|
| UI | Streamlit |
| AI | Google Gemini 2.0 Flash |
| Language | Python 3.10+ |
| Deployment | Streamlit Community Cloud (free) |

---

## Local Setup

### 1. Clone the repo

```bash
git clone git@github.com:ak23bar/CodeLingo.git
cd CodeLingo
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your API key

Get a free Gemini API key from [aistudio.google.com](https://aistudio.google.com).

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_key_here
```

### 4. Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## Deploying to Streamlit Community Cloud

1. Push this repo to GitHub (ensure `.env` is gitignored — it is).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app** → select `ak23bar/CodeLingo` → set main file to `app.py`.
4. Under **Advanced settings → Secrets**, add:

```toml
GEMINI_API_KEY = "your_key_here"
```

5. Click **Deploy**. You'll get a permanent public URL within ~60 seconds.

---

## Project Structure

```
CodeLingo/
├── app.py              # Streamlit UI + Gemini integration
├── requirements.txt    # Dependencies
├── README.md           # This file
├── .env                # Local API key (gitignored)
├── .gitignore
└── .streamlit/
    └── secrets.toml    # Streamlit Cloud API key (gitignored)
```
