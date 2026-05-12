import streamlit as st
import google.generativeai as genai
import glob
import os

# --- 1. التحقق من إعدادات الأمان ---
try:
    api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
    if not api_key:
        st.error("❌ خطأ: لم يتم العثور على مفتاح API Key في إعدادات Secrets.")
        st.stop()
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"❌ فشل في إعداد API Key: {e}")
    st.stop()

# --- 2. إعدادات الواجهة (RTL) ---
st.set_page_config(page_title="APIA Expert", page_icon="🌱")
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

st.title("🤖 مساعد APIA الذكي")

# --- 3. تعليمات النظام ---
SYSTEM_PROMPT = "أنت خبير وكالة APIA. أجب بدقة من الملفات المرفقة واستخدم الجداول للأرقام."

# --- 4. معالجة الملفات (تتم مرة واحدة وتخزن في الذاكرة المؤقتة) ---
@st.cache_resource
def load_and_upload_files():
    pdf_files = glob.glob("*.pdf")
    uploaded = []
    for f in pdf_files:
        try:
            # التحقق مما إذا كان الملف موجوداً مسبقاً في جوجل لتوفير الوقت
            u = genai.upload_file(f)
            uploaded.append(u)
        except Exception as e:
            st.warning(f"⚠️ تعذر رفع الملف {f}: {e}")
    return uploaded

knowledge_base = load_and_upload_files()

# --- 5. إدارة جلسة الدردشة (الذاكرة) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# تهيئة الموديل
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# بدء الجلسة المستمرة
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

# عرض الرسائل السابقة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 6. التنفيذ (الاستجابة الفورية والتدفق) ---
if prompt := st.chat_input("اسألني عن أي تفصيل..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_res = ""
        
        try:
            # إرسال الملفات في أول تفاعل فقط، ثم الاعتماد على ذاكرة الجلسة
            is_first = len(st.session_state.messages) <= 1
            content = [prompt] + knowledge_base if (is_first and knowledge_base) else prompt
            
            # تفعيل التدفق (Stream)
            response = st.session_state.chat_session.send_message(content, stream=True)
            
            for chunk in response:
                if chunk.text:
                    full_res += chunk.text
                    placeholder.markdown(full_res + "▌")
            
            placeholder.markdown(full_res)
            st.session_state.messages.append({"role": "assistant", "content": full_res})
            
        except Exception as e:
            st.error(f"❌ حدث خطأ أثناء التوليد: {e}")
