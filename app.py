import streamlit as st
from openai import OpenAI
from io import BytesIO
import base64
import re
import os
from streamlit_mic_recorder import mic_recorder

# ==========================================
# 1. 화면 설정 & 스타일
# ==========================================
try:
    st.set_page_config(page_title="LSA AI Tutor", page_icon="logo.png")
except:
    st.set_page_config(page_title="LSA AI Tutor", page_icon="🦁")

try:
    col_title1, col_title2 = st.columns([2, 7])
    with col_title1:
        st.image("logo.png", width=150)
    with col_title2:
        st.title("LSA LOD Speaking - Judy 선생님")
except:
    st.title("🦁 LSA LOD Speaking - Judy 선생님")

st.markdown(
    """
    <style>
    .stChatMessage p { font-size: 22px !important; line-height: 1.5 !important; }
    .stChatInput textarea { font-size: 18px !important; }
    div.stButton button { font-size: 18px !important; }
    .big-button {
        display: flex;
        justify-content: center;
        margin-top: 50px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# 2. OpenAI API 키 설정
# ==========================================
try:
    OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
except:
    st.error("OpenAI API 키가 없습니다. Streamlit Secrets에 OPENAI_API_KEY를 설정해주세요.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# ==========================================
# 3. 음성 재생 함수 (OpenAI TTS)
# ==========================================
def load_lesson():
    try:
        with open("LSA Lesson.txt", "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "ERROR"

def speak(text):
    try:
        clean_text = re.sub(r'[^a-zA-Z0-9가-힣\s.,!?\'"]', '', text)
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova", 
            input=clean_text
        )
        audio_data = response.content
        b64 = base64.b64encode(audio_data).decode()
        md = f"""
            <audio controls autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"오디오 오류: {e}")

# ==========================================
# 4. 상태 관리 및 영어 몰입형 페르소나 설정
# ==========================================
if "class_started" not in st.session_state:
    st.session_state.class_started = False

if "messages" not in st.session_state:
    lesson_content = load_lesson()
    
    if lesson_content != "ERROR":
        # ★ Judy 선생님의 영어 사용 비중을 극대화하고 한국어는 최소화하도록 튜닝
        system_instruction = f"""
        You are 'Judy', a friendly AI English tutor for elementary school students at LSA Academy.
        Lead the conversation based on the [Lesson Content] below.
        - [Lesson Content]: {lesson_content}

        [★ Crucial Rules for Language Usage]
        1. Default is 100% English: You must speak ONLY in English by default. 
           - Praise the student in English (e.g., "Great job! 🎉", "Perfect! You are right! 👍").
           - Do NOT translate the student's correct answers or your English responses into Korean. Keep the momentum in English.
        
        2. Strict Condition for Korean (As a Backup Only):
           - Rule A (Student uses Korean): If the student explicitly types or says something in Korean (e.g., "모르겠어요", "힌트 주세요"), reply warmly in Korean for just ONE sentence, then immediately guide them back to English. (e.g., "괜찮아, 선생님이 도와줄게! Let's try together. What is...?")
           - Rule B (Student is struggling in English): If the student tries to answer in English but is wrong or stuck, give a hint in simple English first. Only mix a tiny bit of Korean (like a single word translation) if absolutely necessary to help them understand. Do NOT explain long sentences in Korean.
        
        3. Simple & Short: Use short, clear, and easy sentences suitable for elementary schoolers (Maximum 2 sentences per response).
        
        4. Emojis: Use friendly emojis (✨, 💖, 👍, 😊) to encourage the student.
        """
        st.session_state.messages = [{"role": "system", "content": system_instruction}]
        st.session_state.lesson_content = lesson_content
    else:
        st.session_state.lesson_content = "ERROR"

# ==========================================
# 5. 메인 화면 로직
# ==========================================

if not st.session_state.class_started:
    st.write("---")
    st.subheader("👋 Welcome to League of Dreamtree AI Class!")
    st.write("Click the button below to meet Judy.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 수업 시작하기 (Enter Class)", use_container_width=True):
            st.session_state.class_started = True
            
            if st.session_state.lesson_content != "ERROR":
                with st.spinner("Judy 선생님이 오고 계십니다..."):
                    st.session_state.messages.append({"role": "user", "content": "수업 시작해. 아이에게 영어로 반갑게 첫 마디를 건네줘."})
                    
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=st.session_state.messages
                    )
                    first_greeting_text = response.choices[0].message.content
                    
                    st.session_state.messages.append({"role": "assistant", "content": first_greeting_text})
                    st.session_state.first_greeting = first_greeting_text
            st.rerun()

else:
    # 1. 채팅 기록 표시
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue
        if message["role"] == "user" and "수업 시작해" in message["content"]:
            continue
        
        role = "👩‍🏫 Judy" if message["role"] == "assistant" else "🧑‍💻 나"
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # 첫 입장 시 인사말 자동 재생
    if "first_greeting" in st.session_state:
        speak(st.session_state.first_greeting)
        del st.session_state.first_greeting

    # 2. 입력창 (마이크 + 텍스트)
    st.write("---")
    
    c1, c2 = st.columns([6, 2])
    with c2:
        audio_data = mic_recorder(start_prompt="🎙️ 누르고 말하기", stop_prompt="⏹️ 완료 (전송)", just_once=True, key='mic')

    voice_text = ""
    if audio_data:
        with st.spinner("Judy 선생님이 음성을 듣고 있어요... 🎧"):
            try:
                audio_bytes = BytesIO(audio_data['bytes'])
                audio_bytes.name = "audio.mp3"
                
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_bytes
                )
                voice_text = transcription.text
            except Exception as e:
                st.error(f"음성 인식 오류가 발생했습니다: {e}")

    if voice_text:
        st.info(f"🗣️ You said: **{voice_text}**")

    text_input = st.chat_input("Judy 선생님과 대화해보세요!")
    final_input = voice_text if voice_text else text_input

    if final_input:
        with st.chat_message("user"):
            st.write(final_input)
        st.session_state.messages.append({"role": "user", "content": final_input})
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages
                )
                response_text = response.choices[0].message.content
                st.write(response_text)
                
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                speak(response_text)
