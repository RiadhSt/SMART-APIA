import streamlit as st
from google import genai
from google.genai import types

# --- 1. إعداد الصفحة والمفتاح ---

# قراءة المفتاح من Secrets الخاصة بـ Streamlit
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=ST_API_KEY)
MODEL_ID = "gemini-2.5-flash"

# --- 2. تعليمات النظام (System Instruction) ---

SYSTEM_PROMPT = """أنت "المساعد الرقمي الذكي لوكالة النهوض بالاستثمارات الفلاحية بتونس". مهمتك هي تقديم إرشادات دقيقة وموثوقة للمستثمرين في مجالات الفلاحة، الصيد البحري، وتربية الأحياء المائية.

[مصادر المعرفة]
الأولوية القصوى للملفات المرفوعة. إذا لم تجد المعلومة، ابحث في apia.com.tn أو agriculture.tn.
يمنع اختراع معلومات. إذا غابت المعلومة، وجه المستخدم للتواصل مع المشرف: kouki.riadh@apia.com.tn

[أسلوب الرد]
- استخدم الجداول لشرح المنح والامتيازات.
- أجب بنفس لغة المستخدم مهما كانت (إذا استعمل العامية التونسية استعملها أنت أيضا).
- كن مهنياً ومختصراً."""

# --- 3. واجهة المستخدم (Streamlit UI) ---
st.set_page_config(page_title="Smart APIA", page_icon="🌱", layout="centered")
st.title("🤖 SMART APIA")
st.caption("المساعد الذكي لوكالة النهوض بالاستثمارات الفلاحية")

# تهيئة سجل المحادثة
if "messages" not in st.session_state:
    st.session_state.messages = []

# عرض الرسائل السابقة
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. منطق الإجابة والتدفق (Streaming) ---
if prompt := st.chat_input("اطرح سؤالك هنا..."):

    # إضافة سؤال المستخدم للسجل وعرضه
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # تحضير إعدادات التوليد
    config = types.GenerateContentConfig(
        temperature=0.2,
        system_instruction=SYSTEM_PROMPT,
        tools=[types.Tool(google_search=types.GoogleSearch())],
    )

    # عرض إجابة المساعد باستخدام خاصية التدفق (Streaming)
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""    

        # إرسال السؤال للنموذج
        chunks = client.models.generate_content_stream(
            model=MODEL_ID,
            contents=prompt,
            config=config,
        )      

        for chunk in chunks:
            if chunk.text:
                full_response += chunk.text
                response_placeholder.markdown(full_response + "▌")
        response_placeholder.markdown(full_response)

    # إضافة إجابة المساعد للسجل
    st.session_state.messages.append({"role": "assistant", "content": full_response})