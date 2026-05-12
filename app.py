import streamlit as st
from google import genai
from google.genai import types
import glob
import os

# --- 1. إعداد المفتاح (Secrets) ---
try:
    # سيجرب الكود البحث عن أي مسمى وضعته في الإعدادات
    api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error("تنبيه: تأكد من وضع API Key في إعدادات Secrets على Streamlit Cloud.")
    st.stop()

# --- 2. إعدادات الصفحة و RTL ---
st.set_page_config(page_title="APIA Expert Pro", page_icon="🌱")
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stChatMessage"], [data-testid="stChatInput"] {
        direction: RTL; text-align: right;
    }
    div[data-testid="stChatMessage"] { flex-direction: row-reverse; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 مساعد APIA الذكي")

# --- 3. التعليمات ---
SYSTEM_PROMPT = "أنت مساعد خبير لوكالة APIA. أجب بدقة من الملفات المرفقة فقط."

# --- 4. رفع الملفات تلقائياً ---
@st.cache_resource
def load_all_pdfs():
    pdf_files = glob.glob("*.pdf")
    uploaded_refs = []
    if not pdf_files:
        return []
    for pdf in pdf_files:
        try:
            with st.spinner(f"جاري معالجة المرجع: {pdf}..."):
                u_file = client.files.upload(file=pdf)
                uploaded_refs.append(u_file)
        except Exception:
            pass 
    return uploaded_refs

all_files = load_all_pdfs()

# --- 5. منطق الدردشة بنظام الـ Streaming ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# عرض التاريخ
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# إدخال المستخدم
# --- 5. منطق الدردشة مع الذاكرة (Chat Session) ---
if "chat_session" not in st.session_state:
    # نبدأ جلسة جديدة ونرسل الملفات كـ "سياق أساسي" لمرة واحدة
    st.session_state.chat_session = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.0
        )
    )

# عرض الرسائل السابقة من ذاكرة الجلسة
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("اسأل عن وثائق وكالة APIA..."):
    # عرض سؤال المستخدم
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            # إرسال السؤال مع الملفات في أول مرة فقط، ثم السؤال وحده لاحقاً
            # الموديل سيتذكر الملفات والأسئلة السابقة تلقائياً
            input_content = all_files + [prompt] if not st.session_state.messages[:-1] else prompt
            
            responses = st.session_state.chat_session.send_message_stream(
                msg=input_content
            )
            
            for chunk in responses:
                full_response += chunk.text
                placeholder.markdown(full_response + "▌")
            
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"حدث خطأ: {e}")
