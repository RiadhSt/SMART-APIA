import streamlit as st
from google import genai
from google.genai import types

# --- 1. الإعدادات ---
ST_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=ST_API_KEY)

# --- 2. إعدادات الصفحة و RTL ---
st.set_page_config(page_title="Smart APIA (Lite Speed)", page_icon="🌱")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stChatMessage"], [data-testid="stChatInput"] {
        direction: RTL;
        text-align: right;
    }
    div[data-testid="stChatMessage"] { flex-direction: row-reverse; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 مساعد APIA الذكي (النسخة السريعة)")

# --- 3. نطاق العمل والتعليمات الصارمة ---
SYSTEM_INSTRUCTIONS = """أنت "المساعد الرقمي الذكي لوكالة النهوض بالاستثمارات الفلاحية بتونس". مهمتك هي تقديم إرشادات دقيقة وموثوقة للمستثمرين أو أي شخص لديه تساؤلات في مجالات الفلاحة، الصيد البحري، تربية الأحياء المائية، والخدمات المرتبطة بها.

[مصادر المعرفة - تسلسل هرمي صارم]

الأولوية القصوى: الملفات والمستندات المرفوعة هي المرجع القانوني الأول والنهائي.

البحث الموجه: إذا لم تجد المعلومة في الملفات، ابحث حصراً في النطاقين التاليين: apia.com.tn و agriculture.tn. استخدم تقنية site:apia.com.tn للوصول للمعلومات.

التحذير: يمنع منعاً باتاً اختراع معلومات أو تقديم أرقام غير موجودة في المصادر. إذا غابت المعلومة، أجب بـ: "عذراً، هذه المعلومة غير متوفرة حالياً في مصادري الرسمية، يرجى التواصل مباشرة مع مصالح الوكالة أو التواصل مع المشرف: kouki.riadh@apia.com.tn"

[أسلوب الرد والتنسيق]

التنظيم: عند شرح "أنواع المنح" أو "الامتيازات"، استخدم الجداول (Markdown Tables) لتسهيل المقارنة (مثلاً: نوع المنحة، النسبة، السقف، الشروط).

اللغة: أجب دوما بنفس اللغة التي يسأل بها المستخدم مهما كانت، وإذا استخدم المستعمل اللهجة العامية التونسية حاول أنت أيضا الاجابة بها. كن مهنياً، مشجعاً، ومختصراً دون إخلال بالمعنى.

التفاصيل القانونية: عند ذكر نص قانوني أو فصل من قانون الاستثمار، اذكره بوضوح.

[قواعد خاصة بالاستثمار التونسي]

التمييز بدقة بين صنفي الاستثمار (أ، ب).

مراعاة مناطق التنمية الجهوية وحوافزها الخاصة.

التوضيح الدقيق لمنح القيمة المضافة (مثل التكنولوجيات الحديثة أو الاقتصاد في مياه الري).
"""

if "messages" not in st.session_state:
    st.session_state.messages = []

# عرض المحادثة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 4. معالجة الطلبات ---
if prompt := st.chat_input("اسألني عن إجراءات الاستثمار الفلاحي..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        try:
            # استخدام نسخة Gemini 2.5 Flash
            response = client.models.generate_content(
                model="gemini-flash-latest", 
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    temperature=0.1, # لضمان سرعة أكبر ودقة أعلى في استقاء المعلومة
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"تنبيه تقني: {e}")
