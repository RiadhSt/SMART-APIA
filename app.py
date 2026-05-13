import streamlit as st
import google.generativeai as genai
import glob

# --- 1. الإعدادات المستمدة من Google AI Studio ---
api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
if not api_key:
    st.error("API Key missing!")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. تخصيص الواجهة لتثبيت الألوان ومنع اللون الأسود والأزرق ---
st.set_page_config(page_title="APIA Expert", layout="wide")

st.markdown(f"""
    <style>
    /* فرض الخلفية الشفافة على كل المستويات لمنع اللون الأسود */
    .stApp, .main, .block-container {{
        background: transparent !important;
        background-color: transparent !important;
    }}

    /* تطبيق هوية الموقع البصرية بناءً على صورة image_2df433.jpg */
    :root {{
        --green-deep: #0a5c35;
        --gold: #d4b661;
        --text-primary: #ffffff;
        --glass-bg: rgba(255, 255, 255, 0.11);
        --glass-border: rgba(255, 255, 255, 0.22);
        --radius: 20px;
    }}

    /* منع اللون الأزرق والأسود في صناديق التنبيه والدردشة */
    div[data-testid="stNotification"], [data-testid="stChatMessage"], .stAlert {{
        background: var(--glass-bg) !important;
        background-color: var(--glass-bg) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: var(--radius) !important;
        color: white !important;
        max-width: 100% !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
    }}

    /* إخفاء أي خلفيات زرقاء افتراضية للنصوص */
    .stMarkdown, p, h1, h2, h3, li, span, label {{
        color: var(--text-primary) !important;
        direction: RTL !important;
        text-align: right !important;
    }}

    /* تغيير لون أيقونات التنبيه من الأزرق إلى الذهبي */
    svg {{
        fill: var(--gold) !important;
    }}

    /* تنسيق حقل الإدخال السفلي ومنع الإطار الأزرق عند الكتابة */
    .stChatInput textarea {{
        background-color: rgba(18, 42, 30, 0.8) !important;
        color: white !important;
        border: 1px solid var(--gold) !important;
    }}
    .stChatInput textarea:focus {{
        border: 1px solid var(--gold) !important;
        box-shadow: 0 0 5px var(--gold) !important;
    }}
    
    /* تنسيق الروابط بالذهبي */
    a {{
        color: var(--gold) !important;
        text-decoration: underline !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. إدارة الملفات ---
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

# --- النص الترحيبي الكامل الثابت ---
if not st.session_state.messages:
    full_welcome_text = """
    مرحباً بكم في المساعد الذكي لوكالة النهوض بالاستثمارات الفلاحية المطوّر اعتماداً على تقنيات الذكاء الاصطناعي.
    أساعدكم في تقديم إجابات عامة حول الاستثمار الفلاحي والمنح وإجراءات تكوين الملفات وغيرها، وذلك بالاستناد حصريا إلى وثائق وتقارير مفتوحة ومنشورة للعموم على موقع الوكالة.
    
    تنبيه:
    هذه الخدمة للإرشاد العام وقد تقع بعض الأخطاء أو الالتباس. يُرجى التثبت من النصوص/الوثائق الأصلية، وعند الحاجة يمكنكم التواصل عبر: [kouki.riadh@apia.com.tn](mailto:kouki.riadh@apia.com.tn).
    يُرجى عدم إدخال أي بيانات أو معطيات شخصية داخل المحادثة (الاسم، الهاتف، البريد الإلكتروني، رقم بطاقة التعريف الوطنية، رقم مقرر إسناد الامتيازات، …).
    لا يتم اعتماد محتوى هذه الدردشة كقرار إداري أو التزام رسمي للوكالة.
    
    كيف يمكنني مساعدتكم اليوم؟
    """
    st.info(full_welcome_text)

# عرض المحادثة
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. التنفيذ بالتدفق ---
if prompt := st.chat_input("اسألني عن الاستثمار الفلاحي..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        is_first = len(st.session_state.messages) <= 1
        content = [prompt] + knowledge if (is_first and knowledge) else prompt
        response = st.session_state.chat.send_message(content, stream=True)
        full_res = st.write_stream(chunk.text for chunk in response)
        st.session_state.messages.append({"role": "assistant", "content": full_res})
