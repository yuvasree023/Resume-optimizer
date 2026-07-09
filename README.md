# Resume Optimizer ✦

> An AI-powered resume analysis and optimization web app built with Streamlit and Groq.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)]
(https://resume-optimizer-epk34p7se6qog5biaraumf.streamlit.app/)

Resume Optimizer takes a PDF resume and a target job description, then uses advanced LLMs to score the resume across five key dimensions, rewrite bullet points using the STAR method, and export an optimized version back into a clean layout—all in under 30 seconds.

---

## 🚀 Live Demo

Check out the live application here: **[Resume Optimizer Live App](YOUR_DEPLOYED_STREAMLIT_URL_HERE)**

---

## ✨ Features

- **Instant Resume Scoring:** Evaluates your resume across five crucial categories—Impact, Skills, Formatting, ATS Compatibility, and Experience—providing an individual score out of 100.
- **AI-Powered STAR Rewriting:** Transforms weak bullet points into high-impact statements using the **STAR** (Situation, Task, Action, Result) method, complete with strong action verbs and quantified metrics.
- **Job-Specific Keyword Optimization:** Analyzes the provided job description and intelligently mirrors vital keywords to maximize your ATS (Applicant Tracking System) match rate.
- **Actionable Insights:** Provides 5 prioritized recommendations (High / Medium / Low impact) so you know exactly what parts of your resume need the most attention.
- **Tailored Professional Summary:** Generates a concise, punchy 2-line professional summary specifically aligned with the target role.
- **Clean Pastel UI:** Built with a beautiful, soft violet theme featuring animated score rings, progress bars, and an intuitive multi-page user flow.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit |
| **AI / LLM Engine** | Groq API (`llama-3.3-70b-versatile`) |
| **PDF Parsing & Editing** | PyMuPDF (`fitz`) |
| **Environment Management** | python-dotenv |
| **Language** | Python 3.10+ |

---

## 📁 Project Structure

```text
resume-optimizer/
├── app.py              # Main Streamlit application (pages, UI, and logic)
├── .env                # Local environment variables (API keys - Git ignored)
├── .gitignore          # Prevents tracking of virtual environments, .env, and caches
├── requirements.txt    # Project dependencies
└── README.md           # Project documentation
