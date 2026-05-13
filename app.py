import streamlit as st
import google.generativeai as genai
import glob

# --- 1. الإعدادات والتحقق من المفتاح ---
api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
if not api_key:
    st.error("❌ المفتاح غير موجود في Secrets!")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. تنسيق الواجهة (RTL) ---
st.set_page_config(page_title="APIA Expert 2.5", layout="centered")
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stChatMessage"], [data-testid="stChatInput"] {
        direction: RTL; text-align: right;
    }
    div[data-testid="stChatMessage"] { flex-direction: row-reverse; }
    table { margin-left: auto; margin-right: 0; width: 100%; border-collapse: collapse; }
    th, td { text-align: right !important; padding: 10px; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 مساعد APIA الذكي (Gemini 2.5 Flash)")

# --- 3. رفع الملفات لمرة واحدة فقط ---
@st.cache_resource
def upload_files_to_gemini():
    pdf_files = glob.glob("*.pdf")
    uploaded = []
    for f in pdf_files:
        try:
            with st.spinner(f"جاري معالجة المرجع: {f}..."):
                u = genai.upload_file(f)
                uploaded.append(u)
        except Exception as e:
            st.warning(f"⚠️ فشل رفع {f}: {e}")
    return uploaded

knowledge_base = upload_files_to_gemini()

# --- 4. تهيئة الذاكرة (Chat Session) لعدم النسيان ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# استخدام موديل 2.5 Flash كما طلبت بدقة
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash", 
    system_instruction="أنت خبير وكالة APIA. أجب بدقة من الملفات. استخدم الجداول للأرقام وتذكر سياق الحوار."
)

# بدء الجلسة المستمرة
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

# عرض الرسائل السابقة من الذاكرة
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- 5. التنفيذ (التدفق اللحظي) ---
if prompt := st.chat_input("اسألني عن وثائق APIA..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # نرسل الملفات في أول رسالة فقط لتقليل وقت المعالجة لاحقاً
        is_first_interaction = len(st.session_state.messages) <= 1
        content = [prompt] + knowledge_base if (is_first_interaction and knowledge_base) else prompt
        
        try:
            # تفعيل التدفق الحقيقي (Streaming)
            response = st.session_state.chat_session.send_message(content, stream=True)
            
            # عرض النص كلمة بكلمة فور توليدها
            full_res = st.write_stream(chunk.text for chunk in response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_res})
        except Exception as e:
            st.error(f"❌ حدث خطأ: {e}")
