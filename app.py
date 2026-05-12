import streamlit as st
from google import genai
from google.genai import types
import time

# --- 1. الإعدادات ---
ST_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=ST_API_KEY)

# --- 2. إعدادات الصفحة و RTL ---
st.set_page_config(page_title="Smart APIA", page_icon="🌱")
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stChatMessage"], [data-testid="stChatInput"] {
        direction: RTL; text-align: right;
    }
    div[data-testid="stChatMessage"] { flex-direction: row-reverse; }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 مساعد وكالة APIA الذكي (نسخة السرعة القصوى)")

SYSTEM_INSTRUCTIONS = """
أنت المساعد الذكي لوكالة النهوض بالاستثمارات الفلاحية في تونس. 
نطاق عملك محدد بدقة:
1. الإجابة فقط على الأسئلة المتعلقة بالاستثمار الفلاحي في تونس.
2. مصادرك الوحيدة هي: الوثائق التي تم تدريبك عليها، وموقع الوكالة الرسمي (apia.com.tn)، وموقع وزارة الفلاحة (agriculture.tn).
3. إذا سألك المستخدم عن أي موضوع خارج هذا النطاق، أجب بالصيغة المحددة واذكر البريد الإلكتروني kouki.riadh@apia.com.tn.
4. اللغة: اتبع لغة المستخدم (فصحى، عامية، فرنسية).
5. التنسيق: استخدم الجداول للأرقام والمقارنات.
"""

# --- 3. إنشاء الـ Context Cache (هنا تكمن السرعة) ---
# سنقوم بإنشاء الـ Cache مرة واحدة فقط ليبقى في ذاكرة جوجل
@st.cache_resource
def setup_context_cache():
    # ملاحظة: الـ Caching يتطلب تعيين وقت انتهاء (TTL) - هنا ضبطناه لـ ساعتين
    cache = client.caches.create(
        model="models/gemini-1.5-flash-001",
        config=types.CacheConfig(
            display_name="apia_policy_cache",
            system_instruction=SYSTEM_INSTRUCTIONS,
            ttl_seconds=7200, 
        )
    )
    return cache.name

# جلب اسم الـ Cache
try:
    cache_id = setup_context_cache()
except Exception as e:
    st.error(f"فشل إعداد الذاكرة المؤقتة: {e}")
    cache_id = None

# --- 4. إدارة المحادثة ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("كيف يمكنني مساعدتك؟"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        
        try:
            # استخدام الـ Cache للرد السريع جداً
            response = client.models.generate_content(
                model=cache_id if cache_id else "gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            
            placeholder.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"حدث خطأ أثناء التوليد: {e}")
