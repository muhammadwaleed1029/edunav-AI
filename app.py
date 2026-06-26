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

st.set_page_config(page_title="EduNav AI", page_icon="🎓", layout="centered")

def _safe_latin(text):
    return text.encode("latin-1", errors="replace").decode("latin-1")

class _EduNavPDF(FPDF):
    def header(self):
        self.set_font("Helvetica","B",15); self.set_text_color(108,99,255)
        self.cell(0,10,"EduNav AI - Career Conversation",new_x=XPos.LMARGIN,new_y=YPos.NEXT,align="C")
        self.set_font("Helvetica","",9); self.set_text_color(120,120,160)
        self.cell(0,6,f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",new_x=XPos.LMARGIN,new_y=YPos.NEXT,align="C")
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
            pdf.set_fill_color(67,200,120); pdf.set_text_color(255,255,255); label="  EduNav AI Roadmap"
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
    st.markdown("Your intelligent career guide.")
    st.markdown("---")
    n_msgs = len(st.session_state.messages)
    n_user = sum(1 for m in st.session_state.messages if m["role"]=="user")
    status = "🟢 Connected" if st.session_state.get("client") else "🔴 Error"
    st.markdown(f"💬 {n_msgs} messages | {status}")
    st.markdown("---")
    st.markdown("**💡 Quick Start**")
    for label, prompt_text in [
        ("🗺️ Data Science Roadmap", "Give me a complete roadmap to become a Data Scientist from scratch"),
        ("💻 Full-Stack Web Dev", "Give me a study path for full-stack web development"),
        ("🔐 Cybersecurity Guide", "Give me a roadmap to start a career in cybersecurity"),
        ("🤖 AI/ML Learning Path", "Give me a roadmap to learn Artificial Intelligence and Machine Learning"),
        ("📱 Mobile App Dev", "Give me a roadmap to become a mobile app developer"),
        ("☁️ Cloud & DevOps", "Give me a career roadmap for Cloud Computing and DevOps"),
    ]:
        if st.button(label, use_container_width=True, key=f"sug_{label}"):
            st.session_state.inject_prompt = prompt_text
            st.rerun()
    st.markdown("---")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.inject_prompt = None
        st.rerun()

st.title("EduNav AI 🎓")
st.caption("Your intelligent career guide — roadmaps, skills & advice, instantly.")

if st.session_state.get("auth_error"):
    st.error(f"Connection failed: {st.session_state.auth_error}")

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
    st.success("📄 Your roadmap is ready!")
    st.download_button("⬇️ Download PDF Roadmap", data=pdf_bytes,
        file_name=f"EduNav_Roadmap_{datetime.date.today()}.pdf",
        mime="application/pdf", use_container_width=True)

_maybe_show_pdf_button()

prompt = st.chat_input("Ask me anything — career advice, skills, roadmaps…")
if st.session_state.inject_prompt:
    prompt = st.session_state.inject_prompt
    st.session_state.inject_prompt = None

if prompt:
    if st.session_state.client is None:
        st.error("Cannot connect — check GROQ_API_KEY.")
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
