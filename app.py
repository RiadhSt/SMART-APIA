import streamlit as st
import google.generativeai as genai
import glob
import os

# --- 1. إعدادات الأمان ---
api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
if not api_key:
    st.error("المفتاح غير موجود.")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. إعدادات الواجهة ---
st.set_page_config(page_title="APIA Smart Expert", page_icon="🌱")
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stChatMessage"], [data-testid="stChatInput"] {
        direction: RTL; text-align: right;
    }
    div[data-testid="stChatMessage"] { flex-direction: row-reverse; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 مساعد APIA الذكي")

# --- 3. رفع الملفات لمرة واحدة (السرعة القصوى) ---
@st.cache_resource
def load_docs():
    pdf_files = glob.glob("*.pdf")
    uploaded = []
    for f in pdf_files:
        try:
            with st.spinner(f"جاري تحليل: {f}..."):
                # نرفع الملف وننتظر حتى يصبح جاهزاً (Active)
                u = genai.upload_file(f)
                uploaded.append(u)
        except: pass
    return uploaded

docs = load_docs()

# --- 4. إعداد الموديل والذاكرة ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# استخدام 1.5-flash لأنه الأسرع عالمياً في الـ Streaming حالياً
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction="أنت خبير وكالة APIA. أجب من الملفات وتذكر سياق الحوار. استخدم الجداول للأرقام."
)

# بدء الجلسة مع التاريخ السابق
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# عرض التاريخ
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. التنفيذ (التدفق الحقيقي) ---
if prompt := st.chat_input("اسألني عن وثائق APIA..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # إرسال الملفات فقط في أول مرة، ثم النص فقط
        content = [prompt] + docs if len(st.session_state.messages) <= 1 else prompt
        
        # استخدام stream=True لضمان التدفق اللحظي
        response_stream = st.session_state.chat.send_message(content, stream=True)
        
        # ميزة st.write_stream ستجعل الكلمات تظهر فور ولادتها
        full_response = st.write_stream(chunk.text for chunk in response_stream)
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})
