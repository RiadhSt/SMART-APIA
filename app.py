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
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 مساعد وكالة APIA الذكي")

# --- 3. إدارة الملفات والذاكرة (الـ Context) ---
# سنقوم بتعريف التعليمات والملفات التي رفعتها في Studio هنا
SYSTEM_INSTRUCTIONS = """
أنت الخبير الرقمي لوكالة APIA تونس. 
مهمتك: الإجابة بدقة بناءً على وثائق الوكالة (خطة 2026-2030، قوانين الاستثمار، ومنح الفلاحة).
اللغة: العربية (أو العامية التونسية/الفرنسية حسب السائل).
التنسيق: استخدم الجداول دائماً للمقارنات والأرقام.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []

# عرض الرسائل السابقة
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 4. معالجة السؤال والرد ---
if prompt := st.chat_input("كيف يمكنني مساعدتك في استثمارك الفلاحي؟"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            # استخدام الموديل مباشرة مع التعليمات (سريع جداً في Flash 2.5)
            # لاحظ: Gemini 2.5 Flash يمتلك ذاكرة ضخمة تغنيك عن الـ Cache المعقد برمجياً حالياً
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    tools=[types.Tool(google_search=types.GoogleSearch())] # ميزة إضافية للبحث عن أخبار تونس اللحظية
                )
            )
            
            full_response = response.text
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"حدث خطأ: {e}")
