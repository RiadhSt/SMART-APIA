import streamlit as st
import google.generativeai as genai
import glob

# --- 1. الإعدادات المستمدة من Google AI Studio ---
api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
if not api_key:
    st.error("API Key missing!")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. تخصيص الواجهة لتطابق ألوان موقعك (Visual Integration) ---
st.set_page_config(page_title="APIA Expert", layout="centered")

st.markdown(f"""
    <style>
    /* تطبيق هوية الموقع البصرية بناءً على صورة الموقع image_39555e.jpg */
    :root {{
        --green-deep: #0a5c35;
        --gold: #d4b661;
        --text-primary: #ffffff;
    }}

    /* جعل الخلفية شفافة تماماً وإزالة اللون الأزرق الافتراضي */
    .stApp {{
        background: transparent;
        direction: RTL;
        text-align: right;
    }}

    /* تصحيح شامل لجميع ألوان النصوص والأيقونات */
    .stMarkdown, p, h1, h2, h3, li, span, label {{
        color: var(--text-primary) !important;
        direction: RTL;
        text-align: right;
    }}

    /* إزالة اللون الأزرق من صندوق التنبيه وجعله ذهبياً شفافاً */
    div[data-testid="stNotification"] {{
        background-color: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid var(--gold) !important;
        color: white !important;
    }}
    
    /* إخفاء أيقونات المعلومات الزرقاء الافتراضية */
    div[data-testid="stNotification"] svg {{
        fill: var(--gold) !important;
    }}

    /* تخصيص صناديق الدردشة لتكون زجاجية شفافة */
    [data-testid="stChatMessage"] {{
        background-color: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
    }}

    /* تنسيق حقل الإدخال السفلي (إزالة الإطار الأزرق عند التركيز) */
    .stChatInput textarea {{
        background-color: rgba(18, 42, 30, 0.8) !important;
        color: white !important;
        border: 1px solid var(--gold) !important;
        border-radius: 12px !important;
    }}
    .stChatInput textarea:focus {{
        border: 1px solid var(--gold) !important;
        box-shadow: 0 0 5px var(--gold) !important;
    }}
    
    /* تنسيق الروابط والبريد الإلكتروني بالذهبي الصريح */
    a {{
        color: var(--gold) !important;
        text-decoration: underline !important;
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

# --- النص الترحيبي الكامل كما ورد منك تماماً ---
if not st.session_state.messages:
    full_welcome_text = """
    مرحباً بكم في المساعد الذكي لوكالة النهوض بالاستثمارات الفلاحية المطوّر اعتماداً على تقنيات الذكاء الاصطناعي.
    أساعدكم في تقديم إجابات عامة حول الاستثمار الفلاحي والمنح وإجراءات تكوين الملفات وغيرها، وذلك بالاستناد حصريا إلى وثائق وتقارير مفتوحة ومنشورة للعموم على موقع الوكالة.
    
          تنبيه:
      
    * هذه الخدمة للإرشاد العام وقد تقع بعض الأخطاء أو الالتباس. يُرجى التثبت من النصوص/الوثائق الأصلية، وعند الحاجة يمكنكم التواصل عبر: [kouki.riadh@apia.com.tn](mailto:kouki.riadh@apia.com.tn).
    
    * يرجى عدم إدخال أي بيانات أو معطيات شخصية داخل المحادثة (الاسم، الهاتف، البريد الإلكتروني، رقم بطاقة التعريف الوطنية، رقم مقرر إسناد الامتيازات، …).
    
    * لا يتم اعتماد محتوى هذه الدردشة كقرار إداري أو التزام رسمي للوكالة.
    
    كيف يمكنني مساعدتكم اليوم؟
    """
    st.info(full_welcome_text)

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
