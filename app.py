import streamlit as st
from google import genai
from google.genai import types
import glob
import os

# --- 1. الإعدادات (تأكد من وجود المفتاح في Secrets) ---
try:
    api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error("خطأ في المفتاح: تأكد من إضافته في إعدادات Streamlit Secrets.")
    st.stop()

# --- 2. إعدادات الواجهة (RTL) ---
st.set_page_config(page_title="APIA Smart Assistant", page_icon="🌱")
st.markdown("<style>*{direction: RTL; text-align: right;}</style>", unsafe_allow_html=True)
st.title("🤖 مساعد APIA الذكي")

# --- 3. رفع الملفات لمرة واحدة فقط (لزيادة السرعة) ---
@st.cache_resource
def prepare_files():
    pdf_files = glob.glob("*.pdf")
    if not pdf_files:
        return []
    uploaded = []
    for f in pdf_files:
        try:
            with st.spinner(f"جاري معالجة: {f}..."):
                u = client.files.upload(file=f)
                uploaded.append(u)
        except: pass
    return uploaded

all_files = prepare_files()

# --- 4. إدارة الذاكرة (Chat Session) لعدم النسيان ---
if "chat" not in st.session_state:
    # إنشاء الجلسة لمرة واحدة عند فتح التطبيق
    # استخدمنا gemini-2.5-flash كما ظهر في قائمتك
    st.session_state.chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction="أنت مساعد APIA. استخدم الملفات المرفقة كمرجع أساسي وأجب بدقة.",
            temperature=0.0
        )
    )
    st.session_state.history = []

# عرض المحادثة السابقة
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. تنفيذ الإجابة بنظام Streaming (التدفق) ---
if prompt := st.chat_input("اسأل عن أي تفصيل في وثائق APIA..."):
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        
        try:
            # في أول رسالة فقط نرسل الملفات، بعدها يرسل الموديل النص فقط لأنه يتذكرها
            content = all_files + [prompt] if len(st.session_state.history) <= 1 else prompt
            
            # إرسال الرسالة بنظام التدفق
            stream = st.session_state.chat.send_message_stream(msg=content)
            
            for chunk in stream:
                full_res += chunk.text
                placeholder.markdown(full_res + "▌")
            
            placeholder.markdown(full_res)
            st.session_state.history.append({"role": "assistant", "content": full_res})
            
        except Exception as e:
            st.error(f"عذراً، حدث خطأ: {e}")
