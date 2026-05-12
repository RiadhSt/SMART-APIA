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
SYSTEM_INSTRUCTIONS = """
أنت المساعد الذكي الرسمي لوكالة النهوض بالاستثمارات الفلاحية (APIA) بتونس.
مهمتك: الإجابة على استفسارات المستثمرين بناءً على وثائق الوكالة المرفوعة وموقعي (apia.com.tn) و (agriculture.tn).

القواعد المهنية:
1. النطاق: أجب فقط عن الاستثمار الفلاحي، الصيد البحري، والخدمات المرتبطة.
2. خارج النطاق: إذا كان السؤال غير فلاحي، اعتذر بأدب ووجه المستخدم للتواصل مع المشرف: kouki.riadh@apia.com.tn.
3. اللغة: أجب بنفس لغة السائل (فصحى، تونسية، فرنسية، إنجليزية).
4. التنسيق: استخدم الجداول دائماً عند ذكر أرقام أو منح أو مقارنات.
5. الدقة: لا تقدم وعوداً بمنح أو موافقات، بل وضح الإجراءات القانونية المتبعة حسب الوثائق.
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
