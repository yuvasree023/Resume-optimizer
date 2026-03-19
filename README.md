# Resume Optimizer ✦

> An AI-powered resume analysis and optimization web app built with Streamlit and Groq.

---

## What It Does

Resume Optimizer takes your PDF resume and a job description, then uses AI to score your resume across five key dimensions, rewrite every bullet point using the STAR method, and export the improved version back as a PDF — all in under 30 seconds.

No account needed to try it. No fluff. Just paste, upload, and get results.

---

## Features

- **Instant resume scoring** across five categories — Impact, Skills, Formatting, ATS compatibility, and Experience — each with a score out of 100
- **AI-powered rewriting** using the STAR method (Situation, Task, Action, Result) on every bullet point, with strong action verbs and quantified metrics
- **Job-specific optimization** — mirrors keywords directly from the job description for maximum ATS match
- **In-place PDF editing** — the optimized content is written back onto your original PDF, preserving your layout, fonts, and formatting
- **Actionable recommendations** — five prioritized fixes (High / Medium / Low) so you know exactly what to improve next
- **Professional Summary generation** — a tailored 2-line summary added to the top of your resume matching the role
- **Clean pastel UI** — soft violet theme, score ring, animated bars, and a smooth multi-page flow

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| AI / LLM | Groq API — `llama-3.3-70b-versatile` |
| PDF parsing | PyMuPDF (`fitz`) |
| PDF editing | PyMuPDF in-place redact + rewrite |
| Environment | python-dotenv |
| Language | Python 3.10+ |

---

## Project Structure

```
resume-optimizer/
├── app.py              # Main application — all pages and logic
├── .env                # Your Groq API key (never commit this)
├── .gitignore          # Excludes .env and pycache
├── requirements.txt    # All dependencies
└── README.md           # This file
```

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/resume-optimizer.git
cd resume-optimizer
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your Groq API key

Create a `.env` file in the root folder:

```
GROQ_API_KEY=your_actual_key_here
```

Get a free key at [console.groq.com](https://console.groq.com)

### 4. Run the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

---

## Requirements

```
streamlit
groq
pymupdf
python-dotenv
```

---

## How It Works

1. You land on the home page and sign in (demo auth — no real database required)
2. Upload your resume as a PDF and paste the job description
3. The app extracts text from your PDF using PyMuPDF
4. Two AI calls run in sequence:
   - First call scores your resume across 5 categories and returns JSON
   - Second call rewrites the resume with STAR method bullets and generates 5 recommendations
5. The optimized text is written back into your original PDF using PyMuPDF's redact-and-rewrite approach
6. You see your score ring, bars, and recommendations — and download the improved PDF

---

## Scoring Categories

| Category | What It Measures |
|---|---|
| Impact | Strength and specificity of achievements |
| Skills | Relevance and depth of listed skills |
| Formatting | Consistency, readability, and structure |
| ATS | Keyword match with the job description |
| Experience | Clarity and relevance of work history |

The overall score is the average of all five, displayed as a circular progress ring.

---

## Deployment

### Streamlit Community Cloud (recommended — free)

1. Push your code to a public GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account and select `app.py`
4. In the **Secrets** tab, add:
   ```
   GROQ_API_KEY = "your_actual_key_here"
   ```
5. Click **Deploy** — your app gets a public URL instantly

---

## Important Notes

- **Never commit your `.env` file.** It contains your API key. The `.gitignore` handles this automatically.
- The login system is demo-only — no real database. All session data lives in Streamlit's session state.
- Groq's free tier has rate limits. If you hit errors on analysis, wait a moment and retry.
- PDF in-place editing works best on text-based PDFs. Scanned image PDFs will not have editable text layers.

---

## License

MIT — free to use, modify, and deploy.

---

## Author

Built with Streamlit, Groq, and PyMuPDF.  
Designed to help job seekers put their best resume forward. ✦
