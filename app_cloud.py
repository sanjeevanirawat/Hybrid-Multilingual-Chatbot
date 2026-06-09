import streamlit as st
from chatbot_engine_cloud import chatbot, load_store
from datetime import datetime
from translator import detect_language

st.set_page_config(
    page_title="LinguaBot",
    layout="centered",
    initial_sidebar_state="collapsed"
)

LANG_INFO = {
    "en": ("🇬🇧", "English"), "hi": ("🇮🇳", "Hindi"),
    "ta": ("🇮🇳", "Tamil"),   "bn": ("🇧🇩", "Bengali"),
    "mr": ("🇮🇳", "Marathi"), "te": ("🇮🇳", "Telugu"),
    "ur": ("🇵🇰", "Urdu"),    "gu": ("🇮🇳", "Gujarati"),
    "pa": ("🇮🇳", "Punjabi"), "kn": ("🇮🇳", "Kannada"),
    "ml": ("🇮🇳", "Malayalam"),
}

def get_greeting():
    hour = datetime.utcnow().hour + 5  # IST offset
    if hour < 12:
        return "Good Morning", "🌅"
    elif hour < 17:
        return "Good Afternoon", "☀️"
    elif hour < 21:
        return "Good Evening", "🌆"
    else:
        return "Good Night", "🌙"

