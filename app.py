import streamlit as st
from google import genai
from google.genai import types
import os

# --- 1. الإعدادات ---
ST_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=ST_API_KEY)

# --- 2. إعدادات الصفحة ---
st.set_page_config(page_title="APIA Expert AI", page_icon="🌱")
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { direction: RTL; text-align: right; }
    div[data-testid="stChatMessage"] { flex-direction: row-reverse; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 خبير وكالة APIA (دقة Studio الكاملة)")

# --- 3. التعليمات الصارمة ---
SYSTEM_INSTRUCTIONS = """أنت "المساعد الرقمي الرسمي لوكالة APIA". 
مهمتك: استخراج الإجابات من الملفات المرفقة بدقة حرفية. 
القوانين:
1. لا تجب من ذاكرتك العامة، استخدم فقط الملفات المرفقة والبحث في موقع apia.com.tn.
2. إذا لم تجد المعلومة، قل "غير متوفرة" ووجه المستخدم لـ kouki.riadh@apia.com.tn.
3. التنسيق: جداول Markdown للأرقام والنسب.
"""

# --- 4. الجزء المفقود: رفع الملف برمجياً (هذا ما يفعله Studio) ---
@st.cache_resource
def upload_knowledge_file():
    # تأكد من رفع ملف الـ PDF الخاص بك إلى GitHub بجانب هذا الملف
    # وقم بتغيير الاسم هنا للاسم الصحيح لملفك
    filename = "APIA_Knowledge_Base.pdf" 
    if os.path.exists(filename):
        # رفع الملف لسيرفرات جوجل ليكون متاحاً للـ API
        file_upload = client.files.upload(path=filename)
        return file_upload
    return None

# محاولة تجهيز الملف المرجعي
reference_file = upload_knowledge_file()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. التنفيذ (المطابق لـ Studio) ---
if prompt := st.chat_input("اسألني أي سؤال من ملفات الوكالة..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        try:
            # هنا السر: نرسل الملف + السؤال معاً في مصفوفة واحدة (مثل Studio تماماً)
            content_parts = []
            if reference_file:
                content_parts.append(reference_file) # إضافة الملف أولاً
            content_parts.append(prompt) # إضافة السؤال ثانياً

            response = client.models.generate_content(
                model="gemini-2.0-flash", # يمكنك استخدام 2.5 Pro إذا أردت دقة أعلى
                contents=content_parts,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    temperature=0.0, # السر لعدم "تأليف" إجابات
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"خطأ تقني: {e}")
