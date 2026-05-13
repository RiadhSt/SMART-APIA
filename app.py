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
    /* تطبيق هوية الموقع البصرية */
    :root {{
        --green-deep: #0a5c35;
        --gold: #d4b661;
        --cream: #fbf9f4;
        --dark: #122a1e;
    }}

    /* خلفية التطبيق العامة */
    .stApp {{
        background-color: var(--dark);
        direction: RTL;
        text-align: right;
    }}

    /* تنسيق نصوص الرسائل */
    .stMarkdown, p, h1, h2, h3 {{
        color: white !important;
        direction: RTL;
        text-align: right;
    }}

    /* تخصيص صناديق الدردشة */
    [data-testid="stChatMessage"] {{
        background-color: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px;
        margin-bottom: 10px;
    }}

    /* تخصيص حقل الإدخال */
    .stChatInput textarea {{
        background-color: #1b3a29 !important;
        color: white !important;
        border: 1px solid var(--gold) !important;
    }}

    /* تنسيق الجداول لتناسب أسلوب الاستشارات */
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
        background-color: rgba(255,255,255,0.05);
    }}
    th {{
        background-color: var(--green-deep);
        color: var(--gold) !important;
        padding: 12px;
        border: 1px solid var(--gold);
    }}
    td {{
        padding: 10px;
        border: 1px solid rgba(212, 182, 97, 0.3);
        color: white;
    }}
    </style>
    """, unsafe_allow_html=True)

#st.title("🤖 مساعد APIA الذكي")

# --- 3. إدارة الملفات (Python RAG Logic) ---
@st.cache_resource
def upload_knowledge():
    files = glob.glob("*.pdf")
    return [genai.upload_file(f) for f in files] if files else []

knowledge = upload_knowledge()

# --- 4. محرك Gemini 2.5 Flash والذاكرة المستمرة ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat" not in st.session_state:
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction="أنت خبير وكالة APIA. أجب بدقة من الملفات المرفقة واستخدم الجداول للأرقام."
    )
    st.session_state.chat = model.start_chat(history=[])

# --- إضافة النص الترحيبي وسياسة الخصوصية ---
if not st.session_state.messages:
    welcome_text = """
    مرحباً بكم في المساعد الذكي لوكالة النهوض بالاستثمارات الفلاحية المطوّر اعتماداً على تقنيات الذكاء الاصطناعي.
    أساعدكم في تقديم إجابات عامة حول الاستثمار الفلاحي والمنح وإجراءات تكوين الملفات وغيرها، وذلك بالاستناد حصرياً إلى وثائق وتقارير مفتوحة ومنشورة للعموم على موقع الوكالة.
    
    **تنبيه:**
    * هذه الخدمة للإرشاد العام وقد تقع بعض الأخطاء أو الالتباس. يُرجى التثبت من النصوص/الوثائق الأصلية، وعند الحاجة يمكنكم التواصل عبر: [kouki.riadh@apia.com.tn](mailto:kouki.riadh@apia.com.tn).
    * لا يتم أبدا تسجيل المحادثات أو استعمالها لتدريب نماذج الذكاء الاصطناعي.
    * يُرجى عدم إدخال أي بيانات أو معطيات شخصية داخل المحادثة (الاسم، الهاتف، البريد الإلكتروني، رقم بطاقة التعريف الوطنية، إلخ).
    * لا يتم اعتماد محتوى هذه الدردشة كقرار إداري أو التزام رسمي للوكالة.
    
    **كيف يمكنني مساعدتكم اليوم؟**
    """
    st.info(welcome_text)

# عرض تاريخ المحادثة
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# --- 5. التنفيذ بالتدفق (Python Streaming) ---
if prompt := st.chat_input("اسألني أي شيء عن الاستثمار الفلاحي..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        is_first = len(st.session_state.messages) <= 1
        content = [prompt] + knowledge if (is_first and knowledge) else prompt
        
        response = st.session_state.chat.send_message(content, stream=True)
        full_res = st.write_stream(chunk.text for chunk in response)
        
        st.session_state.messages.append({"role": "assistant", "content": full_res})