greeting, emoji = get_greeting()

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
.stApp { background: #0f1117; }

.header-bar {
    background: #141820; border-bottom: 1px solid #1e2530;
    padding: 13px 20px; display: flex; align-items: center;
    justify-content: space-between; position: sticky; top: 0; z-index: 100;
}
.header-logo { font-size: 18px; font-weight: 600; color: #e8eaf0; }
.header-logo span { color: #4f8ef7; }
.header-status { display: flex; align-items: center; gap: 6px; font-size: 11px; color: #6b7280; }
.status-dot { width: 7px; height: 7px; background: #22c55e; border-radius: 50%; animation: pulse 2s infinite; display: inline-block; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

/* Welcome hero */
.hero {
    background: linear-gradient(135deg, #141820 0%, #1a2035 100%);
    border: 1px solid #1e2530; border-radius: 16px;
    padding: 32px 24px 28px; text-align: center;
    margin: 20px 16px 0;
}
.hero-emoji { font-size: 40px; margin-bottom: 10px; }
.hero-greeting { font-size: 13px; color: #4f8ef7; font-weight: 500; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 6px; }
.hero-title { font-size: 26px; font-weight: 600; color: #e8eaf0; margin-bottom: 10px; line-height: 1.2; }
.hero-title span { color: #4f8ef7; }
.hero-sub { font-size: 14px; color: #6b7280; line-height: 1.7; margin-bottom: 20px; }

/* Language chips */
.lang-section { margin: 0 16px 0; }
.lang-label { font-size: 10px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; padding-top: 16px; }
.lang-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { background: #1a1f2e; border: 1px solid #1e2530; border-radius: 20px; padding: 4px 11px; font-size: 12px; color: #9ca3af; display: inline-block; transition: all 0.2s; }
.chip:hover { background: #1e2d4a; border-color: #4f8ef7; color: #e8eaf0; }

/* Suggestion pills */
.suggestions { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-top: 4px; }
.suggestion {
    background: #1a1f2e; border: 1px solid #1e3a5c;
    border-radius: 20px; padding: 6px 14px;
    font-size: 12px; color: #4f8ef7; cursor: pointer;
    transition: all 0.2s;
}
.suggestion:hover { background: #1e2d4a; }

/* Upload panel */
.upload-panel { background: #141820; border: 1px solid #1e2530; border-radius: 12px; padding: 16px; margin: 14px 16px 0; }
.upload-label { font-size: 10px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 10px; }
.doc-pill { display: flex; align-items: center; gap: 8px; background: #1a1f2e; border: 1px solid #1e2530; border-radius: 8px; padding: 7px 10px; margin-top: 6px; font-size: 12px; color: #d1d5db; }
.doc-icon { color: #4f8ef7; }
.doc-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.doc-chunks { color: #6b7280; font-size: 10px; }
.success-banner { background: #0f2a1a; border: 1px solid #166534; border-radius: 8px; padding: 8px 12px; color: #22c55e; font-size: 12px; margin-top: 8px; }
.error-banner { background: #2a0f0f; border: 1px solid #991b1b; border-radius: 8px; padding: 8px 12px; color: #f87171; font-size: 12px; margin-top: 8px; }

/* Chat */
.chat-wrapper { max-width: 700px; margin: 0 auto; padding: 16px 16px 140px; }
.msg-row { display: flex; margin-bottom: 16px; gap: 8px; animation: fadeUp 0.3s ease; }
@keyframes fadeUp { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
.msg-row.user { flex-direction: row-reverse; }
.avatar { width: 30px; height: 30px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0; margin-top: 2px; font-weight: 600; }
.avatar.bot  { background: #1e2d4a; color: #4f8ef7; }
.avatar.user { background: #1a2a1a; color: #22c55e; }
.bubble-wrap { display: flex; flex-direction: column; max-width: 85%; }
.msg-row.user .bubble-wrap { align-items: flex-end; }
.bubble { padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.65; word-break: break-word; }
.bubble.bot  { background: #141820; border: 1px solid #1e2530; color: #d1d5db; border-radius: 4px 12px 12px 12px; }
.bubble.user { background: #1a3a5c; border: 1px solid #1e4a7a; color: #e2eeff; border-radius: 12px 4px 12px 12px; }
.lang-badge { display: inline-flex; align-items: center; gap: 4px; font-size: 10px; color: #6b7280; margin-top: 4px; padding: 2px 8px; background: #1a1f2e; border-radius: 20px; border: 1px solid #1e2530; }
.typing-indicator { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
.typing-dots { display: flex; gap: 5px; padding: 12px 15px; background: #141820; border: 1px solid #1e2530; border-radius: 4px 12px 12px 12px; }
.typing-dots span { width: 6px; height: 6px; background: #4f8ef7; border-radius: 50%; animation: bounce 1.2s infinite; }
.typing-dots span:nth-child(2){animation-delay:.2s} .typing-dots span:nth-child(3){animation-delay:.4s}
@keyframes bounce { 0%,60%,100%{transform:translateY(0);opacity:.4} 30%{transform:translateY(-5px);opacity:1} }

/* Input */
.input-area { position: fixed; bottom: 0; left: 0; right: 0; background: #0f1117; border-top: 1px solid #1e2530; padding: 10px 14px 14px; z-index: 99; }
.stTextInput > div > div > input { background: #141820 !important; border: 1px solid #1e2530 !important; border-radius: 10px !important; color: #e8eaf0 !important; font-family: 'DM Sans', sans-serif !important; font-size: 14px !important; padding: 11px 14px !important; caret-color: #4f8ef7; }
.stTextInput > div > div > input:focus { border-color: #4f8ef7 !important; box-shadow: 0 0 0 3px rgba(79,142,247,0.12) !important; }
.stTextInput > div > div > input::placeholder { color: #4b5563 !important; }
.stButton > button { background: #4f8ef7 !important; color: white !important; border: none !important; border-radius: 10px !important; padding: 11px 14px !important; font-family: 'DM Sans', sans-serif !important; font-size: 13px !important; font-weight: 500 !important; transition: background 0.2s !important; }
.stButton > button:hover { background: #3b7af0 !important; }
div[data-testid="stSpinner"] { display: none; }
[data-testid="stFileUploader"] { background: #1a1f2e !important; border: 1px dashed #1e4a7a !important; border-radius: 10px !important; padding: 6px !important; }
[data-testid="stExpander"] { background: #141820 !important; border: 1px solid #1e2530 !important; border-radius: 12px !important; margin: 10px 16px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──
if "messages"      not in st.session_state: st.session_state.messages = []
if "thinking"      not in st.session_state: st.session_state.thinking = False
if "uploaded_docs" not in st.session_state: st.session_state.uploaded_docs = []
if "upload_msg"    not in st.session_state: st.session_state.upload_msg = None
if "upload_ok"     not in st.session_state: st.session_state.upload_ok = True
if "input_key"     not in st.session_state: st.session_state.input_key = 0

store = load_store()

# ── Header ──
st.markdown("""
<div class="header-bar">
    <div class="header-logo">Lingua<span>Bot</span></div>
    <div class="header-status">
        <div class="status-dot"></div>
        HuggingFace · Cloud
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# WELCOME HERO — only shown before first message
# ══════════════════════════════════════════════
if not st.session_state.messages:
    st.markdown(f"""
    <div class="hero">
        <div class="hero-emoji">{emoji}</div>
        <div class="hero-greeting">{greeting}</div>
        <div class="hero-title">Welcome to <span>LinguaBot</span></div>
        <div class="hero-sub">
            Your multilingual AI assistant — ask me anything<br>
            in Hindi, Bengali, Tamil, Hinglish or any Indian language.
        </div>
        <div class="suggestions">
            <div class="suggestion">महिला सुरक्षा क्या है?</div>
            <div class="suggestion">What is GDP?</div>
            <div class="suggestion">আপনি কি বাংলায় কথা বলতে পারেন?</div>
            <div class="suggestion">AI kya hota hai?</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Language chips — always visible on home screen
    st.markdown("""
    <div class="lang-section">
        <div class="lang-label">Supported Languages</div>
        <div class="lang-chips">
            <span class="chip">🇮🇳 Hindi</span>
            <span class="chip">🇮🇳 Tamil</span>
            <span class="chip">🇧🇩 Bengali</span>
            <span class="chip">🇮🇳 Marathi</span>
            <span class="chip">🇮🇳 Telugu</span>
            <span class="chip">🇮🇳 Gujarati</span>
            <span class="chip">🇮🇳 Punjabi</span>
            <span class="chip">🇮🇳 Kannada</span>
            <span class="chip">🇮🇳 Malayalam</span>
            <span class="chip">🇵🇰 Urdu</span>
            <span class="chip">🇬🇧 English</span>
            <span class="chip">🔀 Hinglish</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# UPLOAD PANEL — always accessible
# ══════════════════════════════════════════════
with st.expander("📂  Upload Document", expanded=False):
    uploaded_file = st.file_uploader(
        label="PDF, TXT or Word files",
        type=["pdf", "txt", "docx"],
        label_visibility="visible"
    )
    if uploaded_file is not None:
        already = any(d["name"] == uploaded_file.name for d in st.session_state.uploaded_docs)
        if not already:
            if st.button("Add to Knowledge Base", use_container_width=True):
                with st.spinner(f"Processing {uploaded_file.name}..."):
                    try:
                        file_bytes = uploaded_file.read()
                        num_chunks = store.add(file_bytes, uploaded_file.name)
                        st.session_state.uploaded_docs.append({
                            "name":   uploaded_file.name,
                            "chunks": num_chunks,
                            "type":   uploaded_file.name.split(".")[-1].upper()
                        })
                        st.session_state.upload_msg = f"Added {num_chunks} chunks from {uploaded_file.name}"
                        st.session_state.upload_ok  = True
                    except Exception as e:
                        st.session_state.upload_msg = f"Error: {str(e)}"
                        st.session_state.upload_ok  = False
                st.rerun()
        else:
            st.markdown('<div class="error-banner">Already in knowledge base.</div>', unsafe_allow_html=True)

    if st.session_state.upload_msg:
        css_class = "success-banner" if st.session_state.upload_ok else "error-banner"
        st.markdown(f'<div class="{css_class}">{st.session_state.upload_msg}</div>', unsafe_allow_html=True)

    if st.session_state.uploaded_docs:
        icons = {"PDF": "📄", "TXT": "📝", "DOCX": "📘"}
        for doc in st.session_state.uploaded_docs:
            icon = icons.get(doc["type"], "📎")
            st.markdown(f"""
            <div class="doc-pill">
                <span class="doc-icon">{icon}</span>
                <span class="doc-name">{doc["name"]}</span>
                <span class="doc-chunks">{doc["chunks"]} chunks</span>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════
# CHAT MESSAGES
# ══════════════════════════════════════════════
st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg["role"] == "user":
        lang_code = detect_language(msg["content"])
        flag, lang_name = LANG_INFO.get(lang_code, ("🌐", lang_code.upper()))
        st.markdown(f"""
        <div class="msg-row user">
            <div class="avatar user">U</div>
            <div class="bubble-wrap">
                <div class="bubble user">{msg["content"]}</div>
                <div class="lang-badge">{flag} {lang_name}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="msg-row">
            <div class="avatar bot">AI</div>
            <div class="bubble-wrap">
                <div class="bubble bot">{msg["content"]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

if st.session_state.thinking:
    st.markdown("""
    <div class="typing-indicator">
        <div class="avatar bot">AI</div>
        <div class="typing-dots"><span></span><span></span><span></span></div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Input bar ──
st.markdown('<div class="input-area">', unsafe_allow_html=True)
col1, col2 = st.columns([8, 1])
with col1:
    user_input = st.text_input(
        label="", placeholder="Type in any language...",
        key=f"input_{st.session_state.input_key}",
        label_visibility="collapsed"
    )
with col2:
    send = st.button("Send", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.messages:
    if st.button("🗑 Clear chat", use_container_width=False):
        st.session_state.messages = []
        st.session_state.thinking = False
        st.session_state.input_key += 1
        st.rerun()

if send and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input.strip()})
    st.session_state.thinking  = True
    st.session_state.upload_msg = None
    st.session_state.input_key += 1
    st.rerun()

if st.session_state.thinking:
    history    = st.session_state.messages[:-1]
    last_query = st.session_state.messages[-1]["content"]
    response   = chatbot(last_query, history=history)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.thinking = False
    st.rerun()
# import streamlit as st
# import os
# from chatbot_engine_cloud import chatbot
# from datetime import datetime
# from translator import detect_language
# if not os.path.exists("data") or len(os.listdir("data")) == 0:
#     from fetch_wiki import fetch_wikipedia_data
#     fetch_wikipedia_data()
    
# st.set_page_config(
#     page_title="LinguaBot — Multilingual AI",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# LANG_INFO = {
#     "en": ("🇬🇧", "English"), "hi": ("🇮🇳", "Hindi"),
#     "ta": ("🇮🇳", "Tamil"),   "bn": ("🇧🇩", "Bengali"),
#     "mr": ("🇮🇳", "Marathi"), "te": ("🇮🇳", "Telugu"),
#     "ur": ("🇵🇰", "Urdu"),    "gu": ("🇮🇳", "Gujarati"),
#     "pa": ("🇮🇳", "Punjabi"), "kn": ("🇮🇳", "Kannada"),
#     "ml": ("🇮🇳", "Malayalam"),
# }

# def get_greeting():
#     hour = datetime.utcnow().hour + 5
#     if hour < 12: return "Good Morning", "🌅"
#     elif hour < 17: return "Good Afternoon", "☀️"
#     elif hour < 21: return "Good Evening", "🌆"
#     else: return "Good Night", "🌙"

# greeting, emoji = get_greeting()

# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

# *, html, body, [class*="css"] {
#     font-family: 'DM Sans', sans-serif;
#     box-sizing: border-box;
# }

# #MainMenu, footer, header { visibility: hidden; }
# .block-container { padding: 0 !important; max-width: 100% !important; }
# .stApp { background: #080c14; }

# /* ── SIDEBAR ── */
# section[data-testid="stSidebar"] {
#     background: #0c111c !important;
#     border-right: 1px solid #1a2235 !important;
#     width: 300px !important;
# }
# section[data-testid="stSidebar"] > div { padding: 0 !important; }

# .sb-brand {
#     padding: 28px 22px 22px;
#     border-bottom: 1px solid #1a2235;
#     background: linear-gradient(135deg, #0c111c 0%, #111827 100%);
# }
# .sb-brand-logo {
#     font-family: 'Syne', sans-serif;
#     font-size: 22px; font-weight: 800;
#     color: #e8edf5; letter-spacing: -0.5px;
#     margin-bottom: 4px;
# }
# .sb-brand-logo span { color: #4f8ef7; }
# .sb-brand-sub { font-size: 11px; color: #4b5e7a; font-weight: 400; letter-spacing: 0.05em; }

# .sb-section {
#     padding: 18px 22px 14px;
#     border-bottom: 1px solid #1a2235;
# }
# .sb-section-title {
#     font-size: 9px; font-weight: 600; color: #3d5273;
#     letter-spacing: 0.12em; text-transform: uppercase;
#     margin-bottom: 12px;
# }

# .lang-grid {
#     display: grid; grid-template-columns: 1fr 1fr;
#     gap: 6px;
# }
# .lang-chip {
#     background: #111827; border: 1px solid #1a2235;
#     border-radius: 8px; padding: 5px 10px;
#     font-size: 11px; color: #6b7fa0;
#     text-align: center;
#     transition: all 0.2s;
# }
# .lang-chip:hover { border-color: #4f8ef7; color: #a0b4d0; }

# .stat-row {
#     display: flex; justify-content: space-between;
#     align-items: center; padding: 7px 0;
#     border-bottom: 1px solid #111827;
#     font-size: 12px;
# }
# .stat-row:last-child { border-bottom: none; }
# .stat-label { color: #3d5273; }
# .stat-value { color: #8fa5c5; font-weight: 500; }

# .online-badge {
#     display: inline-flex; align-items: center; gap: 6px;
#     background: #0a1f12; border: 1px solid #166534;
#     border-radius: 20px; padding: 4px 10px;
#     font-size: 11px; color: #22c55e; font-weight: 500;
# }
# .pulse-dot {
#     width: 6px; height: 6px; background: #22c55e;
#     border-radius: 50%; animation: pulse 2s infinite;
#     display: inline-block;
# }
# @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.5;transform:scale(0.8)} }

# /* ── MAIN AREA ── */
# .main-wrapper {
#     display: flex; flex-direction: column;
#     height: 100vh; overflow: hidden;
# }

# .topbar {
#     background: #0c111c;
#     border-bottom: 1px solid #1a2235;
#     padding: 14px 36px;
#     display: flex; align-items: center; justify-content: space-between;
#     flex-shrink: 0;
# }
# .topbar-logo {
#     font-family: 'Syne', sans-serif;
#     font-size: 20px; font-weight: 800;
#     color: #e8edf5; letter-spacing: -0.5px;
# }
# .topbar-logo span { color: #4f8ef7; }
# .topbar-right { display: flex; align-items: center; gap: 16px; }
# .topbar-model {
#     font-size: 11px; color: #3d5273;
#     background: #111827; border: 1px solid #1a2235;
#     border-radius: 20px; padding: 4px 12px;
#     font-weight: 500;
# }

# /* ── HERO ── */
# .hero-wrap {
#     flex: 1; display: flex; flex-direction: column;
#     align-items: center; justify-content: center;
#     padding: 40px 20px;
# }
# .hero-emoji { font-size: 48px; margin-bottom: 16px; animation: float 3s ease-in-out infinite; }
# @keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }
# .hero-greeting {
#     font-size: 11px; font-weight: 600; color: #4f8ef7;
#     letter-spacing: 0.15em; text-transform: uppercase;
#     margin-bottom: 10px;
# }
# .hero-title {
#     font-family: 'Syne', sans-serif;
#     font-size: 36px; font-weight: 800;
#     color: #e8edf5; text-align: center;
#     line-height: 1.2; margin-bottom: 14px;
#     letter-spacing: -1px;
# }
# .hero-title span { color: #4f8ef7; }
# .hero-sub {
#     font-size: 14px; color: #4b5e7a;
#     text-align: center; line-height: 1.7;
#     max-width: 480px; margin-bottom: 30px;
# }
# .hero-pills {
#     display: flex; flex-wrap: wrap; gap: 8px;
#     justify-content: center; margin-bottom: 10px;
# }
# .hero-pill {
#     background: #111827; border: 1px solid #1a2235;
#     border-radius: 20px; padding: 7px 16px;
#     font-size: 12px; color: #4f8ef7;
#     cursor: pointer; transition: all 0.2s;
# }
# .hero-pill:hover { background: #1a2640; border-color: #4f8ef7; }

# /* ── CHAT ── */
# .chat-scroll {
#     flex: 1; overflow-y: auto;
#     padding: 28px 0 20px;
#     scrollbar-width: thin;
#     scrollbar-color: #1a2235 transparent;
# }
# .chat-inner { max-width: 760px; margin: 0 auto; padding: 0 24px; }

# .msg-row { display: flex; gap: 12px; margin-bottom: 22px; animation: fadeUp 0.3s ease; }
# @keyframes fadeUp { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
# .msg-row.user { flex-direction: row-reverse; }

# .avatar {
#     width: 34px; height: 34px; border-radius: 10px;
#     display: flex; align-items: center; justify-content: center;
#     font-size: 13px; font-weight: 700; flex-shrink: 0; margin-top: 2px;
# }
# .avatar.bot { background: linear-gradient(135deg, #1a2d4a, #1e3a5f); color: #4f8ef7; }
# .avatar.user { background: linear-gradient(135deg, #1a2a1a, #1f3320); color: #22c55e; }

# .bubble-col { display: flex; flex-direction: column; max-width: 72%; }
# .msg-row.user .bubble-col { align-items: flex-end; }

# .bubble {
#     padding: 12px 16px; border-radius: 14px;
#     font-size: 14px; line-height: 1.7; word-break: break-word;
# }
# .bubble.bot {
#     background: #0f1520; border: 1px solid #1a2235;
#     color: #c8d4e8; border-radius: 4px 14px 14px 14px;
# }
# .bubble.user {
#     background: linear-gradient(135deg, #1a3a5c, #1e4570);
#     border: 1px solid #1e4a7a; color: #ddeeff;
#     border-radius: 14px 4px 14px 14px;
# }

# .lang-tag {
#     display: inline-flex; align-items: center; gap: 4px;
#     font-size: 10px; color: #3d5273; margin-top: 5px;
#     padding: 2px 8px; background: #0c111c;
#     border-radius: 20px; border: 1px solid #1a2235;
# }

# /* ── TYPING ── */
# .typing-row { display: flex; gap: 12px; margin-bottom: 22px; }
# .typing-bubble {
#     padding: 14px 18px; background: #0f1520;
#     border: 1px solid #1a2235; border-radius: 4px 14px 14px 14px;
#     display: flex; gap: 5px; align-items: center;
# }
# .dot {
#     width: 7px; height: 7px; border-radius: 50%;
#     background: #4f8ef7; animation: bounce 1.3s infinite;
# }
# .dot:nth-child(2){animation-delay:.15s}
# .dot:nth-child(3){animation-delay:.3s}
# @keyframes bounce { 0%,60%,100%{transform:translateY(0);opacity:0.3} 30%{transform:translateY(-7px);opacity:1} }

# /* ── INPUT ── */
# .input-bar {
#     flex-shrink: 0;
#     background: #0c111c;
#     border-top: 1px solid #1a2235;
#     padding: 16px 24px 20px;
# }
# .input-inner { max-width: 760px; margin: 0 auto; }

# /* Override Streamlit chat input */
# [data-testid="stChatInput"] {
#     background: #111827 !important;
#     border: 1px solid #1a2235 !important;
#     border-radius: 14px !important;
# }
# [data-testid="stChatInput"] textarea {
#     background: transparent !important;
#     color: #c8d4e8 !important;
#     font-family: 'DM Sans', sans-serif !important;
#     font-size: 14px !important;
#     caret-color: #4f8ef7 !important;
# }
# [data-testid="stChatInput"]:focus-within {
#     border-color: #4f8ef7 !important;
#     box-shadow: 0 0 0 3px rgba(79,142,247,0.1) !important;
# }

# /* Override Streamlit chat messages */
# [data-testid="stChatMessage"] {
#     background: transparent !important;
#     border: none !important;
#     padding: 0 !important;
# }

# div[data-testid="stVerticalBlock"] { gap: 0 !important; }

# /* Divider line at bottom of sidebar */
# .sb-footer {
#     padding: 16px 22px;
#     font-size: 10px; color: #1e2d45;
#     text-align: center; letter-spacing: 0.08em;
# }
# </style>
# """, unsafe_allow_html=True)

# # ── Session state ──
# if "messages" not in st.session_state: st.session_state.messages = []

# # ══════════════════════════════════════════════
# # SIDEBAR
# # ══════════════════════════════════════════════
# with st.sidebar:
#     # Brand
#     st.markdown("""
#     <div class="sb-brand">
#         <div class="sb-brand-logo">Lingua<span>Bot</span></div>
#         <div class="sb-brand-sub">MULTILINGUAL AI ASSISTANT</div>
#     </div>
#     """, unsafe_allow_html=True)

#     # Status
#     st.markdown("""
#     <div class="sb-section">
#         <div class="sb-section-title">Status</div>
#         <div class="online-badge">
#             <div class="pulse-dot"></div>
#             Cloud · HuggingFace Active
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     # Languages
#     st.markdown("""
#     <div class="sb-section">
#         <div class="sb-section-title">Supported Languages</div>
#         <div class="lang-grid">
#             <div class="lang-chip">🇮🇳 Hindi</div>
#             <div class="lang-chip">🇮🇳 Tamil</div>
#             <div class="lang-chip">🇧🇩 Bengali</div>
#             <div class="lang-chip">🇮🇳 Marathi</div>
#             <div class="lang-chip">🇮🇳 Telugu</div>
#             <div class="lang-chip">🇮🇳 Kannada</div>
#             <div class="lang-chip">🇮🇳 Malayalam</div>
#             <div class="lang-chip">🇵🇰 Urdu</div>
#             <div class="lang-chip">🇬🇧 English</div>
#             <div class="lang-chip">🔀 Hinglish</div>
#             <div class="lang-chip">🔀 Tanglish</div>
#             <div class="lang-chip">🔀 Benglish</div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     # Stats
#     st.markdown(f"""
#     <div class="sb-section">
#         <div class="sb-section-title">System Info</div>
#         <div class="stat-row"><span class="stat-label">Primary Model</span><span class="stat-value">Qwen 2.5 7B</span></div>
#         <div class="stat-row"><span class="stat-label">Fallback</span><span class="stat-value">Mixtral 8x7B</span></div>
#         <div class="stat-row"><span class="stat-label">Embeddings</span><span class="stat-value">Multilingual-E5</span></div>
#         <div class="stat-row"><span class="stat-label">Reranker</span><span class="stat-value">BGE-M3</span></div>
#         <div class="stat-row"><span class="stat-label">Translation</span><span class="stat-value">NLLB-200</span></div>
#         <div class="stat-row"><span class="stat-label">Messages</span><span class="stat-value">{len(st.session_state.messages)}</span></div>
#     </div>
#     """, unsafe_allow_html=True)

#     # Clear chat button
#     st.markdown('<div class="sb-section">', unsafe_allow_html=True)
#     if st.button("🗑  Clear Chat History", use_container_width=True):
#         st.session_state.messages = []
#         st.rerun()
#     st.markdown('</div>', unsafe_allow_html=True)

#     st.markdown('<div class="sb-footer">LinguaBot · C-DAC Pune · 2025</div>', unsafe_allow_html=True)

# # ══════════════════════════════════════════════
# # TOPBAR
# # ══════════════════════════════════════════════
# st.markdown("""
# <div class="topbar">
#     <div class="topbar-logo">Lingua<span>Bot</span></div>
#     <div class="topbar-right">
#         <div class="topbar-model">⚡ Qwen 2.5 · Mixtral · Llama 3.1</div>
#         <div class="online-badge"><div class="pulse-dot"></div> Online</div>
#     </div>
# </div>
# """, unsafe_allow_html=True)

# # ══════════════════════════════════════════════
# # HERO — shown before first message
# # ══════════════════════════════════════════════
# if not st.session_state.messages:
#     st.markdown(f"""
#     <div class="hero-wrap">
#         <div class="hero-emoji">{emoji}</div>
#         <div class="hero-greeting">{greeting}</div>
#         <div class="hero-title">Welcome to <span>LinguaBot</span></div>
#         <div class="hero-sub">
#             Your multilingual AI assistant — ask anything in Hindi, Bengali,
#             Tamil, Hinglish, or any Indian language. Powered by RAG + Cloud LLMs.
#         </div>
#         <div class="hero-pills">
#             <div class="hero-pill">महिला सुरक्षा क्या है?</div>
#             <div class="hero-pill">AI kya hota hai?</div>
#             <div class="hero-pill">What is RAG?</div>
#             <div class="hero-pill">AI enna sollu?</div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

# # ══════════════════════════════════════════════
# # CHAT MESSAGES
# # ══════════════════════════════════════════════
# for msg in st.session_state.messages:
#     if msg["role"] == "user":
#         lang_code = msg.get("lang", detect_language(msg["content"]))
#         flag, lang_name = LANG_INFO.get(lang_code, ("🌐", lang_code.upper()))
#         st.markdown(f"""
#         <div class="msg-row user">
#             <div class="avatar user">U</div>
#             <div class="bubble-col">
#                 <div class="bubble user">{msg["content"]}</div>
#                 <div class="lang-tag">{flag} {lang_name}</div>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)
#     else:
#         st.markdown(f"""
#         <div class="msg-row">
#             <div class="avatar bot">AI</div>
#             <div class="bubble-col">
#                 <div class="bubble bot">{msg["content"]}</div>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

# # ══════════════════════════════════════════════
# # CHAT INPUT
# # ══════════════════════════════════════════════
# if user_input := st.chat_input("Type in any language — Hindi, Tamil, Hinglish, English..."):
#     lang_code = detect_language(user_input)
#     flag, lang_name = LANG_INFO.get(lang_code, ("🌐", "Unknown"))

#     st.session_state.messages.append({
#         "role": "user",
#         "content": user_input,
#         "lang": lang_code
#     })

#     # Show user message immediately
#     st.markdown(f"""
#     <div class="msg-row user">
#         <div class="avatar user">U</div>
#         <div class="bubble-col">
#             <div class="bubble user">{user_input}</div>
#             <div class="lang-tag">{flag} {lang_name}</div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     # Typing indicator
#     st.markdown("""
#     <div class="typing-row">
#         <div class="avatar bot">AI</div>
#         <div class="typing-bubble">
#             <div class="dot"></div><div class="dot"></div><div class="dot"></div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     # Generate response
#     with st.spinner(""):
#         history = st.session_state.messages[:-1]
#         response = chatbot(user_input, history)

#     st.session_state.messages.append({"role": "assistant", "content": response})
#     st.rerun()