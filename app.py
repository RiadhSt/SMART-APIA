import streamlit as st
from google import genai
from google.genai import types
import os

# --- 1. الإعدادات والربط ---
ST_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=ST_API_KEY)

# --- 2. إعدادات الصفحة و RTL ---
st.set_page_config(page_title="APIA Expert AI", page_icon="🌱")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stChatMessage"], [data-testid="stChatInput"] {
        direction: RTL;
        text-align: right;
    }
    div[data-testid="stChatMessage"] { flex-direction: row-reverse; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 خبير وكالة APIA الذكي (دقة الاستوديو)")

# --- 3. التعليمات الصارمة ونطاق العمل ---
SYSTEM_INSTRUCTIONS = """أنت "المساعد الرقمي الذكي لوكالة النهوض بالاستثمارات الفلاحية بتونس". 
مهمتك: تقديم إرشادات دقيقة بناءً على المستندات المرفقة فقط.

[قواعد الدقة المطلقة]
1. الأولوية القصوى: الإجابة من الملفات المرفقة (الملف المرتبط بهذه الجلسة).
2. درجة الحرارة (Temperature): أنت مبرمج على دقة 0.0، أي لا تخرج عن النص نهائياً.
3. في حال غياب المعلومة: قل "يرجى مراجعة مصالح الوكالة بخصوص هذا التفصيل" ولا تخمن أبداً.
4. التنسيق: استخدم الجداول للمقارنات والنسب المئوية.
5. التواصل: المشرف هو kouki.riadh@apia.com.tn.
"""

# --- 4. وظيفة رفع الملفات برمجياً (لضمان الدقة) ---
# ملاحظة: يجب وضع ملفاتك (مثل الـ 82 سلايد) في مجلد المشروع ورفعها هنا
@st.cache_resource
def load_and_upload_files():
    """هذه الوظيفة ترفع ملفاتك إلى سحابة جوجل لكي يراها الموديل مثل الاستوديو تماماً"""
    # استبدل 'your_file.pdf' باسم ملفك الحقيقي الموجود في مجلد التطبيق
    # يمكنك رفع عدة ملفات وتخزينها في قائمة
    files_to_upload = ["presentation_82_slides.pdf"] 
    uploaded_files_uris = []
    
    for file_path in files_to_upload:
        if os.path.exists(file_path):
            uploaded_file = client.files.upload(path=file_path)
            uploaded_files_uris.append(uploaded_file)
    return uploaded_files_uris

# محاولة رفع الملفات (تأكد من وجود الملف في نفس المجلد)
try:
    context_files = load_and_upload_files()
except Exception as e:
    st.warning("لم يتم العثور على ملفات مرجعية، سيتم الاعتماد على البحث فقط.")
    context_files = []

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. معالجة الطلبات بالدقة القصوى ---
if prompt := st.chat_input("كيف يمكنني مساعدتك في استثمارك؟"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        try:
            # دمج الملفات مع السؤال في قائمة واحدة كما يحدث في الاستوديو
            contents_to_send = []
            for f in context_files:
                contents_to_send.append(f)
            contents_to_send.append(prompt)

            # استخدام Gemini 2.5 Pro (لأنه الأدق في تحليل الملفات المرفوعة)
            response = client.models.generate_content(
                model="gemini-flash-latest", 
                contents=contents_to_send,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    temperature=0.0, # الدقة الحرفية مثل الاستوديو
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"تنبيه تقني: {e}")
