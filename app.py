import streamlit as st
import google.generativeai as genai
import glob

# --- 1. الإعدادات المستمدة من Google AI Studio ---
api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
if not api_key:
    st.error("API Key missing!")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. تخصيص الواجهة لفرض الشفافية الكاملة وتصحيح الألوان ---
st.set_page_config(page_title="APIA Expert", layout="wide")

st.markdown("""
    <style>
    /* 1. إخفاء أي خلفيات بيضاء أو رمادية افتراضية */
    .stApp, .main, .block-container, [data-testid="stHeader"] {
        background: transparent !important;
        background-color: transparent !important;
    }

    /* 2. تصميم "البطاقة الزجاجية" للنص الترحيبي (بديل st.info الأزرق) */
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

    /* 3. تصحيح نافذة السؤال (Input Box) لتصبح بخلفية داكنة بدلاً من الأخضر */
    [data-testid="stChatInput"] {
        background-color: transparent !important;
    }
    .stChatInput textarea {
        /* تم تغيير اللون هنا من الأخضر الداكن إلى الأسود الرمادي */
        background-color: #1a1a1a !important; 
        color: white !important;
        border: 1px solid #d4b661 !important; /* حد ذهبي صريح */
        border-radius: 12px !important;
    }

    /* 4. إجبار كافة النصوص على اللون الأبيض وRTL */
    .stMarkdown, p, span, div {
        color: #ffffff !important;
        direction: RTL !important;
        text-align: right !important;
    }

    /* تغيير لون الأيقونات للذهبي لمنع أي ظهور للأزرق */
    svg { fill: #d4b661 !important; }
    
    /* تنسيق الروابط */
    a { color: #d4b661 !important; font-weight: bold; }
    .highlight-yellow {
    color: #fffd01 !important; /* أصفر صريح وواضح */
    font-weight: bold !important;
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

# --- النص الترحيبي (باستخدام HTML صرف لضمان ثبات اللون) ---
# --- النص الترحيبي المحدث ---
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-card">
        مرحباً بكم في المساعد الذكي لوكالة النهوض بالاستثمارات الفلاحية المطوّر اعتماداً على تقنيات الذكاء الاصطناعي.
        أساعدكم في تقديم إجابات عامة حول الاستثمار الفلاحي والمنح وإجراءات تكوين الملفات وغيرها، وذلك بالاستناد حصرياً إلى وثائق وتقارير مفتوحة ومنشورة للعموم على موقع الوكالة.
        <br><br>
        <strong class="highlight-yellow">تنبيه:</strong>
        <ul style="list-style-type: disc; padding-right: 20px;">
            <li>هذه الخدمة للإرشاد العام وقد يقع بعض الالتباس. يُرجى التثبت من الوثائق الأصلية، وعند الحاجة يمكنكم التواصل عبر kouki.riadh@apia.com.tn.</li>
            <li>يرجى عدم إدخال أي معطيات شخصية داخل المحادثة (الاسم، الهاتف، البريد الإلكتروني، رقم بطاقة التعريف الوطنية، رقم مقرر إسناد الامتيازات، …).</li>
            <li>لا يتم تسجيل أو تخزين أو استعمال محتوى المحادثة لتدريب نماذج الذكاء الاصطناعي.</li>
            <li>لا يتم اعتماد محتوى هذه الدردشة كقرار إداري أو التزام رسمي للوكالة.</li>
        </ul>
        <br>
<span class="highlight-yellow">كيف يمكنني مساعدتكم اليوم؟</span>    </div>
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
