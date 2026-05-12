import streamlit as st
from google import genai
from google.genai import types
import glob
import os

# --- 1. إعدادات الأمان ---
try:
    api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("تأكد من وجود API Key في Secrets.")
    st.stop()

# --- 2. إعدادات الواجهة ودعم RTL ---
st.set_page_config(page_title="APIA Smart Expert", page_icon="🌱", layout="centered")
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stChatMessage"], [data-testid="stChatInput"] {
        direction: RTL; text-align: right;
    }
    div[data-testid="stChatMessage"] { flex-direction: row-reverse; }
    table { margin-left: auto; margin-right: 0; }
    th, td { text-align: right !important; padding: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 مساعد APIA الذكي")

# --- 3. تعليمات النظام ---
SYSTEM_PROMPT = """أنت خبير وكالة APIA. 
أجب بدقة من الملفات. استخدم جداول Markdown للمقارنات والأرقام. 
تذكر سياق الحوار كاملاً."""

# --- 4. رفع الملفات لمرة واحدة (السرعة) ---
@st.cache_resource
def prepare_knowledge_base():
    pdf_files = glob.glob("*.pdf")
    if not pdf_files: return []
    uploaded = []
    for f in pdf_files:
        try:
            with st.spinner(f"جاري تحليل: {f}..."):
                u = client.files.upload(file=f)
                uploaded.append(u)
        except: pass
    return uploaded

knowledge_base = prepare_knowledge_base()

# --- 5. إدارة الجلسة (الذاكرة) ---
if "chat_session" not in st.session_state:
    st.session_state.chat_session = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.0
        )
    )
if "messages" not in st.session_state:
    st.session_state.messages = []

# عرض التاريخ
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. منطق الاستجابة المحسن (Fast Streaming) ---
if prompt := st.chat_input("اسألني عن وثائق APIA..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # دالة "مولد" لكسر الـ Buffering وضمان الانسياب اللحظي
        def stream_generator():
            is_first = len(st.session_state.messages) <= 1
            input_data = knowledge_base + [prompt] if is_first else prompt
            
            responses = st.session_state.chat_session.send_message_stream(
                message=input_data
            )
            for chunk in responses:
                yield chunk.text

        # استخدام st.write_stream لعرض النص بطريقة Chat-like سلسة جداً
        full_response = st.write_stream(stream_generator())
        
        # حفظ الإجابة النهائية في الذاكرة
        st.session_state.messages.append({"role": "assistant", "content": full_response})
