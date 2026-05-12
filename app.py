import streamlit as st
from google import genai
from google.genai import types
import glob
import os

# --- 1. جلب المفتاح بأمان ---
try:
    # سيقرأ أي اسم وضعته في Secrets (سواء GEMINI_API_KEY أو غيره)
    # لكن يفضل توحيده في Secrets باسم GEMINI_API_KEY
    api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error("مشكلة في مفتاح الـ API. تأكد من وضعه في Secrets.")
    st.stop()

# --- 2. واجهة التطبيق ---
st.set_page_config(page_title="APIA Expert", page_icon="🌱")
st.markdown("<style>*{direction: RTL; text-align: right;}</style>", unsafe_allow_html=True)
st.title("🤖 مساعد APIA الذكي")

# --- 3. التعليمات ---
SYSTEM_PROMPT = "أنت مساعد خبير لوكالة APIA. أجب بدقة من الملفات المرفقة فقط."

# --- 4. رفع "كل" ملفات الـ PDF تلقائياً ---
@st.cache_resource
def load_all_pdfs():
    # يبحث عن أي ملف ينتهي بـ .pdf في المجلد الحالي
    pdf_files = glob.glob("*.pdf")
    uploaded_refs = []
    
    if not pdf_files:
        st.warning("لم يتم العثور على أي ملفات PDF في GitHub.")
        return []

    for pdf in pdf_files:
        try:
            with st.spinner(f"جاري قراءة: {pdf}..."):
                u_file = client.files.upload(file=pdf)
                uploaded_refs.append(u_file)
        except Exception as e:
            st.error(f"فشل رفع {pdf}: {e}")
    return uploaded_refs

# تنفيذ الرفع
all_files = load_all_pdfs()

# --- 5. الدردشة ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("اسأل عن استثمارات وكالة APIA..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # نرسل كل الملفات التي وجدناها مع السؤال
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=all_files + [prompt],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.0
                )
            )
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"حدث خطأ: {e}")
