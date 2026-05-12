import streamlit as st
from google import genai
from google.genai import types
import os

# --- 1. الإعدادات ---
# ملاحظة: تأكد أن الاسم في Streamlit Secrets هو "GEMINI_API_KEY" لتجنب خطأ KeyError
try:
    ST_API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=ST_API_KEY)
except Exception as e:
    st.error("خطأ: لم يتم العثور على مفتاح API. تأكد من إضافته في Secrets باسم GEMINI_API_KEY")
    st.stop()

# --- 2. إعدادات الواجهة و RTL ---
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

# --- 3. التعليمات الصارمة (System Instructions) ---
SYSTEM_INSTRUCTIONS = """أنت "المساعد الرقمي الرسمي لوكالة APIA". 
مهمتك: الإجابة بدقة مطلقة من كافة الملفات المرفقة (عروض، قوانين، أدلة).
القوانين:
1. ادمج المعلومات من مختلف الملفات لتقديم إجابة شاملة.
2. الملفات المرفقة هي المرجع الأول والنهائي.
3. التنسيق: استخدم جداول Markdown للأرقام والنسب.
4. في حال غياب المعلومة، وجه المستخدم لـ kouki.riadh@apia.com.tn.
"""

# --- 4. وظيفة رفع الملفات من GitHub ---
@st.cache_resource
def upload_github_files():
    # تأكد أن هذه الأسماء تطابق تماماً ملفاتك في GitHub (بدون حروف خاصة أو مسافات معقدة)
    filenames = [
        "Guide_Global.pdf", 
        "RAPPORT_2025_PUBLIQUE.pdf",
        "Rapport_Comite_Inv.pdf",
        "guide-de-l_investisseur-etranger.pdf",
        "guide_societes_communautaires.pdf",
        "APIA_QA.pdf"
    ]
    
    uploaded_files_list = []
    
    for f_name in filenames:
        if os.path.exists(f_name):
            try:
                with st.spinner(f"جاري ربط مرجع: {f_name}..."):
                    # الرفع باستخدام المعامل الصحيح 'file'
                    u_file = client.files.upload(file=f_name) 
                    uploaded_files_list.append(u_file)
            except Exception as e:
                st.error(f"خطأ في تحميل {f_name}: {e}")
        else:
            st.warning(f"الملف {f_name} غير موجود في GitHub.")
            
    return uploaded_files_list

# تنفيذ عملية الربط (تتم مرة واحدة بفضل الكاش)
reference_files = upload_github_files()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. التنفيذ بالدقة والسرعة (Gemini 2.0 Flash) ---
if prompt := st.chat_input("اسألني عن أي تفصيل في وثائق APIA..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        try:
            # تجميع الملفات مع السؤال
            content_payload = []
            for ref in reference_files:
                content_payload.append(ref)
            
            content_payload.append(prompt)

            # استخدام gemini-2.0-flash للسرعة الفائقة مع الحفاظ على الدقة
            response = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=content_payload,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    temperature=0.0,
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"عذراً، حدث خطأ تقني أثناء التوليد: {e}")
