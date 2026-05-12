import streamlit as st
import google.generativeai as genai
import glob
import os

# --- 1. إعداد المفتاح والأمان ---
api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
if not api_key:
    st.error("خطأ: مفتاح الـ API غير موجود في الإعدادات.")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. إعدادات الواجهة ودعم العربية (RTL) ---
st.set_page_config(page_title="APIA Smart Expert", page_icon="🌱")
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stChatMessage"], [data-testid="stChatInput"] {
        direction: RTL; text-align: right;
    }
    div[data-testid="stChatMessage"] { flex-direction: row-reverse; }
    table { margin-left: auto; margin-right: 0; width: 100%; border-collapse: collapse; }
    th, td { text-align: right !important; padding: 8px; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 مساعد APIA الذكي")

# --- 3. تعليمات النظام الصارمة ---
SYSTEM_PROMPT = """أنت "المساعد الرقمي الرسمي لوكالة APIA".
قوانينك:
1. الجداول: أي أرقام أو مقارنات يجب صياغتها في جدول Markdown.
2. الدقة: أجب من الملفات المرفقة فقط.
3. الاستمرارية: تذكر سياق الحوار السابق دائماً.
"""

# --- 4. رفع ومعالجة الملفات (تتم مرة واحدة فقط) ---
@st.cache_resource
def prepare_files():
    pdf_files = glob.glob("*.pdf")
    uploaded_docs = []
    for f in pdf_files:
        try:
            with st.spinner(f"جاري قراءة المرجع: {f}..."):
                # رفع الملف لمنصة جوجل للحصول على تحليل سريع
                doc = genai.upload_file(f)
                uploaded_docs.append(doc)
        except: pass
    return uploaded_docs

knowledge_base = prepare_files()

# --- 5. إدارة الذاكرة والجلسة ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# تهيئة الموديل مع تعليمات النظام
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", # الفلاش هو الأسرع في الاستجابة اللحظية
    system_instruction=SYSTEM_PROMPT
)

# بدء الجلسة إذا لم تكن موجودة
if "chat" not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])

# عرض المحادثات السابقة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. التنفيذ بنظام التدفق الحقيقي (Real-time Streaming) ---
if prompt := st.chat_input("اسألني عن وثائق APIA..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # إرسال الملفات في أول رسالة فقط لزيادة السرعة في الرسائل اللاحقة
        is_first = len(st.session_state.messages) <= 1
        content = [prompt] + knowledge_base if is_first else prompt
        
        # مكان ظهور النص المتدفق
        placeholder = st.empty()
        full_res = ""
        
        try:
            # استخدام stream=True لضمان التدفق الحقيقي
            response = st.session_state.chat.send_message(content, stream=True)
            
            for chunk in response:
                full_res += chunk.text
                # تحديث فوري للنص لكسر أي Buffering
                placeholder.markdown(full_res + "▌")
            
            placeholder.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            
        except Exception as e:
            st.error(f"حدث خطأ: {e}")
