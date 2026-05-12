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
    st.error("خطأ في المفتاح.")
    st.stop()

# --- 2. واجهة التطبيق ---
st.set_page_config(page_title="APIA Expert", page_icon="🌱")
st.markdown("<style>*{direction: RTL; text-align: right;}</style>", unsafe_allow_html=True)
st.title("🤖 مساعد APIA الذكي")

# --- 3. رفع الملفات لمرة واحدة (السرعة) ---
@st.cache_resource
def load_docs():
    pdfs = glob.glob("*.pdf")
    return [client.files.upload(file=f) for f in pdfs] if pdfs else []

all_files = load_docs()

# --- 4. الذاكرة (Chat Session) ---
if "chat_session" not in st.session_state:
    st.session_state.chat_session = client.chats.create(
        model="gemini-2.5-flash", 
        config=types.GenerateContentConfig(
            system_instruction="أنت مساعد APIA الرسمي. تذكر سياق الحوار بدقة.",
            temperature=0.0
        )
    )
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. التنفيذ (Streaming + الذاكرة) ---
if prompt := st.chat_input("اسأل عن وثائق APIA..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        
        # تصحيح الخطأ: نرسل الملفات في أول مرة فقط
        is_first_msg = len(st.session_state.messages) <= 1
        content_to_send = all_files + [prompt] if is_first_msg else prompt
        
        try:
            # تم استبدال msg بـ message لحل خطأ الصورة الأخيرة
            responses = st.session_state.chat_session.send_message_stream(
                message=content_to_send 
            )
            
            for chunk in responses:
                full_res += chunk.text
                placeholder.markdown(full_res + "▌")
            
            placeholder.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
        except Exception as e:
            st.error(f"عذراً، حدث خطأ: {e}")
