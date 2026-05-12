import streamlit as st
from google import genai
from google.genai import types
import glob
import os

# --- 1. إعدادات الأمان والمفتاح ---
try:
    # يحاول الكود جلب المفتاح بأي مسمى وضعته في الـ Secrets
    api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("خطأ: لم يتم العثور على المفتاح. تأكد من إضافته في إعدادات Streamlit Secrets.")
    st.stop()

# --- 2. إعدادات الواجهة ودعم اللغة العربية (RTL) ---
st.set_page_config(page_title="APIA Smart Expert", page_icon="🌱", layout="centered")
st.markdown("""
    <style>
    /* تنسيق اتجاه النص والجداول لليمين */
    [data-testid="stAppViewContainer"], [data-testid="stChatMessage"], [data-testid="stChatInput"] {
        direction: RTL; text-align: right;
    }
    div[data-testid="stChatMessage"] { flex-direction: row-reverse; }
    table { margin-left: auto; margin-right: 0; }
    th, td { text-align: right !important; padding: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 مساعد APIA الذكي (نسخة الاحتراف)")

# --- 3. تعليمات النظام (لضمان الجداول والدقة) ---
SYSTEM_PROMPT = """أنت "المساعد الرقمي الرسمي لوكالة APIA".
مهمتك: الإجابة بدقة من الملفات المرفقة فقط.
القوانين الصارمة:
1. الجداول: أي مقارنة أو أرقام يجب وضعها في جدول Markdown منظم.
2. الذاكرة: تذكر سياق المحادثة كاملاً وأجب بناءً على الأسئلة السابقة.
3. المصدر: إذا لم تجد المعلومة في الملفات، قل بوضوح أنها غير متوفرة ووجه المستخدم لـ kouki.riadh@apia.com.tn.
4. التنسيق: استخدم الخط العريض للعناوين والنقاط لتسهيل القراءة.
"""

# --- 4. معالجة الملفات لمرة واحدة (السرعة) ---
@st.cache_resource
def prepare_knowledge_base():
    # البحث عن جميع ملفات PDF في المجلد
    pdf_files = glob.glob("*.pdf")
    if not pdf_files:
        return []
    
    uploaded_files = []
    for f_path in pdf_files:
        try:
            with st.spinner(f"جاري تحليل المرجع: {f_path}..."):
                # رفع الملف لمنصة جوجل
                u_file = client.files.upload(file=f_path)
                uploaded_files.append(u_file)
        except Exception as e:
            st.error(f"فشل في معالجة {f_path}: {e}")
    return uploaded_files

# تنفيذ الرفع التلقائي
knowledge_base = prepare_knowledge_base()

# --- 5. إدارة جلسة المحادثة (الذاكرة) ---
if "chat_session" not in st.session_state:
    # إنشاء جلسة دردشة مستمرة لا تنسى
    st.session_state.chat_session = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.0 # دقة وحرفية عالية
        )
    )
if "messages" not in st.session_state:
    st.session_state.messages = []

# عرض تاريخ المحادثة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. منطق الاستجابة (Streaming + Memory) ---
if prompt := st.chat_input("اسألني عن أي تفصيل في وثائق APIA..."):
    # إضافة سؤال المستخدم
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            # في أول رسالة فقط، نرسل الملفات كـ "سياق". في الرسائل التالية، الموديل يتذكرها تلقائياً.
            is_first_interaction = len(st.session_state.messages) <= 1
            input_data = knowledge_base + [prompt] if is_first_interaction else prompt
            
            # تنفيذ الطلب بنظام التدفق (Streaming)
            responses = st.session_state.chat_session.send_message_stream(
                message=input_data
            )
            
            for chunk in responses:
                full_response += chunk.text
                # تحديث النص كلمة بكلمة مع مؤشر كتابة
                placeholder.markdown(full_response + "▌")
            
            # عرض النص النهائي (بدون المؤشر) لضمان ظهور الجداول بشكل سليم
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"عذراً، حدث خطأ تقني: {e}")
