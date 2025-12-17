import streamlit as st
import google.generativeai as genai
from gtts import gTTS
from io import BytesIO
import base64
import re
import os
from streamlit_mic_recorder import speech_to_text

# ==========================================
# 1. 화면 설정 & 스타일
# ==========================================
# ★ [수정 1] 브라우저 탭 아이콘을 이미지 파일로 변경
# (반드시 'logo.png' 파일이 같은 폴더에 있어야 합니다)
try:
    st.set_page_config(page_title="LSA AI Tutor", page_icon="logo.png")
except:
    # 혹시 파일이 없으면 그냥 이모지로 표시 (에러 방지)
    st.set_page_config(page_title="LSA AI Tutor", page_icon="🦁")

# ★ [수정 2] 메인 타이틀 옆에 로고 이미지 배치
# 기존 st.title("🦁...") 코드를 아래 4줄로 교체
try:
    col_title1, col_title2 = st.columns([2, 7])
    with col_title1:
        st.image("logo.png", width=150) # 이미지 크기 조절 가능
    with col_title2:
        st.title("LSA 영어 회화 - Judy 선생님") # 🦁 이모지 삭제
except:
    # 파일이 없을 경우 대비
    st.title("🦁 LSA 영어 회화 - Judy 선생님")

st.markdown(
    """
    <style>
    .stChatMessage p { font-size: 22px !important; line-height: 1.5 !important; }
    .stChatInput textarea { font-size: 18px !important; }
    div.stButton button { font-size: 18px !important; }
    
    /* 입장 버튼 스타일 꾸미기 */
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
# 2. API 키 설정 (보안 적용)
# ==========================================
# 완전히 안전한 버전
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("API 키가 없습니다. Secrets를 설정해주세요.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# ==========================================
# 3. 함수들
# ==========================================
def load_lesson():
    try:
        with open("LSA Lesson.txt", "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return "ERROR"

def speak(text):
    try:
        # 이모지 제거
        clean_text = re.sub(r'[^a-zA-Z0-9가-힣\s.,!?\'"]', '', text)
        tts = gTTS(text=clean_text, lang='en', slow=False)
        audio_bytes = BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_data = audio_bytes.getvalue()
        
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
# 4. 상태 관리 (수업 시작 여부 체크)
# ==========================================
if "class_started" not in st.session_state:
    st.session_state.class_started = False

if "chat_session" not in st.session_state:
    lesson_content = load_lesson()
    
    # 모델 설정
    if lesson_content != "ERROR":
        system_instruction = f"""
        당신은 LSA 영어 학원의 튜터 'Judy'입니다.
        아래 [학습 자료]의 내용으로만 수업하세요.
        [학습 자료] {lesson_content}
        [규칙] 1. 자료 내용만 사용. 2. 초등학생 대상: 쉽고 짧게. 3. 이모지 필수(읽을 땐 무시).
        """
        model = genai.GenerativeModel(model_name="models/gemini-flash-latest", system_instruction=system_instruction)
        st.session_state.chat_session = model.start_chat(history=[])
        st.session_state.lesson_content = lesson_content
    else:
        st.session_state.lesson_content = "ERROR"

# ==========================================
# 5. 메인 화면 로직 (입장 버튼 vs 채팅창)
# ==========================================

# [상황 A] 아직 수업 시작 버튼을 안 눌렀을 때
if not st.session_state.class_started:
    st.write("---")
    st.subheader("👋 Welcome to League of Dreamtree AI Class!")
    st.write("Click the button below to meet Judy.")
    
    # 가운데 정렬을 위한 컬럼 트릭
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # 이 버튼을 누르는 순간 '클릭'으로 인정되어 오디오 권한이 풀림!
        if st.button("🚀 수업 시작하기 (Enter Class)", use_container_width=True):
            st.session_state.class_started = True
            
            # 버튼 누르자마자 첫 인사 생성 & 재생
            if st.session_state.lesson_content != "ERROR":
                with st.spinner("Judy 선생님이 오고 계십니다..."):
                    first_msg = st.session_state.chat_session.send_message("수업 시작해. 주제와 관련된 첫 인사를 건네줘.")
                    # 여기서 생성된 첫 인사를 저장해둠
                    st.session_state.first_greeting = first_msg.text
            st.rerun()

# [상황 B] 수업 시작 버튼을 누른 후 (채팅 화면)
else:
    # 1. 채팅 기록 표시
    for i, message in enumerate(st.session_state.chat_session.history):
        if message.role == "user" and "수업 시작해" in message.parts[0].text:
            continue
        
        role = "👩‍🏫 Judy" if message.role == "model" else "🧑‍💻 나"
        with st.chat_message(message.role):
            st.write(message.parts[0].text)

    # ★ 첫 입장 시 인사말 자동 재생 ★
    # (방금 버튼을 클릭하고 들어왔으므로 브라우저가 소리를 허용해줌)
    if "first_greeting" in st.session_state:
        # 화면에 보이지 않는 오디오 플레이어를 심어서 소리만 나게 함
        speak(st.session_state.first_greeting)
        # 한 번 재생했으니 삭제 (새로고침 시 중복 재생 방지)
        del st.session_state.first_greeting

    # 2. 입력창 (마이크 + 텍스트)
    st.write("---")
    
    # 마이크 버튼 배치
    # [수정] 글자가 길어지니까 버튼 공간을 1 -> 2로 늘려줍니다.
    c1, c2 = st.columns([6, 2])
    with c2:
        voice_text = speech_to_text(language='en', start_prompt="🎙️ 음성으로 답하기", stop_prompt="⏹️ 완료하기", just_once=True, key='mic')

    if voice_text:
        st.info(f"🗣️ You said: **{voice_text}**")

    text_input = st.chat_input("Type your message here...")
    final_input = voice_text if voice_text else text_input

    if final_input:
        with st.chat_message("user"):
            st.write(final_input)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.chat_session.send_message(final_input)
                st.write(response.text)

                speak(response.text)
