import streamlit as st
import google.generativeai as genai
import glob

# --- 1. الإعدادات المستمدة من Google AI Studio ---
api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
if not api_key:
    st.error("API Key missing!")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. تخصيص الواجهة لتطابق صورة الموقع image_39555e.jpg ---
st.set_page_config(page_title="APIA Expert", layout="centered")

st.markdown(f"""
    <style>
    /* تطبيق هوية الموقع البصرية بناءً على لوحة الألوان المقدمة */
    :root {{
        --green-deep: #0a5c35;
        --gold: #d4b661;
        --text-primary: #ffffff;
        --glass-bg: rgba(255, 255, 255, 0.05);
    }}

    /* جعل الخلفية شفافة لتندمج مع تصميم الموقع المدمج */
    .stApp {{
        background: transparent;
        direction: RTL;
        text-align: right;
    }}

    /* تصحيح ألوان النصوص لتصبح واضحة جداً */
    .stMarkdown, p, h1, h2, h3, li {{
        color: var(--text-primary) !important;
        direction: RTL;
        text-align: right;
        font-weight: 400;
    }}

    /* تنسيق صندوق التنبيه ليكون شفافاً بحدود ذهبية (كما في الصورة) */
    .stAlert {{
        background-color: var(--glass-bg) !important;
        border: 1px solid var(--gold) !important;
        color: white !important;
        border-radius: 15px;
    }}

    /* تخصيص صناديق الدردشة لتكون زجاجية */
    [data-testid="stChatMessage"] {{
        background-color: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
    }}

    /* تحسين مظهر حقل الإدخال السفلي */
    .stChatInput textarea {{
        background-color: rgba(18, 42, 30, 0.8) !important;
        color: white !important;
        border: 1px solid var(--gold) !important;
        border-radius: 12px !important;
    }}
    
    /* تنسيق الروابط لتكون باللون الذهبي الواضح */
    a {{
        color: var(--gold) !important;
        text-decoration: none;
        font-weight: bold;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. إدارة الملفات (Python RAG Logic) ---
@st.cache_resource
def upload_knowledge():
    files = glob.glob("*.pdf")
    return [genai.upload_file(f) for f in files] if files else []

knowledge = upload_knowledge()

# --- 4. محرك Gemini والذاكرة المستمرة ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat" not in st.session_state:
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction="أنت خبير وكالة APIA. أجب بدقة من الملفات المرفقة واستخدم الجداول للأرقام."
    )
    st.session_state.chat = model.start_chat(history=[])

# --- النص الترحيبي المحسن بصرياً بناءً على صورة الموقع ---
if not st.session_state.messages:
    welcome_text = """
    **مرحباً بكم في المساعد الذكي لوكالة النهوض بالاستثمارات الفلاحية**
    
    أساعدكم في تقديم إجابات عامة حول الاستثمار الفلاحي والمنح وإجراءات تكوين الملفات، وذلك بالاستناد حصرياً إلى وثائق وتقارير الوكالة المنشورة.
    
    ⚠️ **تنبيه هام:**
    * هذه الخدمة للإرشاد العام؛ يُرجى التثبت من النصوص الأصلية.
    * للتواصل الرسمي: [kouki.riadh@apia.com.tn](mailto:kouki.riadh@apia.com.tn).
    * يُرجى عدم إدخال أي بيانات شخصية (رقم تعريف، هاتف، إلخ).
    
    **كيف يمكنني مساعدتكم اليوم؟**
    """
    st.info(welcome_text)

# عرض تاريخ المحادثة
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. التنفيذ بالتدفق (Python Streaming) ---
if prompt := st.chat_input("اسألني عن الاستثمار الفلاحي..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        is_first = len(st.session_state.messages) <= 1
        content = [prompt] + knowledge if (is_first and knowledge) else prompt
        
        response = st.session_state.chat.send_message(content, stream=True)
        full_res = st.write_stream(chunk.text for chunk in response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_res})
