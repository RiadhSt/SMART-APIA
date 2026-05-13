import streamlit as st
import google.generativeai as genai
import glob

# --- 1. الإعدادات ---
api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
if not api_key:
    st.error("API Key missing!")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. تخصيص الواجهة (الحل النهائي للأيقونات والألوان) ---
st.set_page_config(page_title="APIA Expert", layout="wide")

st.markdown("""
    <style>
    /* 1. تصفير الخلفيات */
    .stApp, .main, .block-container {
        background: transparent !important;
    }

    /* 2. إجبار الأيقونات على اليمين واستعادة اللون الذهبي */
    /* استهداف الحاوية الكبرى للرسالة */
    [data-testid="stChatMessage"] {
        display: flex !important;
        flex-direction: row-reverse !important; /* الأيقونة يميناً */
        text-align: right !important;
        direction: rtl !important;
        background: transparent !important;
    }

    /* استهداف الأيقونة (Avatar) وفرض لونها ومكانها */
    [data-testid="stChatMessageAvatarUser"], 
    [data-testid="stChatMessageAvatarAssistant"] {
        order: 1 !important; /* التأكد من أنها العنصر الأول من اليمين */
        margin-left: 15px !important;
        margin-right: 0px !important;
    }

    /* تلوين الأيقونات بالذهبي */
    [data-testid="stChatMessageAvatarUser"] svg, 
    [data-testid="stChatMessageAvatarAssistant"] svg {
        fill: #d4b661 !important;
        color: #d4b661 !important;
        width: 28px !important;
        height: 28px !important;
    }

    /* استهداف نص الرسالة */
    [data-testid="stChatMessageContent"] {
        order: 2 !important;
        flex-grow: 1 !important;
        background: transparent !important;
    }

    /* 3. صندوق الأسئلة الممتاز (بدون إطارات حمراء أو رمادية) */
    [data-testid="stChatInput"] {
        background-color: transparent !important;
        border: none !important;
    }

    .stChatInput textarea {
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(212, 182, 97, 0.5) !important;
        border-radius: 15px !important;
        direction: rtl !important;
        text-align: right !important;
    }

    .stChatInput textarea:focus {
        border: 1px solid #d4b661 !important;
        box-shadow: 0 0 10px rgba(212, 182, 97, 0.2) !important;
        outline: none !important;
    }

    /* زر الإرسال */
    [data-testid="stChatInputSubmitButton"] svg {
        fill: #d4b661 !important;
    }

    /* البطاقة الترحيبية */
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
    .stMarkdown, p, span, li {
        color: #ffffff !important;
        direction: RTL !important;
        text-align: right !important;
    }
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
