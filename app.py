import streamlit as st
from google import genai
from google.genai import types
import glob
import os

# --- 1. الإعدادات ---
try:
    api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("تأكد من وجود API Key في Secrets.")
    st.stop()

# --- 2. واجهة التطبيق ---
st.set_page_config(page_title="APIA Expert Pro", page_icon="🌱")
st.markdown("<style>*{direction: RTL; text-align: right;}</style>", unsafe_allow_html=True)
st.title("🤖 مساعد APIA الذكي")

# --- 3. رفع الملفات مرة واحدة (السرعة) ---
@st.cache_resource
def load_docs_once():
    pdfs = glob.glob("*.pdf")
    return [client.files.upload(file=f) for f in pdfs] if pdfs else []

all_files = load_docs_once()

# --- 4. إدارة الجلسة (الذاكرة القوية) ---
# هذا الجزء هو المسؤول عن عدم نسيان الأسئلة السابقة
if "chat_session" not in st.session_state:
    st.session_state.chat_session = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction="أنت خبير وكالة APIA. أجب من الملفات وتذكر كل ما قاله المستخدم سابقاً.",
            temperature=0.0
        )
    )
if "history" not in st.session_state:
    st.session_state.history = []

# عرض المحادثة السابقة
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. التنفيذ الذكي ---
if prompt := st.chat_input("اسألني عن أي تفصيل..."):
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        
        try:
            # نرسل الملفات في أول رسالة فقط، الموديل سيحفظها في الجلسة (Session)
            content = all_files + [prompt] if len(st.session_state.history) <= 1 else prompt
            
            # استخدام message بدلاً من msg لتجنب الخطأ السابق
            responses = st.session_state.chat_session.send_message_stream(message=content)
            
            for chunk in responses:
                full_res += chunk.text
                placeholder.markdown(full_res + "▌")
            
            placeholder.markdown(full_res)
            st.session_state.history.append({"role": "assistant", "content": full_res})
        except Exception as e:
            st.error(f"حدث خطأ: {e}")
