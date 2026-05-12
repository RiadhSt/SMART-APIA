import streamlit as st
from google import genai
from google.genai import types
import os

# --- 1. الإعدادات ---
ST_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=ST_API_KEY)

# --- 2. إعدادات الواجهة و RTL ---
st.set_page_config(page_title="Smart APIA - Pro", page_icon="🌱")
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stChatMessage"], [data-testid="stChatInput"] {
        direction: RTL; text-align: right;
    }
    div[data-testid="stChatMessage"] { flex-direction: row-reverse; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 مساعد APIA الذكي (دقة Studio القصوى)")

# --- 3. التعليمات الصارمة (System Instructions) ---
SYSTEM_INSTRUCTIONS = """أنت "المساعد الرقمي الرسمي لوكالة APIA". 
مهمتك: الإجابة بدقة من كافة الملفات المرفقة (عروض، قوانين، جداول).
القوانين:
1. ادمج المعلومات من مختلف الملفات لتعطي إجابة كاملة ودقيقة.
2. التزم ببيانات الملفات المرفقة أولاً كمرجع نهائي.
3. إذا لم تجد المعلومة، وجه المستخدم للمشرف: kouki.riadh@apia.com.tn.
4. التنسيق: استخدم جداول Markdown للأرقام والنسب.
"""

# --- 4. الجزء الأهم: إضافة عناوين ملفات GitHub ---
@st.cache_resource
def upload_github_files():
    # أضف هنا أسماء الملفات تماماً كما تظهر في حسابك على GitHub
    # تأكد من كتابة الاسم مع الامتداد (مثل .pdf أو .pptx)
    filenames = [
        "دليل تعهد ملفات الاستثمار.pdf",
        "RAPPORT_2025_PUBLIQUE.pdf",
        "تقرير فريق عمل الإستثمار الخاص نسخة نهائية محينة.pdf",
        "guide-de-l_investisseur-etranger.pdf",
        "guide_societes_communautaires.pdf",
        "APIA_QA.pdf",
        # يمكنك إضافة أي عدد من الملفات هنا
    ]
    
    uploaded_files_list = []
    
    for f_name in filenames:
        # الكود سيبحث عن الملف في المجلد الرئيسي لـ GitHub/Streamlit
        if os.path.exists(f_name):
            try:
                with st.spinner(f"جاري ربط مرجع: {f_name}..."):
                    # رفع الملف لسيرفرات Gemini ليعالجه مثل Studio
                    u_file = client.files.upload(path=f_name)
                    uploaded_files_list.append(u_file)
            except Exception as e:
                st.error(f"خطأ في تحميل {f_name}: {e}")
        else:
            st.warning(f"الملف {f_name} غير موجود في GitHub. تأكد من رفعه للمستودع.")
            
    return uploaded_files_list

# تنفيذ عملية الربط (تتم مرة واحدة بفضل الكاش)
reference_files = upload_github_files()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. التنفيذ (إرسال الملفات مع السؤال) ---
if prompt := st.chat_input("اسألني عن أي تفصيل في وثائق APIA..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        try:
            # هنا نقوم بتجميع "كل" الملفات التي قرأناها من GitHub مع السؤال
            content_payload = []
            for ref in reference_files:
                content_payload.append(ref)
            
            content_payload.append(prompt) # إضافة سؤال المستخدم في الأخير

            # نستخدم الموديل Pro لضمان أعلى مستوى من الدقة كما في Studio
            response = client.models.generate_content(
                model="gemini-2.5-pro", 
                contents=content_payload,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    temperature=0.0, # حرفية مطلقة لعدم الخطأ في الأرقام
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"عذراً، حدث خطأ تقني: {e}")
