import streamlit as st
from google import genai
from google.genai import types
import datetime

# --- الإعدادات ---
ST_API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=ST_API_KEY)

# --- تفعيل الـ Caching ---
# سنقوم بإنشاء الـ Cache لملفاتك لتقليل استهلاك التوكنز وزيادة السرعة
@st.cache_resource
def get_cached_model():
    # 1. جلب الملفات المرفوعة مسبقاً (تأكد أن الملفات مرفوعة على نفس الـ API Key)
    # ملاحظة: سنفترض أنك تريد استخدام ملف الـ 82 سلايد والتقارير
    
    # 2. إنشاء الـ Content Cache
    # الـ TTL (Time To Live) هنا ساعة واحدة، يمكن زيادتها
    cached_content = client.caches.create(
        model='models/gemini-1.5-flash-004', 
        config=types.CacheConfig(
            display_name='apia_docs_cache',
            contents=[
                # هنا نضع مراجع الملفات، أو نكتفي بالتعليمات الضخمة
            ],
            system_instruction="أنت خبير وكالة APIA. اعتمد كلياً على الوثائق المرفوعة في ذاكرتك للإجابة بدقة عن الاستثمار الفلاحي في تونس 2026-2030.",
            ttl_seconds=3600, 
        )
    )
    return cached_content.name

# استدعاء اسم الـ Cache
cache_name = get_cached_model()

# --- واجهة التطبيق ---
st.set_page_config(page_title="Smart APIA", page_icon="🌱")

# تنسيق RTL
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stChatMessage"], [data-testid="stChatInput"] {
        direction: RTL;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🤖 مساعد APIA (نسخة الذاكرة الذكية)")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("اسألني عن تفاصيل خطة 2026-2030..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_response = ""
        
        try:
            # استخدام الـ Cache في التوليد
            response = client.models.generate_content(
                model=cache_name, # نستخدم الـ Cache هنا بدلاً من الموديل الخام
                contents=prompt
            )
            
            full_response = response.text
            placeholder.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"خطأ في الذاكرة المؤقتة: {e}")
