import streamlit as st
from openai import OpenAI
from io import BytesIO
import base64
import re
import os
from streamlit_mic_recorder import speech_to_text

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

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=OPENAI_API_KEY)

# ==========================================
# 3. 함수들 (OpenAI TTS 원어민 음성 적용)
# ==========================================
def load_lesson():
    try:
        with open("LSA Lesson.txt", "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "ERROR"

def speak(text):
    try:
        # 이모지나 특수문자 제거
        clean_text = re.sub(r'[^a-zA-Z0-9가-힣\s.,!?\'"]', '', text)
        
        # ★ OpenAI의 최고급 TTS 엔진으로 부드러운 원어민 목소리 생성
        # 추천 목소리: nova(부드러운 여성), shimmer(밝은 여성)
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova", 
            input=clean_text
        )
        
        audio_data = response.content
        
        # 브라우저 강제 재생 (autoplay)
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
# 4. 상태 관리 & 대화 초기화 (OpenAI GPT-4o-mini 적용)
# ==========================================
if "class_started" not in st.session_state:
    st.session_state.class_started = False

if "messages" not in st.session_state:
    lesson_content = load_lesson()
    
    if lesson_content != "ERROR":
        system_instruction = f"""
        당신은 LSA 영어 학원의 튜터 'Judy'입니다.
        아래 [학습 자료]의 내용으로만 수업하세요.
        [학습 자료] {lesson_content}
        [규칙] 1. 자료 내용만 사용. 2. 초등학생 대상: 쉽고 짧게. 3. 이모지 필수(읽을 땐 무시).
        """
        # OpenAI용 대화 기록 리스트 초기화 (System Prompt 주입)
        st.session_state.messages = [{"role": "system", "content": system_instruction}]
        st.session_state.lesson_content = lesson_content
    else:
        st.session_state.lesson_content = "ERROR"

# ==========================================
# 5. 메인 화면 로직
# ==========================================

# [상황 A] 아직 수업 시작 버튼을 안 눌렀을 때
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
                    # 첫 인사 요청 메시지 추가
                    st.session_state.messages.append({"role": "user", "content": "수업 시작해. 주제와 관련된 첫 인사를 건네줘."})
                    
                    # GPT-4o-mini 모델로 첫 인사 생성
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=st.session_state.messages
                    )
                    first_greeting_text = response.choices[0].message.content
                    
                    # 답변 기록 저장 및 첫 인사 세션 저장
                    st.session_state.messages.append({"role": "assistant", "content": first_greeting_text})
                    st.session_state.first_greeting = first_greeting_text
            st.rerun()

# [상황 B] 수업 시작 버튼을 누른 후 (채팅 화면)
else:
    # 1. 채팅 기록 표시
    for message in st.session_state.messages:
        # 시스템 프롬프트나 최초 트리거 대화는 화면에서 숨김
        if message["role"] == "system":
            continue
        if message["role"] == "user" and "수업 시작해" in message["content"]:
            continue
        
        role = "👩‍🏫 Judy" if message["role"] == "assistant" else "🧑‍💻 나"
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # ★ 첫 입장 시 원어민 인사말 자동 재생 ★
    if "first_greeting" in st.session_state:
        speak(st.session_state.first_greeting)
        del st.session_state.first_greeting

    # 2. 입력창 (마이크 + 텍스트)
    st.write("---")
    
    c1, c2 = st.columns([6, 2])
    with c2:
        voice_text = speech_to_text(language='en', start_prompt="🎙️ 음성으로 답하기", stop_prompt="⏹️ 완료하기", just_once=True, key='mic')

    if voice_text:
        st.info(f"🗣️ You said: **{voice_text}**")

    text_input = st.chat_input("Type your message here...")
    final_input = voice_text if voice_text else text_input

    if final_input:
        # 사용자 입력 표시 및 저장
        with st.chat_message("user"):
            st.write(final_input)
        st.session_state.messages.append({"role": "user", "content": final_input})
        
        # Judy 선생님 답변 생성 및 재생
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages
                )
                response_text = response.choices[0].message.content
                st.write(response_text)
                
                # 답변 기록 저장 및 음성 출력
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                speak(response_text)
