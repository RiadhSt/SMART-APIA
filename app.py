import streamlit as st
import google.generativeai as genai
import glob

# --- 1. الإعدادات المستمدة من Google AI Studio ---
api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
if not api_key:
    st.error("API Key missing!")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. تخصيص الواجهة (إلغاء الإطار الأحمر والخلفية الرمادية) ---
st.set_page_config(page_title="APIA Expert", layout="wide")

st.markdown("""
    <style>
    /* 1. تنظيف شامل للخلفيات */
    .stApp, .main, .block-container {
        background: transparent !important;
    }

    /* 2. تصميم البطاقة الترحيبية الزجاجية */
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

    /* 3. حل جذري لصندوق السؤال (إزالة الأحمر والرمادي) */
    /* استهداف الحاوية الخارجية لإلغاء أي إطار أحمر */
    [data-testid="stChatInput"] {
        border: none !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }

    /* استهداف منطقة الكتابة الفعلية */
    .stChatInput textarea {
        background-color: rgba(255, 255, 255, 0.05) !important; /* خلفية زجاجية خفيفة جداً */
        color: white !important;
        border: 1px solid rgba(212, 182, 97, 0.4) !important; /* إطار ذهبي نحيف */
        border-radius: 15px !important;
        box-shadow: none !important;
    }

    /* إزالة الإطار الأحمر عند النقر أو التركيز (Focus) */
    .stChatInput textarea:focus {
        border: 1px solid #d4b661 !important; /* تحويله لذهبي ثابت عند التركيز */
        outline: none !important;
        box-shadow: 0 0 10px rgba(212, 182, 97, 0.2) !important;
    }

    /* 4. توحيد نصوص المحادثة */
    .stMarkdown, p, span {
        color: #ffffff !important;
        direction: RTL !important;
        text-align: right !important;
    }

    /* أيقونات ذهبية */
    svg { fill: #d4b661 !important; }
    
    a { color: #d4b661 !important; }
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

# --- عرض النص الترحيبي بنمط البطاقة الزجاجية ---
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
