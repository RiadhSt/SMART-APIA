import streamlit as st
import google.generativeai as genai
import glob

# --- 1. الإعدادات المستمدة من Google AI Studio ---
api_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("SMART APIA API Key")
if not api_key:
    st.error("API Key missing!")
    st.stop()

genai.configure(api_key=api_key)

# --- 2. تخصيص الواجهة لفرض المظهر الداكن والشفاف ---
st.set_page_config(page_title="APIA Expert", layout="wide")

# إضافة CSS قسري لإلغاء أي ألوان افتراضية (أسود أو أزرق)
st.markdown(f"""
    <style>
    /* إلغاء خلفية التطبيق بالكامل */
    .stApp {{
        background: transparent !important;
    }}

    /* استهداف حاوية الرسائل لإزالة اللون الأزرق والأسود */
    [data-testid="stChatMessage"], .stChatMessage {{
        background-color: rgba(255, 255, 255, 0.08) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 20px !important;
        margin-bottom: 15px !important;
    }}

    /* إجبار صندوق st.info (الرسالة الترحيبية) على التخلي عن اللون الأزرق */
    div[data-testid="stNotification"] {{
        background-color: rgba(255, 255, 255, 0.08) !important;
        border: 1px solid #d4b661 !important; /* حدود ذهبية لتمييزها */
        color: white !important;
        border-radius: 20px !important;
    }}
    
    /* منع أي خلفية سوداء تظهر عند التحميل */
    .main, .block-container {{
        background: transparent !important;
    }}

    /* توحيد ألوان النصوص (أبيض ناصع) */
    h1, h2, h3, p, li, span, div, label {{
        color: #ffffff !important;
        text-align: right !important;
        direction: RTL !important;
    }}

    /* تحويل كل الأيقونات الزرقاء إلى ذهبية */
    svg, [data-testid="stIcon"] {{
        fill: #d4b661 !important;
        color: #d4b661 !important;
    }}

    /* تنسيق صندوق الإدخال السفلي */
    .stChatInput textarea {{
        background-color: rgba(10, 40, 30, 0.9) !important;
        color: white !important;
        border: 1px solid #d4b661 !important;
    }}
    
    /* تنسيق الروابط */
    a {{
        color: #d4b661 !important;
        text-decoration: none !important;
        font-weight: bold !important;
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

# --- النص الترحيبي الكامل ---
if not st.session_state.messages:
    full_welcome_text = """
    مرحباً بكم في المساعد الذكي لوكالة النهوض بالاستثمارات الفلاحية المطوّر اعتماداً على تقنيات الذكاء الاصطناعي.
    أساعدكم في تقديم إجابات عامة حول الاستثمار الفلاحي والمنح وإجراءات تكوين الملفات وغيرها، وذلك بالاستناد حصريا إلى وثائق وتقارير مفتوحة ومنشورة للعموم على موقع الوكالة.
    
    تنبيه:
    * هذه الخدمة للإرشاد العام وقد تقع بعض الالتباس. يُرجى التثبت من الوثائق الأصلية، وعند الحاجة يمكنكم التواصل عبر kouki.riadh@apia.com.tn.
    * يرجى عدم إدخال أي بيانات أو معطيات شخصية داخل المحادثة (الاسم، الهاتف، البريد الإلكتروني، رقم بطاقة التعريف الوطنية، رقم مقرر إسناد الامتيازات، …).
    * لا يتم تسجيل أو تخزين أو استعمال محتوى المحادثة لتدريب نماذج الذكاء الاصطناعي.
    * لا يتم اعتماد محتوى هذه الدردشة كقرار إداري أو التزام رسمي للوكالة.
    
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
