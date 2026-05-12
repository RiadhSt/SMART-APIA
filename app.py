import streamlit as st
from google import genai
from google.genai import types

# --- 1. الإعدادات وقراءة المفتاح السري ---
ST_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=ST_API_KEY)

# --- 2. إعدادات الصفحة و RTL ---
st.set_page_config(page_title="Smart APIA", page_icon="🌱")

st.markdown("""
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stChatMessage"], [data-testid="stChatInput"] {
        direction: RTL;
        text-align: right;
    }
    div[data-testid="stChatMessage"] { flex-direction: row-reverse; }
    /* تحسين سرعة العرض */
    .stMarkdown { transition: none !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 مساعد وكالة APIA الذكي")

# --- 3. التعليمات الصارمة ونطاق العمل ---
SYSTEM_INSTRUCTIONS = """
أنت المساعد الذكي الرسمي لوكالة APIA تونس. 
نطاق عملك: الاستثمار الفلاحي، الصيد البحري، وخطط التنمية الفلاحية 2026-2030 فقط.
مصادر الإجابة: 1. الوثائق المرفوعة (الملفات). 2. موقع apia.com.tn. 3. موقع agriculture.tn.

القواعد الصارمة:
- إذا كان السؤال خارج المجال الفلاحي، أجب بـ: "أعتذر منك، أنا مبرمج للإجابة فقط على الاستفسارات المتعلقة بالاستثمار الفلاحي وتوجيه المستثمرين ضمن اختصاصات الوكالة ووزارة الفلاحة. للتواصل مع المشرف: kouki.riadh@apia.com.tn"
- استخدم الجداول دائماً لعرض الأرقام والمقارنات.
- التزم بلغة المستخدم (تونسية، عربية، فرنسية).
"""

if "messages" not in st.session_state:
    st.session_state.messages = []

# عرض المحادثة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 4. التفاعل السريع جداً ---
if prompt := st.chat_input("كيف يمكنني مساعدتك اليوم؟"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        try:
            # استخدام Gemini 1.5 Flash - الأسرع عالمياً في معالجة النصوص الضخمة
            response = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    temperature=0.1, # أقل قيمة لضمان أقصى سرعة وأعلى دقة
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            # حل ذكي في حال حدوث ضغط: إعادة المحاولة تلقائياً
            st.error("السيرفر مشغول حالياً، يرجى إعادة إرسال السؤال.")
