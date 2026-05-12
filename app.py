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
أنت المساعد الذكي لوكالة النهوض بالاستثمارات الفلاحية في تونس. 
نطاق عملك محدد بدقة:
1. الإجابة فقط على الأسئلة المتعلقة بالاستثمار الفلاحي في تونس.
2. مصادرك الوحيدة هي: الوثائق التي تم تدريبك عليها، وموقع الوكالة الرسمي (apia.com.tn)، وموقع وزارة الفلاحة (agriculture.tn).
3. إذا سألك المستخدم عن أي موضوع خارج هذا النطاق (سياسة، ترفيه، طبخ، أخبار عالمية، أو حتى أسئلة عامة غير فلاحية)، أجب بالصيغة التالية:
   " أعتذر منك، أنا مبرمج للإجابة فقط على الاستفسارات المتعلقة بالاستثمار الفلاحي وتوجيه المستثمرين ضمن اختصاصات الوكالة ووزارة الفلاحة. للحصول على تفاصيل أكثر، يرجى التواصل مباشرة مع مصالح الوكالة أو التواصل مع المشرف kouki.riadh@apia.com.tn"
4. ممنوع إبداء الآراء الشخصية أو التوقعات خارج البيانات الرسمية.
5. حافظ دائماً على لهجة مهنية ورسمية.
اللغة: دوما تكون حسب لغة السؤال (يعني إذا كن السؤال بالعربية الفصحى أجب بالعربية الفصحى وإذا كان بالعامية التونسية أجب بالعامية التونسية وإذا كان بلغة أخرى أجب بنفس اللغة التي سألك بها المستخدم).
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
                model="gemini-2.5-flash", 
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTIONS,
                    temperature=0.2,  # تجعل الإجابة دقيقة جداً وغير إبداعية خارج النص
                    tools=[types.Tool(google_search=types.GoogleSearch())] # ميزة إضافية للبحث عن أخبار تونس اللحظية
                )
            )
            
            full_response = response.text
            placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"حدث خطأ: {e}")
