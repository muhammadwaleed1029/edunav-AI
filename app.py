import streamlit as st
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import datetime
from ai_service import build_client, stream_response

GROQ_API_KEY = "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"
MODEL_NAME   = "llama-3.3-70b-versatile"
ROADMAP_TRIGGER = (
    "💡 If you like this roadmap, you can instantly download this entire "
    "conversation as a beautifully formatted PDF using the button below!"
)

st.set_page_config(page_title="EduNav AI — Career Chatbot", page_icon="🎓",
                   layout="centered", initial_sidebar_state="expanded")

# ═══════════════════════════════════════════════════════════
# CSS START — Pure styling only, no application logic here
# ═══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
:root { --primary:#6C63FF; --secondary:#FF6584; --accent:#43E97B; --text:#E0E0F0; --muted:#8888AA; --radius:14px; }
html, body, [class*="css"] { font-family:'Inter',sans-serif !important; color:var(--text); }
.stApp { background:linear-gradient(135deg,#0f0c29 0%,#302b63 50%,#24243e 100%) !important; min-height:100vh; }
.stApp > header, .stApp [data-testid="stAppViewContainer"], .stApp [data-testid="stHeader"] { background:transparent !important; }
footer { display:none !important; }
#MainMenu { visibility:hidden !important; }
[data-testid="stToolbar"], [data-testid="stDecoration"] { display:none !important; }
[data-testid="stSidebar"] { background:rgba(20,18,40,0.97) !important; border-right:1px solid rgba(108,99,255,0.25); }
[data-testid="stSidebar"] * { color:var(--text) !important; }
.block-container { max-width:780px !important; padding-top:2rem !important; padding-bottom:5rem !important; background:transparent !important; }
.edunav-header { background:linear-gradient(90deg,#6C63FF 0%,#FF6584 55%,#43E97B 100%); background-clip:text; -webkit-background-clip:text; -webkit-text-fill-color:transparent; font-size:2.6rem; font-weight:700; letter-spacing:-0.5px; line-height:1.2; margin-top:0.5rem; margin-bottom:0.2rem; display:block; }
.edunav-tagline { color:var(--muted); font-size:0.9rem; margin-bottom:1.2rem; display:block; }
[data-testid="stChatMessage"] { border-radius:var(--radius); padding:0.6rem 0.8rem; margin-bottom:0.5rem; border:1px solid rgba(255,255,255,0.06); animation:fadeUp 0.3s ease; }
@keyframes fadeUp { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { background:rgba(108,99,255,0.12) !important; border-color:rgba(108,99,255,0.30) !important; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) { background:rgba(255,255,255,0.04) !important; border-color:rgba(67,233,123,0.18) !important; }
[data-testid="stChatInput"] textarea { background:rgba(42,42,62,0.85) !important; border:1.5px solid rgba(108,99,255,0.45) !important; border-radius:12px !important; color:var(--text) !important; font-family:'Inter',sans-serif !important; font-size:0.95rem !important; padding:0.75rem 1rem !important; }
[data-testid="stChatInput"] textarea:focus { border-color:var(--primary) !important; box-shadow:0 0 0 3px rgba(108,99,255,0.18) !important; }
[data-testid="stChatInput"] button { background:linear-gradient(135deg,#6C63FF,#FF6584) !important; border:none !important; border-radius:8px !important; }
[data-testid="stChatInput"] button:hover { opacity:0.88 !important; transform:scale(1.05) !important; }
.pdf-section { background:linear-gradient(135deg,rgba(108,99,255,0.18) 0%,rgba(67,233,123,0.12) 100%); border:1.5px solid rgba(67,233,123,0.40); border-radius:var(--radius); padding:1rem 1.2rem; margin:0.8rem 0; display:flex; align-items:center; gap:0.8rem; }
.stDownloadButton > button { background:linear-gradient(90deg,#43E97B 0%,#38f9d7 100%) !important; color:#0f0c29 !important; font-weight:600 !important; border-radius:8px !important; border:none !important; padding:0.5rem 1.2rem !important; }
.stDownloadButton > button:hover { transform:translateY(-1px) !important; opacity:0.90 !important; }
.error-box { background:rgba(255,101,132,0.12); border-left:4px solid #FF6584; border-radius:8px; padding:0.8rem 1rem; margin:0.6rem 0; font-size:0.9rem; color:#FFB3C6; }
.stat-pill { display:inline-block; background:rgba(108,99,255,0.20); border:1px solid rgba(108,99,255,0.35); border-radius:20px; padding:0.2rem 0.75rem; font-size:0.78rem; color:#b8b4ff; margin:0.15rem 0.1rem; }
hr { border-color:rgba(255,255,255,0.08) !important; }
::-webkit-scrollbar { width:5px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:rgba(108,99,255,0.40); border-radius:10px; }
</style>
""", unsafe_allow_html=True)
# ═══════════════════════════════════════════════════════════
# CSS END — Application logic starts below
# ═══════════════════════════════════════════════════════════

def _safe_latin(text):
    return text.encode("latin-1", errors="replace").decode("latin-1")

class _EduNavPDF(FPDF):
    def header(self):
        self.set_font("Helvetica","B",15); self.set_text_color(108,99,255)
        self.cell(0,10,"EduNav AI - Career Conversation",new_x=XPos.LMARGIN,new_y=YPos.NEXT,align="C")
        self.set_font("Helvetica","",9); self.set_text_color(120,120,160)
        self.cell(0,6,f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d  %H:%M')}",new_x=XPos.LMARGIN,new_y=YPos.NEXT,align="C")
        self.set_draw_color(108,99,255); self.line(10,self.get_y()+1,200,self.get_y()+1); self.ln(5)
    def footer(self):
        self.set_y(-15); self.set_font("Helvetica","I",8); self.set_text_color(150,150,180)
        self.cell(0,10,f"Page {self.page_no()} | EduNav AI",align="C")

def build_pdf(messages):
    pdf = _EduNavPDF(); pdf.set_auto_page_break(auto=True,margin=18); pdf.add_page()
    trigger_safe = _safe_latin(ROADMAP_TRIGGER)
    last_ai_idx = None
    for i in reversed(range(len(messages))):
        if messages[i]["role"]=="assistant" and ROADMAP_TRIGGER in messages[i]["content"]:
            last_ai_idx = i; break
    if last_ai_idx is None:
        return bytes(pdf.output())
    roadmap_msgs = []
    if last_ai_idx > 0 and messages[last_ai_idx-1]["role"]=="user":
        roadmap_msgs.append(messages[last_ai_idx-1])
    roadmap_msgs.append(messages[last_ai_idx])
    for msg in roadmap_msgs:
        role, content = msg["role"], msg["content"]
        if role=="user":
            pdf.set_fill_color(108,99,255); pdf.set_text_color(255,255,255); label="  Your Request"
        else:
            pdf.set_fill_color(67,200,120); pdf.set_text_color(255,255,255); label="  EduNav AI — Career Roadmap"
        pdf.set_font("Helvetica","B",10)
        pdf.cell(0,8,_safe_latin(label),new_x=XPos.LMARGIN,new_y=YPos.NEXT,fill=True)
        pdf.set_text_color(30,30,50); pdf.set_fill_color(245,245,252); pdf.set_font("Helvetica","",10)
        pdf.multi_cell(0,6,_safe_latin(content).replace(trigger_safe,"").strip(),fill=True); pdf.ln(4)
    return bytes(pdf.output())

def _init_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "client" not in st.session_state:
        try:
            st.session_state.client = build_client(GROQ_API_KEY)
            st.session_state.auth_error = None
        except Exception as exc:
            st.session_state.client = None
            st.session_state.auth_error = str(exc)
    if "inject_prompt" not in st.session_state:
        st.session_state.inject_prompt = None

_init_state()

with st.sidebar:
    st.markdown("## 🎓 EduNav AI")
    st.markdown("<span style='color:#8888AA;font-size:0.85rem'>Your intelligent career guide.</span>", unsafe_allow_html=True)
    st.markdown("---")
    n_msgs = len(st.session_state.messages)
    n_user = sum(1 for m in st.session_state.messages if m["role"]=="user")
    status = "🟢 Connected" if st.session_state.get("client") else "🔴 Error"
    st.markdown(
        f'<span class="stat-pill">💬 {n_msgs} msgs</span>'
        f'<span class="stat-pill">🧑 {n_user}</span>'
        f'<span class="stat-pill">🤖 {n_msgs-n_user}</span>'
        f'<span class="stat-pill">{status}</span>',
        unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<span style='font-size:0.8rem;color:#8888AA;font-weight:600;letter-spacing:0.05em;text-transform:uppercase'>💡 Quick Start</span>", unsafe_allow_html=True)
    for label, prompt_text in [
        ("🗺️ Data Science Roadmap",      "Give me a complete roadmap to become a Data Scientist from scratch"),
        ("💻 Full-Stack Web Dev Path",    "Give me a study path for full-stack web development"),
        ("🔐 Cybersecurity Career Guide", "Give me a roadmap to start a career in cybersecurity"),
        ("🤖 AI/ML Learning Path",        "Give me a roadmap to learn Artificial Intelligence and Machine Learning"),
        ("📱 Mobile App Dev Roadmap",     "Give me a roadmap to become a mobile app developer"),
        ("☁️ Cloud & DevOps Guide",       "Give me a career roadmap for Cloud Computing and DevOps"),
    ]:
        if st.button(label, use_container_width=True, key=f"sug_{label}"):
            st.session_state.inject_prompt = prompt_text
            st.rerun()
    st.markdown("---")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.inject_prompt = None
        st.rerun()

st.markdown(
    '<span class="edunav-header">EduNav AI 🎓</span>'
    '<span class="edunav-tagline">Your intelligent career guide — roadmaps, skills &amp; advice, instantly.</span>',
    unsafe_allow_html=True)

if st.session_state.get("auth_error"):
    st.markdown(f'<div class="error-box">⚠️ <b>Connection failed:</b> {st.session_state.auth_error}</div>', unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"]=="user" else "🤖"):
        st.markdown(msg["content"])

def _last_assistant_content():
    for msg in reversed(st.session_state.messages):
        if msg["role"]=="assistant":
            return msg["content"]
    return ""

def _maybe_show_pdf_button():
    if ROADMAP_TRIGGER not in _last_assistant_content():
        return
    pdf_bytes = build_pdf(st.session_state.messages)
    st.markdown(
        '<div class="pdf-section"><span style="font-size:1.5rem">📄</span>'
        '<span style="flex:1"><b style="color:#43E97B">Your roadmap is ready!</b><br>'
        '<span style="font-size:0.82rem;color:#8888AA">Download as a formatted PDF.</span>'
        '</span></div>', unsafe_allow_html=True)
    st.download_button("⬇️  Download PDF Roadmap", data=pdf_bytes,
        file_name=f"EduNav_Roadmap_{datetime.date.today()}.pdf",
        mime="application/pdf", use_container_width=True)

_maybe_show_pdf_button()

prompt = st.chat_input("Ask me anything — career advice, skills, roadmaps…")
if st.session_state.inject_prompt:
    prompt = st.session_state.inject_prompt
    st.session_state.inject_prompt = None

if prompt:
    if st.session_state.client is None:
        st.markdown('<div class="error-box">❌ Cannot connect — check <code>GROQ_API_KEY</code>.</div>', unsafe_allow_html=True)
        st.stop()
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(prompt)
    with st.chat_message("assistant", avatar="🤖"):
        full_reply = st.write_stream(stream_response(
            client=st.session_state.client, model_name=MODEL_NAME,
            history=st.session_state.messages[:-1], user_message=prompt))
    st.session_state.messages.append({"role":"assistant","content":full_reply})
    st.rerun()
