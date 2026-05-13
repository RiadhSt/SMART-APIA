import streamlit as st
import google.generativeai as genai
import glob

# --- 1. الإعدادات المستمدة من Google AI Studio ---
api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
if not api_key:
    st.error("API Key missing!")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. تخصيص الواجهة لفرض الشفافية وتصحيح الألوان والاتجاهات ---
st.set_page_config(page_title="APIA Expert", layout="wide")

st.markdown("""
    <style>
    /* 1. إخفاء الخلفيات الافتراضية */
    .stApp, .main, .block-container, [data-testid="stHeader"] {
        background: transparent !important;
        background-color: transparent !important;
    }

    /* 2. تصميم البطاقة الترحيبية الزجاجية */
    .welcome-card {
        background: rgba(255, 255, 255, 0.07) !important;
        backdrop-filter: blur(15px) !important;
        -webkit-backdrop-filter: blur(15px) !important;
        border: 1px solid rgba(212, 182, 97, 0.3) !important;
        border-radius: 20px !important;
        padding: 25px !important;
        color: white !important;
        margin-bottom: 30px !important;
        direction: rtl !important;
        text-align: right !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    }

    /* 3. تصحيح نافذة السؤال (تغيير الأخضر إلى أسود/رمادي داكن) */
    [data-testid="stChatInput"] {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    .stChatInput textarea {
        background-color: #121212 !important; /* لون أسود داكن */
        color: white !important;
        border: 1px solid #d4b661 !important; /* إطار ذهبي */
        border-radius: 12px !important;
        direction: rtl !important;
        text-align: right !important;
    }
    
    /* إلغاء الإطار الأحمر تماماً عند التركيز */
    .stChatInput textarea:focus {
        box-shadow: 0 0 10px rgba(212, 182, 97, 0.3) !important;
        border: 1px solid #d4b661 !important;
        outline: none !important;
    }

    /* 4. تعديل مكان الأيقونات (الصور الرمزية) لتظهر على اليمين */
    [data-testid="stChatMessage"] {
        flex-direction: row-reverse !important;
        direction: rtl !important;
        background: transparent !important;
    }
    
    [data-testid="stChatMessageContent"] {
        margin-right: 15px !important;
        margin-left: 0px !important;
        text-align: right !important;
    }

    /* 5. فرض اللون الذهبي للأيقونات والرموز */
    svg { fill: #d4b661 !important; }
    [data-testid="stChatMessageAvatarUser"] svg, 
    [data-testid="stChatMessageAvatarAssistant"] svg {
        fill: #d4b661 !important;
        color: #d4b661 !important;
    }

    /* 6. تنسيق النصوص العامة والروابط */
    .stMarkdown, p, span, div, li {
        color: #ffffff !important;
        direction: RTL !important;
        text-align: right !important;
    }
    a { color: #d4b661 !important; font-weight: bold; }
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
        <ul style="list-style-type: disc; padding-right: 20px;">
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
