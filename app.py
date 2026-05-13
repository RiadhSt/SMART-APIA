import streamlit as st
import google.generativeai as genai
import glob

# --- 1. الإعدادات ---
api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
if not api_key:
    st.error("API Key missing!")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. الواجهة (RTL) ---
st.set_page_config(page_title="APIA Expert", layout="centered")
st.markdown("<style>*{direction: RTL; text-align: right;}</style>", unsafe_allow_html=True)
st.title("🤖 مساعد APIA الذكي")

# --- 3. الملفات (الرفع لمرة واحدة) ---
@st.cache_resource
def upload_knowledge():
    files = glob.glob("*.pdf")
    return [genai.upload_file(f) for f in files] if files else []

knowledge = upload_knowledge()

# --- 4. المحادثة والذاكرة ---
if "chat" not in st.session_state:
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction="أنت خبير وكالة APIA. أجب بدقة من الملفات المرفقة واستخدم الجداول للأرقام."
    )
    st.session_state.chat = model.start_chat(history=[])
    st.session_state.messages = []

# عرض التاريخ
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. التنفيذ بالتدفق (Streaming) ---
if prompt := st.chat_input("اسألني أي شيء..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        # إرسال الملفات في أول مرة فقط
        is_first = len(st.session_state.messages) <= 1
        content = [prompt] + knowledge if (is_first and knowledge) else prompt
        
        # التدفق الحقيقي
        response = st.session_state.chat.send_message(content, stream=True)
        full_res = st.write_stream(chunk.text for chunk in response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_res})
