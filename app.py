import streamlit as st
import google.generativeai as genai
import glob

# --- 1. الإعدادات ---
api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
if not api_key:
    st.error("API Key missing!")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. تخصيص الواجهة (حل تضارب الـ RTL والإطار الأحمر) ---
st.set_page_config(page_title="APIA Expert", layout="wide")

st.markdown("""
    <style>
    /* إخفاء الخلفيات */
    .stApp, .main, .block-container {
        background: transparent !important;
    }

    /* --- حل مشكلة الأيقونات على اليمين (إجبار الترتيب العربي) --- */
    /* استهداف الحاوية التي تجمع الأيقونة والنص */
    div[data-testid="stChatMessage"] {
        display: flex !important;
        flex-direction: row-reverse !important; /* وضع الأيقونة يميناً والنص يسارها */
        justify-content: flex-start !important;
        direction: rtl !important;
    }

    /* إزالة الخلفية الرمادية من الأيقونة نفسها لدمجها */
    div[data-testid="stChatMessageAvatarUser"], 
    div[data-testid="stChatMessageAvatarAssistant"] {
        background-color: transparent !important;
        margin-left: 15px !important; /* مسافة بين الأيقونة والنص من جهة اليمين */
        margin-right: 0px !important;
    }

    /* --- حل مشكلة الإطار الأحمر في صندوق السؤال --- */
    /* استهداف الحاوية العلوية لمنع الأحمر تماماً */
    [data-testid="stChatInput"] {
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    /* استهداف كل الطبقات الداخلية التي قد تحمل الإطار الأحمر */
    [data-testid="stChatInput"] > div {
        border: none !important;
        box-shadow: none !important;
        background-color: transparent !important;
    }

    /* تنسيق منطقة الكتابة وإلغاء أي تأثير عند النقر (Focus) */
    .stChatInput textarea {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(212, 182, 97, 0.4) !important;
        border-radius: 15px !important;
        direction: rtl !important;
        text-align: right !important;
    }

    /* ضمان عدم ظهور الأحمر عند الضغط للكتابة */
    .stChatInput textarea:focus {
        border: 1px solid #d4b661 !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* البطاقة الترحيبية الزجاجية */
    .welcome-card {
        background: rgba(255, 255, 255, 0.07) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(212, 182, 97, 0.25) !important;
        border-radius: 20px !important;
        padding: 25px !important;
        color: white !important;
        margin-bottom: 30px !important;
        direction: rtl !important;
        text-align: right !important;
    }

    /* توحيد النصوص */
    .stMarkdown, p, span {
        color: #ffffff !important;
        direction: RTL !important;
        text-align: right !important;
    }

    svg { fill: #d4b661 !important; }
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

# --- النص الترحيبي ---
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-card">
        مرحباً بكم في المساعد الذكي لوكالة النهوض بالاستثمارات الفلاحية المطوّر اعتماداً على تقنيات الذكاء الاصطناعي.
        أساعدكم في تقديم إجابات عامة حول الاستثمار الفلاحي والمنح وإجراءات تكوين الملفات وغيرها، وذلك بالاستناد حصرياً إلى وثائق وتقارير مفتوحة ومنشورة للعموم على موقع الوكالة.
        <br><br>
        <strong>تنبيه:</strong>
        <ul style="list-style-type: disc; padding-right: 20px; margin-top: 10px;">
            <li>هذه الخدمة للإرشاد العام وقد يقع بعض الالتباس. يُرجى التثبت من الوثائق الأصلية، وعند الحاجة يمكنكم التواصل عبر kouki.riadh@apia.com.tn.</li>
            <li>يرجى عدم إدخال أي بيانات أو معطيات شخصية داخل المحادثة (الاسم، الهاتف، البريد الإلكتروني، رقم بطاقة التعريف الوطنية، رقم مقرر إسناد الامتيازات، …).</li>
            <li>لا يتم تسجيل أو تخزين أو استعمال محتوى المحادثة لتدريب نماذج الذكاء الاصطناعي.</li>
            <li>لا يتم اعتماد محتوى هذه الدردشة كقرار إداري أو التزام رسمي للوكالة.</li>
        </ul>
        كيف يمكنني مساعدتكم اليوم؟
    </div>
    """, unsafe_allow_html=True)

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
