import streamlit as st
import fitz
from groq import Groq
from dotenv import load_dotenv
import os, json, re, io

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ══════════════════════════════════════════════════════
# PDF IN-PLACE EDITOR — rewrites text on original PDF
# ══════════════════════════════════════════════════════
def edit_original_pdf(original_pdf_bytes: bytes, optimized_text: str) -> bytes:
    """
    Takes the user's original PDF and rewrites it with optimized content.
    Preserves page layout. Replaces each text block with the matching
    optimized line, keeping font size and position.
    """
    doc = fitz.open(stream=original_pdf_bytes, filetype="pdf")

    # Build a flat list of optimized lines (skip section headers & blank)
    opt_lines = []
    for ln in optimized_text.split("\n"):
        s = ln.strip()
        if s:
            opt_lines.append(s)

    opt_idx = 0  # walk through opt_lines page by page

    for page in doc:
        page_dict = page.get_text("dict")

        for block in page_dict.get("blocks", []):
            if block.get("type") != 0:   # 0 = text block
                continue

            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    orig_text = span["text"].strip()
                    if not orig_text or opt_idx >= len(opt_lines):
                        continue

                    new_text = opt_lines[opt_idx]
                    opt_idx += 1

                    # Only touch spans that changed
                    if orig_text == new_text:
                        continue

                    bbox   = fitz.Rect(span["bbox"])
                    fsize  = span.get("size", 10)
                    color  = span.get("color", 0)
                    r = ((color >> 16) & 0xFF) / 255.0
                    g = ((color >>  8) & 0xFF) / 255.0
                    b = ( color        & 0xFF) / 255.0

                    # 1. Whiteout the original span
                    page.draw_rect(bbox, color=(1,1,1), fill=(1,1,1))

                    # 2. Write new text in same box, same font size & color
                    page.insert_textbox(
                        bbox,
                        new_text,
                        fontsize=fsize,
                        color=(r, g, b),
                        align=fitz.TEXT_ALIGN_LEFT,
                    )

    buf = io.BytesIO()
    doc.save(buf, garbage=4, deflate=True)
    buf.seek(0)
    return buf.read()

st.set_page_config(page_title="Resume Optimizer", page_icon="✦", layout="wide", initial_sidebar_state="collapsed")

for k, v in [("page","landing"),("logged_in",False),("user_name",""),("result",None),("score_data",None),("resume_text",""),("pdf_bytes",None)]:
    if k not in st.session_state: st.session_state[k] = v

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,400&family=Inter:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"], .stApp { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header,
[data-testid="stDecoration"],
[data-testid="collapsedControl"] { visibility: hidden !important; display: none !important; }

/* ── FULL APP BACKGROUND — soft pastel violet ── */
.stApp {
    background: linear-gradient(135deg, #f3eeff 0%, #ede4ff 35%, #e8dbff 65%, #e2d4ff 100%) !important;
    min-height: 100vh;
}
.block-container {
    max-width: 1200px !important;
    padding: 0 2rem 4rem !important;
    margin: 0 auto !important;
}

/* Kill streamlit's own white backgrounds on every container */
[data-testid="stVerticalBlock"],
[data-testid="column"],
section[data-testid="stSidebar"],
.css-1d391kg, .css-12oz5g7 {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* ── NAVBAR ── */
.topnav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1.3rem 0 1rem;
    border-bottom: 1px solid rgba(109,40,217,0.12);
    margin-bottom: 1rem;
}
.topnav-logo {
    font-family: 'Playfair Display', serif; font-style: italic;
    font-size: 1.65rem; font-weight: 700; color: #3b1f6b;
}
.topnav-right { color: #8b6fc0; font-size: 0.85rem; font-weight: 500; }

/* ── LANDING HERO ── */
.hero-left { padding: 2.5rem 0 2rem; animation: fadeUp 0.8s ease both; }
.eyebrow {
    display: inline-block;
    background: rgba(109,40,217,0.1); border: 1px solid rgba(109,40,217,0.2);
    color: #6d28d9; font-size: 0.68rem; font-weight: 600;
    letter-spacing: 0.18em; text-transform: uppercase;
    padding: 0.4rem 1.1rem; border-radius: 50px; margin-bottom: 1.5rem;
}
.hero-left h1 {
    font-family: 'Playfair Display', serif; font-weight: 700;
    font-size: clamp(2.2rem, 4vw, 3.5rem); color: #2e0a5e;
    line-height: 1.15; letter-spacing: -0.02em; margin-bottom: 1rem;
}
.hero-left h1 em { font-style: italic; font-weight: 400; color: #7c3aed; }
.hero-left p { color: #6b5f8a; font-size: 0.95rem; line-height: 1.75; max-width: 420px; margin-bottom: 1.8rem; }
.ticks { list-style: none; padding: 0; margin-bottom: 2rem; }
.ticks li { color: #4a3a6e; font-size: 0.85rem; padding: 0.26rem 0; display: flex; align-items: center; gap: 0.6rem; }
.ck { width: 17px; height: 17px; background: rgba(109,40,217,0.1); border: 1px solid rgba(109,40,217,0.25); border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 0.52rem; flex-shrink: 0; color: #7c3aed; }
.socials { display: flex; gap: 0.9rem; margin-top: 1.8rem; }
.social-icon { width: 34px; height: 34px; background: rgba(109,40,217,0.08); border: 1px solid rgba(109,40,217,0.18); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.78rem; color: #7c3aed; }

/* ── 3D CARD ── */
.hero-scene { position: relative; display: flex; align-items: center; justify-content: center; height: 520px; animation: fadeUp 1s ease both 0.2s; }
.main-card { width: 295px; height: 380px; background: linear-gradient(160deg, rgba(255,255,255,0.14) 0%, rgba(255,255,255,0.04) 100%); backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.18); border-radius: 24px; box-shadow: 0 40px 80px rgba(0,0,0,0.5); position: relative; z-index: 5; padding: 1.7rem 1.5rem; transform: perspective(900px) rotateY(-6deg) rotateX(2deg); animation: cardFloat 6s ease-in-out infinite; overflow: hidden; }
.main-card::before { content: ''; position: absolute; top: -50px; right: -50px; width: 150px; height: 150px; background: radial-gradient(circle, rgba(196,181,253,0.25) 0%, transparent 70%); border-radius: 50%; }
.res-hd { display: flex; align-items: center; gap: 0.7rem; margin-bottom: 1.1rem; }
.res-av { width: 42px; height: 42px; border-radius: 50%; background: linear-gradient(135deg,#c4b5fd,#7c3aed); display: flex; align-items: center; justify-content: center; font-size: 1.1rem; flex-shrink: 0; }
.res-nm { color: #fff; font-weight: 700; font-size: 0.88rem; }
.res-rl { color: rgba(255,255,255,0.45); font-size: 0.66rem; margin-top: 0.08rem; }
.res-ln { height: 6px; border-radius: 5px; background: rgba(255,255,255,0.12); margin-bottom: 0.5rem; }
.res-ln.w90{width:90%}.res-ln.w70{width:70%}.res-ln.w55{width:55%;background:rgba(196,181,253,0.18)}.res-ln.w80{width:80%}
.res-sec-lbl { font-size: 0.56rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: #a78bfa; margin: 0.8rem 0 0.5rem; }
.res-chips { display: flex; gap: 0.3rem; flex-wrap: wrap; margin-bottom: 0.6rem; }
.res-chip { background: rgba(167,139,250,0.15); border: 1px solid rgba(167,139,250,0.25); color: rgba(255,255,255,0.75); font-size: 0.56rem; font-weight: 600; padding: 0.18rem 0.55rem; border-radius: 50px; }
.sc-dot { position: absolute; bottom: 1.3rem; right: 1.3rem; width: 58px; height: 58px; background: linear-gradient(135deg,#7c3aed,#a78bfa); border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; box-shadow: 0 6px 18px rgba(124,58,237,0.6); animation: pulseDot 3s ease-in-out infinite; }
.sc-dot .sn { color: #fff; font-weight: 800; font-size: 0.95rem; line-height: 1; }
.sc-dot .sl { color: rgba(255,255,255,0.65); font-size: 0.42rem; letter-spacing: 0.08em; text-transform: uppercase; }
.fcard { position: absolute; background: rgba(30,5,80,0.7); backdrop-filter: blur(16px); border: 1px solid rgba(255,255,255,0.15); border-radius: 14px; padding: 0.8rem 0.95rem; box-shadow: 0 8px 28px rgba(0,0,0,0.35); z-index: 8; min-width: 125px; }
.fcard-t { color: #e9d5ff; font-weight: 700; font-size: 0.75rem; margin-bottom: 0.38rem; }
.fcard-s { color: rgba(255,255,255,0.45); font-size: 0.63rem; }
.fc-ats  { top: 24px; right: -12px; animation: fcF1 4.5s ease-in-out infinite; }
.fc-match{ bottom: 50px; left: -22px; animation: fcF2 5s ease-in-out infinite 0.8s; }
.fc-tag  { top: 72px; left: -28px; padding: 0.5rem 0.85rem; animation: fcF3 4s ease-in-out infinite 0.3s; }
.fc-kw   { bottom: 22px; right: -8px; padding: 0.5rem 0.85rem; animation: fcF1 5.5s ease-in-out infinite 1.2s; }
.ats-row { display: flex; align-items: center; gap: 0.38rem; margin-bottom: 0.28rem; }
.ats-lb  { color: rgba(255,255,255,0.45); font-size: 0.56rem; width: 42px; flex-shrink: 0; }
.ats-bg  { flex: 1; height: 4px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; }
.ats-fl  { height: 100%; border-radius: 4px; background: linear-gradient(90deg,#a78bfa,#c4b5fd); }
.match-c { width: 46px; height: 46px; background: linear-gradient(135deg,#10b981,#34d399); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.82rem; color: #fff; margin: 0 auto 0.38rem; }
.bgblob  { position: absolute; border-radius: 50%; filter: blur(60px); z-index: 0; }
.blob1   { width: 340px; height: 340px; background: rgba(139,92,246,0.18); top: -30px; right: -30px; }
.blob2   { width: 220px; height: 220px; background: rgba(109,40,217,0.22); bottom: 15px; right: 55px; }
.sparkle { position: absolute; color: rgba(255,255,255,0.3); font-size: 1rem; animation: spk 6s ease-in-out infinite; z-index: 1; }
.sp1{top:13%;left:11%}.sp2{top:27%;right:6%;font-size:0.82rem;animation-delay:1.5s}.sp3{bottom:17%;left:7%;font-size:0.62rem;animation-delay:3s}

/* ── LANDING STATS + FEATURES ── */
.lstats { display: flex; justify-content: center; gap: 3rem; padding: 1.6rem 0; border-top: 1px solid rgba(109,40,217,0.1); margin-top: 0.5rem; }
.lstats-n { font-family: 'Playfair Display', serif; font-size: 1.85rem; font-weight: 700; color: #2e0a5e; text-align: center; }
.lstats-l { font-size: 0.7rem; color: #8b6fc0; letter-spacing: 0.1em; text-transform: uppercase; margin-top: 0.12rem; text-align: center; }
.lfeats   { display: grid; grid-template-columns: repeat(3,1fr); gap: 1rem; margin: 1.4rem 0; }
.lfeat    { background: rgba(255,255,255,0.6); border: 1px solid rgba(109,40,217,0.1); border-radius: 14px; padding: 1.3rem; }
.lfeat-ic { font-size: 1.5rem; margin-bottom: 0.55rem; }
.lfeat-tt { color: #2e0a5e; font-weight: 600; font-size: 0.88rem; margin-bottom: 0.28rem; }
.lfeat-ds { color: #8b6fc0; font-size: 0.78rem; line-height: 1.52; }

/* ── AUTH TITLE ── */
.auth-title { font-family: 'Playfair Display', serif; font-weight: 700; font-size: 1.75rem; color: #2e0a5e; text-align: center; margin-bottom: 0.25rem; }
.auth-title em { font-style: italic; font-weight: 400; color: #7c3aed; }
.auth-sub { text-align: center; font-size: 0.83rem; color: #8b6fc0; margin-bottom: 1.6rem; }

/* ── ALL STREAMLIT INPUTS — white bg, dark readable text ── */
.stTextInput > div > div > input {
    background: #fff !important;
    border: 1.5px solid #ddd6fe !important;
    border-radius: 12px !important;
    color: #2e0a5e !important;
    font-size: 0.9rem !important;
    padding: 0.75rem 1rem !important;
    caret-color: #7c3aed !important;
}
.stTextInput > div > div > input:focus {
    border-color: #7c3aed !important;
    background: #fff !important;
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.12) !important;
}
.stTextInput > div > div > input::placeholder { color: #c4b5fd !important; }

.stTextArea > div > div > textarea {
    background: #fff !important;
    border: 1.5px solid #ddd6fe !important;
    border-radius: 12px !important;
    color: #2e0a5e !important;
    font-size: 0.87rem !important;
    padding: 0.75rem 1rem !important;
    line-height: 1.65 !important;
    caret-color: #7c3aed !important;
}
.stTextArea > div > div > textarea:focus {
    border-color: #7c3aed !important;
    background: #fff !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.12) !important;
}
.stTextArea > div > div > textarea::placeholder { color: #c4b5fd !important; }

/* ── FILE UPLOADER ── */
.stFileUploader > div {
    background: rgba(139,92,246,0.08) !important;
    border: 1.5px dashed rgba(167,139,250,0.4) !important;
    border-radius: 14px !important;
    padding: 1.2rem !important;
}
.stFileUploader p, .stFileUploader span, .stFileUploader small,
[data-testid="stFileUploaderDropzoneInstructions"] {
    color: rgba(196,181,253,0.7) !important;
    font-size: 0.82rem !important;
}
/* Browse files button — white with black text */
[data-testid="stFileUploaderDropzone"] button,
.stFileUploader button {
    background: #fff !important;
    color: #1a0533 !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.84rem !important;
    padding: 0.55rem 1.2rem !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
}
/* uploaded file name + size */
[data-testid="stFileUploaderFile"],
[data-testid="stFileUploaderFileName"],
[data-testid="stFileUploaderFileData"] span,
.stFileUploader [data-testid="stMarkdownContainer"] p,
section[data-testid="stFileUploader"] span {
    color: #3b1f6b !important;
}
/* the delete X button */
[data-testid="stFileUploaderDeleteBtn"] { color: #6d28d9 !important; }

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #6d28d9, #8b5cf6) !important;
    color: #fff !important; border: none !important;
    border-radius: 50px !important; padding: 0.8rem 1.8rem !important;
    font-weight: 600 !important; font-size: 0.86rem !important;
    width: 100% !important;
    box-shadow: 0 6px 20px rgba(109,40,217,0.4) !important;
    transition: all 0.25s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 28px rgba(109,40,217,0.5) !important;
}
.stDownloadButton > button {
    background: #3b1f6b !important;
    color: #fff !important;
    border: none !important;
    border-radius: 50px !important; font-weight: 600 !important;
    font-size: 0.84rem !important; width: 100% !important;
    padding: 0.75rem !important; margin-top: 0.8rem !important;
    box-shadow: 0 4px 14px rgba(59,31,107,0.35) !important;
    transition: all 0.3s ease !important;
}
.stDownloadButton > button:hover { background: #2e0a5e !important; box-shadow: 0 6px 20px rgba(59,31,107,0.5) !important; }

/* Hide "Press Enter to apply" tooltip on inputs */
[data-testid="InputInstructions"],
.stTextInput [data-testid="InputInstructions"],
small[data-testid="InputInstructions"] {
    display: none !important;
    visibility: hidden !important;
}
label,
.stTextInput label,
.stTextArea label,
.stFileUploader label {
    color: #8b6fc0 !important;
    font-size: 0.67rem !important; font-weight: 600 !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important;
}

/* ── RADIO ── */
.stRadio > div > label { color: #4a3a6e !important; font-size: 0.87rem !important; }
.stRadio > div > label > div:first-child div { border-color: rgba(109,40,217,0.4) !important; }

/* ── SPINNER / ALERTS ── */
.stAlert { background: rgba(237,233,254,0.8) !important; border: 1px solid #c4b5fd !important; border-radius: 12px !important; color: #5b21b6 !important; }
.stSpinner > div { border-top-color: #7c3aed !important; }

/* ── DASHBOARD SECTION HEADING ── */
.section-head {
    font-family: 'Playfair Display', serif; font-weight: 700;
    font-size: 1.7rem; color: #2e0a5e; text-align: center; margin-bottom: 0.3rem;
}
.section-head em { font-style: italic; color: #7c3aed; font-weight: 400; }
.section-sub { text-align: center; color: #8b6fc0; font-size: 0.88rem; margin-bottom: 1.8rem; }

/* ── DASHBOARD PANELS ── */
.panel {
    background: rgba(255,255,255,0.55);
    border: 1px solid rgba(196,181,253,0.35);
    border-radius: 18px;
    padding: 1.4rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 16px rgba(109,40,217,0.06);
}
.panel-title {
    font-size: 0.95rem; font-weight: 900;
    color: #2e0a5e;
    letter-spacing: 0.14em; text-transform: uppercase;
    margin-bottom: 1.2rem;
    display: flex; align-items: center; justify-content: center; gap: 0.5rem;
    width: 100%;
    background: #fff;
    padding: 0.65rem 1.2rem;
    border-radius: 50px;
    box-shadow: 0 3px 12px rgba(109,40,217,0.12);
}

/* ── SCORE RING ── */
.score-wrap { text-align: center; padding: 0.6rem 0 0.5rem; }
.score-outer { width: 118px; height: 118px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 0.7rem; position: relative; }
.score-inner { width: 84px; height: 84px; background: #ede9fe; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; position: absolute; box-shadow: inset 0 2px 8px rgba(109,40,217,0.1); }
.score-n { font-family: 'Playfair Display', serif; font-size: 1.9rem; color: #3b1f6b; font-weight: 700; line-height: 1; }
.score-d { font-size: 0.63rem; color: #3b1f6b; }
.score-lbl { font-weight: 700; font-size: 0.88rem; margin-bottom: 1rem; }

/* score bars */
.sbar-row  { display: flex; align-items: center; margin-bottom: 0.68rem; }
.sbar-name { font-size: 0.74rem; color: #3b1f6b; font-weight: 600; width: 90px; flex-shrink: 0; }
.sbar-bg   { flex: 1; height: 6px; background: rgba(196,181,253,0.25); border-radius: 6px; overflow: hidden; margin: 0 0.6rem; }
.sbar-fill { height: 100%; border-radius: 6px; background: #3b1f6b; }
.sbadge    { font-size: 0.6rem; font-weight: 700; padding: 0.2rem 0.65rem; border-radius: 20px; white-space: nowrap; min-width: 82px; text-align: center; }
.bg-great  { background: #3b1f6b; color: #fff !important; }
.bg-good   { background: #3b1f6b; color: #fff !important; }
.bg-ok     { background: #3b1f6b; color: #fff !important; }
.bg-weak   { background: rgba(255,179,179,0.75); color: #3b1f6b !important; }

/* ── RESUME PREVIEW ── */
.resume-box {
    background: rgba(255,255,255,0.7);
    border: 1px solid rgba(196,181,253,0.3);
    border-radius: 12px; padding: 1.3rem;
    font-size: 0.78rem; line-height: 1.78;
    color: #2e0a5e;
    max-height: 520px; overflow-y: auto;
    white-space: pre-wrap; font-family: 'Inter', sans-serif;
}

/* ── RECOMMENDATIONS ── */
.rec-item { border-left: 3px solid; border-radius: 0 10px 10px 0; padding: 0.7rem 0.95rem; margin-bottom: 0.6rem; font-size: 0.79rem; line-height: 1.55; }
.rec-hi   { background: rgba(254,226,226,0.8); border-color: #ef4444; color: #7f1d1d; }
.rec-md   { background: rgba(254,243,199,0.8); border-color: #f59e0b; color: #78350f; }
.rec-lo   { background: rgba(236,253,245,0.8); border-color: #10b981; color: #064e3b; }
.rec-lbl  { font-size: 0.58rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 0.22rem; }
.rec-lbl-hi{color:#dc2626}.rec-lbl-md{color:#d97706}.rec-lbl-lo{color:#059669}

/* ── SCORE BREAKDOWN ── */
.bd-row  { display: flex; align-items: center; justify-content: space-between; padding: 0.42rem 0; border-bottom: 1px solid rgba(196,181,253,0.2); }
.bd-name { font-size: 0.76rem; color: #8b6fc0; }
.bd-val  { font-size: 0.76rem; font-weight: 700; }

/* ── ANIMATIONS ── */
@keyframes fadeUp { from{opacity:0;transform:translateY(14px)} to{opacity:1;transform:translateY(0)} }
@keyframes cardFloat { 0%,100%{transform:perspective(900px) rotateY(-6deg) rotateX(2deg) translateY(0)} 50%{transform:perspective(900px) rotateY(-6deg) rotateX(2deg) translateY(-12px)} }
@keyframes pulseDot { 0%,100%{transform:scale(1)} 50%{transform:scale(1.06)} }
@keyframes fcF1 { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }
@keyframes fcF2 { 0%,100%{transform:translateY(0)} 50%{transform:translateY(7px)} }
@keyframes fcF3 { 0%,100%{transform:translateY(0) rotate(-1deg)} 50%{transform:translateY(-7px) rotate(1deg)} }
@keyframes spk  { 0%,100%{opacity:0.22;transform:scale(1)} 50%{opacity:0.65;transform:scale(1.22)} }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════
# HELPERS
# ══════════════════════════════
def score_color(s):
    if s >= 80: return "#3b1f6b", "bg-great", "Excellent"
    if s >= 60: return "#3b1f6b", "bg-good",  "Good"
    if s >= 40: return "#3b1f6b", "bg-ok",    "Fair"
    return "#3b1f6b", "bg-weak", "Needs Work"

def score_bar(name, score):
    color, badge, label = score_color(score)
    st.markdown(f"""
    <div class="sbar-row">
      <div class="sbar-name">{name}</div>
      <div class="sbar-bg"><div class="sbar-fill" style="width:{score}%;background:#3b1f6b"></div></div>
      <span class="sbadge {badge}">{score} — {label}</span>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════
# LANDING
# ══════════════════════════════
def page_landing():
    st.markdown("""
    <div class="topnav">
      <div class="topnav-logo">Resume Optimizer.</div>
      <div class="topnav-right">AI-Powered Resume Tool</div>
    </div>""", unsafe_allow_html=True)

    lc, rc = st.columns([1, 1], gap="large")

    with lc:
        st.markdown("""
        <div class="hero-left">
          <div class="eyebrow">✦ AI-Powered Resume Intelligence</div>
          <h1>Turn Your Resume Into<br>a <em>Career Magnet</em></h1>
          <p>Upload your resume, paste a job description, and get an instant AI score with STAR-method rewrites tailored to get you hired faster.</p>
          <ul class="ticks">
            <li><span class="ck">✓</span> Instant score across 5 key categories</li>
            <li><span class="ck">✓</span> AI rewrites every bullet using STAR method</li>
            <li><span class="ck">✓</span> ATS keyword gap analysis</li>
            <li><span class="ck">✓</span> Job-specific recommendations</li>
          </ul>
        </div>""", unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("✦  Score My Resume", key="hs"):
                st.session_state.page = "login"; st.rerun()
        with b2:
            if st.button("→  Sign In", key="hsi"):
                st.session_state.page = "login"; st.rerun()
        st.markdown("""
        <div class="socials">
          <div class="social-icon">in</div>
          <div class="social-icon">𝕏</div>
          <div class="social-icon">f</div>
        </div>""", unsafe_allow_html=True)

    with rc:
        st.markdown("""
        <div class="hero-scene">
          <div class="bgblob blob1"></div><div class="bgblob blob2"></div>
          <div class="sparkle sp1">✦</div><div class="sparkle sp2">✦</div><div class="sparkle sp3">✦</div>

          <div class="main-card">
            <div class="res-hd">
              <div class="res-av">👤</div>
              <div><div class="res-nm">Alex Johnson</div><div class="res-rl">Software Engineer</div></div>
            </div>
            <div class="res-sec-lbl">Experience</div>
            <div class="res-ln w90"></div><div class="res-ln w70"></div><div class="res-ln w80"></div>
            <div class="res-sec-lbl">Skills</div>
            <div class="res-chips">
              <span class="res-chip">Python</span><span class="res-chip">React</span>
              <span class="res-chip">SQL</span><span class="res-chip">AWS</span>
            </div>
            <div class="res-sec-lbl">Education</div>
            <div class="res-ln w55"></div><div class="res-ln w70"></div>
            <div class="sc-dot"><div class="sn">92</div><div class="sl">Score</div></div>
          </div>

          <div class="fcard fc-ats">
            <div class="fcard-t">📊 ATS Score</div>
            <div class="ats-row"><div class="ats-lb">Impact</div><div class="ats-bg"><div class="ats-fl" style="width:88%"></div></div></div>
            <div class="ats-row"><div class="ats-lb">Skills</div><div class="ats-bg"><div class="ats-fl" style="width:72%"></div></div></div>
            <div class="ats-row"><div class="ats-lb">Format</div><div class="ats-bg"><div class="ats-fl" style="width:95%"></div></div></div>
          </div>
          <div class="fcard fc-match">
            <div class="fcard-t">🎯 Job Match</div>
            <div class="match-c">87%</div>
            <div class="fcard-s" style="text-align:center">Great fit!</div>
          </div>
          <div class="fcard fc-tag">
            <div style="font-size:0.7rem;font-weight:700;color:#c4b5fd;">🤖 AI Optimized</div>
            <div style="font-size:0.6rem;color:rgba(255,255,255,0.4);margin-top:0.12rem;">STAR method applied</div>
          </div>
          <div class="fcard fc-kw">
            <div style="font-size:0.7rem;font-weight:700;color:#e9d5ff;">⚡ 12 Keywords Added</div>
            <div style="font-size:0.6rem;color:rgba(255,255,255,0.4);margin-top:0.12rem;">ATS ready</div>
          </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("""
    <div class="lstats">
      <div><div class="lstats-n">50K+</div><div class="lstats-l">Resumes Scored</div></div>
      <div><div class="lstats-n">94%</div><div class="lstats-l">Interview Rate</div></div>
      <div><div class="lstats-n">4.9★</div><div class="lstats-l">User Rating</div></div>
      <div><div class="lstats-n">30%</div><div class="lstats-l">Higher Callbacks</div></div>
    </div>
    <div class="lfeats">
      <div class="lfeat"><div class="lfeat-ic">📊</div><div class="lfeat-tt">Instant Resume Score</div><div class="lfeat-ds">Scored across 5 key categories — impact, skills, formatting, ATS, and experience.</div></div>
      <div class="lfeat"><div class="lfeat-ic">🤖</div><div class="lfeat-tt">AI-Powered Rewrites</div><div class="lfeat-ds">Every bullet rewritten with STAR method to maximize recruiter impact.</div></div>
      <div class="lfeat"><div class="lfeat-ic">🎯</div><div class="lfeat-tt">Job-Specific Feedback</div><div class="lfeat-ds">Paste any job description and get tailored recommendations instantly.</div></div>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════
# LOGIN
# ══════════════════════════════
def page_login():
    st.markdown("""<div class="topnav"><div class="topnav-logo">Resume Optimizer.</div></div>""", unsafe_allow_html=True)
    tab = st.radio("", ["Sign In", "Create Account"], horizontal=True, label_visibility="collapsed")
    _, mid, _ = st.columns([1, 1.2, 1])
    with mid:
        if tab == "Sign In":
            st.markdown('<div class="auth-title">Welcome <em>Back</em></div><div class="auth-sub">Sign in to your account</div>', unsafe_allow_html=True)
            email    = st.text_input("Email", placeholder="you@email.com")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Sign In  →", key="si"):
                    if email and password:
                        st.session_state.logged_in = True
                        st.session_state.user_name = email.split("@")[0].capitalize()
                        st.session_state.page = "dashboard"; st.rerun()
                    else: st.error("Please fill in all fields.")
            with b2:
                if st.button("← Back to Home", key="bh"):
                    st.session_state.page = "landing"; st.rerun()
        else:
            st.markdown('<div class="auth-title">Get <em>Started</em></div><div class="auth-sub">Create your free account</div>', unsafe_allow_html=True)
            name     = st.text_input("Full Name", placeholder="Your Name")
            email    = st.text_input("Email", placeholder="you@email.com")
            password = st.text_input("Password", type="password", placeholder="Create a password")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("Create Account  →", key="ca"):
                    if name and email and password:
                        st.session_state.logged_in = True
                        st.session_state.user_name = name.split()[0].capitalize()
                        st.session_state.page = "dashboard"; st.rerun()
                    else: st.error("Please fill in all fields.")
            with b2:
                if st.button("← Back to Home", key="bh2"):
                    st.session_state.page = "landing"; st.rerun()


# ══════════════════════════════
# DASHBOARD
# ══════════════════════════════
def page_dashboard():
    st.markdown(f"""
    <div class="topnav">
      <div class="topnav-logo">Resume Optimizer.</div>
      <div class="topnav-right">Hi, {st.session_state.user_name} 👋</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── UPLOAD FORM ──
    if not st.session_state.result:
        st.markdown("""
        <div class="section-head">Analyze Your <em>Resume</em></div>
        <div class="section-sub">Upload your PDF and paste a job description to get your AI score</div>
        """, unsafe_allow_html=True)

        uc, jc = st.columns([1,1], gap="large")
        with uc:
            st.markdown('<div class="panel"><div class="panel-title">📎 Upload Resume (PDF)</div>', unsafe_allow_html=True)
            uploaded = st.file_uploader("PDF", type=["pdf"], label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)
        with jc:
            st.markdown('<div class="panel"><div class="panel-title">💼 Job Description</div>', unsafe_allow_html=True)
            job_desc = st.text_area("jd", height=155, placeholder="Paste the job description here…", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

        _, bc, _ = st.columns([1,1.2,1])
        with bc:
            go = st.button("✦  Analyze & Score My Resume")

        if go:
            if not uploaded:          st.error("Please upload your resume PDF.")
            elif not job_desc.strip(): st.error("Please paste a job description.")
            elif not GROQ_API_KEY:     st.error("GROQ_API_KEY not found in .env file.")
            else:
                with st.spinner("Reading your resume..."):
                    raw_bytes = uploaded.read()
                    doc = fitz.open(stream=raw_bytes, filetype="pdf")
                    resume_text = "".join(p.get_text() for p in doc)
                    st.session_state.resume_text = resume_text
                    st.session_state.pdf_bytes = raw_bytes

                with st.spinner("Scoring and optimizing with AI..."):
                    client = Groq(api_key=GROQ_API_KEY)

                    sr = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role":"user","content":f"""Score this resume on 5 topics (0-100). Reply ONLY with this exact JSON, no other text:
{{"impact":72,"skills":65,"formatting":80,"ats":58,"experience":70}}

Job: {job_desc[:600]}
Resume: {resume_text[:1800]}"""}],
                        max_tokens=100
                    )
                    raw = sr.choices[0].message.content.strip()
                    try:
                        m = re.search(r'\{.*\}', raw, re.DOTALL)
                        scores = json.loads(m.group()) if m else {}
                    except:
                        scores = {"impact":65,"skills":60,"formatting":70,"ats":55,"experience":65}
                    st.session_state.score_data = scores

                    or_ = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role":"user","content":f"""You are an expert ATS resume writer and career coach with 15+ years experience. Your task is to produce a highly optimized, job-specific resume.

STRICT RULES:
- Keep ALL original jobs, companies, dates, education, and qualifications — never invent anything
- Rewrite EVERY bullet point using the STAR method (Situation→Task→Action→Result)
- Add quantified metrics wherever possible (%, $, numbers, time saved)
- Front-load each bullet with a strong action verb (Engineered, Drove, Spearheaded, Delivered, etc.)
- Mirror keywords and phrases directly from the job description for ATS matching
- Keep bullets to 1-2 lines max — concise, punchy, scannable
- Use consistent formatting: name/contact at top, then Summary, Experience, Skills, Education
- Add a 2-line Professional Summary tailored to the job description at the top
- Ensure 85-90%+ keyword match with the job description

OUTPUT FORMAT — output ONLY the resume, no commentary:

## OPTIMIZED RESUME
[Full optimized resume here]

## RECOMMENDATIONS
HIGH: [critical fix 1]
HIGH: [critical fix 2]
MEDIUM: [important fix 1]
MEDIUM: [important fix 2]
LOW: [nice to have fix]

Job Description:
{job_desc[:800]}

Original Resume:
{resume_text[:2500]}"""}],
                        max_tokens=1800
                    )
                    st.session_state.result = or_.choices[0].message.content
                    st.rerun()

    # ── RESULTS ──
    else:
        result = st.session_state.result
        scores = st.session_state.score_data or {}

        opt_resume, recs = "", []
        if "## OPTIMIZED RESUME" in result and "## RECOMMENDATIONS" in result:
            parts = result.split("## RECOMMENDATIONS")
            opt_resume = parts[0].replace("## OPTIMIZED RESUME","").strip()
            for line in parts[1].strip().split("\n"):
                line = line.strip()
                if line: recs.append(line)
        else:
            opt_resume = result

        overall = int(sum(scores.values())/len(scores)) if scores else 70
        oc, _, ol = score_color(overall)
        od = overall * 3.6

        sc, rc, recc = st.columns([1, 1.5, 1], gap="large")

        # LEFT — Score
        with sc:
            st.markdown('<div class="panel"><div class="panel-title">📊 Resume Score</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="score-wrap">
              <div class="score-outer" style="background:conic-gradient(#3b1f6b {od}deg, rgba(196,181,253,0.25) 0deg);">
                <div class="score-inner">
                  <div class="score-n">{overall}</div>
                  <div class="score-d">/ 100</div>
                </div>
              </div>
              <div class="score-lbl" style="color:#3b1f6b">{ol}</div>
            </div>""", unsafe_allow_html=True)
            for k, lbl in [("impact","Impact"),("skills","Skills"),("formatting","Formatting"),("ats","ATS"),("experience","Experience")]:
                score_bar(lbl, scores.get(k, 65))
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Analyze New Resume", key="reset"):
                st.session_state.result = None
                st.session_state.score_data = None
                st.session_state.resume_text = ""
                st.session_state.pdf_bytes = None
                st.rerun()

        # CENTER — Resume
        with rc:
            st.markdown('<div class="panel"><div class="panel-title">📄 Optimized Resume</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="resume-box">{opt_resume}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            orig_bytes = st.session_state.get("pdf_bytes")
            if orig_bytes:
                out_pdf = edit_original_pdf(orig_bytes, opt_resume)
            else:
                out_pdf = edit_original_pdf(b"", opt_resume)
            st.download_button(
                "⬇️  Download Optimized PDF",
                data=out_pdf,
                file_name="optimized_resume.pdf",
                mime="application/pdf"
            )

        # RIGHT — Recs + Breakdown
        with recc:
            st.markdown('<div class="panel"><div class="panel-title">💡 Recommendations</div>', unsafe_allow_html=True)
            for line in recs[:5]:
                if line.upper().startswith("HIGH:"):
                    st.markdown(f'<div class="rec-item rec-hi"><div class="rec-lbl rec-lbl-hi">🔴 High Priority</div>{line[5:].strip()}</div>', unsafe_allow_html=True)
                elif line.upper().startswith("MEDIUM:"):
                    st.markdown(f'<div class="rec-item rec-md"><div class="rec-lbl rec-lbl-md">🟡 Medium</div>{line[7:].strip()}</div>', unsafe_allow_html=True)
                elif line.upper().startswith("LOW:"):
                    st.markdown(f'<div class="rec-item rec-lo"><div class="rec-lbl rec-lbl-lo">🟢 Low Priority</div>{line[4:].strip()}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="rec-item rec-md"><div class="rec-lbl rec-lbl-md">📌 Note</div>{line}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="panel"><div class="panel-title">📈 Score Breakdown</div>', unsafe_allow_html=True)
            for k, lbl in [("impact","Impact"),("skills","Skills"),("formatting","Formatting"),("ats","ATS"),("experience","Experience")]:
                s = scores.get(k, 65)
                c, _, lb = score_color(s)
                st.markdown(f'<div class="bd-row"><span class="bd-name">{lbl}</span><span class="bd-val" style="color:{c}">{s}/100 — {lb}</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════
# ROUTER
# ══════════════════════════════
if not st.session_state.logged_in and st.session_state.page == "dashboard":
    st.session_state.page = "login"

if   st.session_state.page == "landing":    page_landing()
elif st.session_state.page == "login":      page_login()
elif st.session_state.page == "dashboard":  page_dashboard()