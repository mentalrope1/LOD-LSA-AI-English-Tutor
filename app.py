import streamlit as st
from openai import OpenAI
from io import BytesIO
import base64
import re
import os
# ★ 변경: speech_to_text 대신 raw 녹음용 mic_recorder를 가져옵니다.
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
# 4. 상태 관리 및 유연한 교육용 페르소나 설정
# ==========================================
if "class_started" not in st.session_state:
    st.session_state.class_started = False

if "messages" not in st.session_state:
    lesson_content = load_lesson()
    
    if lesson_content != "ERROR":
        system_instruction = f"""
        당신은 초등학생을 대상으로 하는 LSA 영어 학원의 대화형 AI 튜터 'Judy'입니다.
        정답만 체크하는 딱딱한 로봇처럼 굴지 말고, 아이들이 편안하고 재미있게 대화할 수 있도록 극도로 유연하고 따뜻하게 반응하세요.

        [기본 미션 및 학습 자료]
        - 아래 [학습 자료]의 내용을 기반으로 대화를 리드하되, 상황에 맞게 유동적으로 대화하세요.
        - [학습 자료]: {lesson_content}

        [★ 핵심 지침: 유연한 소통 및 유도법]
        1. 한국어 사용에 대한 포용력: 학생이 음성이나 타자로 한국어로 말하거나 질문하면 절대 밀어내지 마세요. 
           반드시 한국어로 친절하게 맞장구를 치거나 설명해 준 뒤, "이번에는 선생님이 한국어로 설명해 주지만, 다음에는 영어로 같이 말해보기 약속! 😉" 과 같은 부드러운 멘트를 남기세요. 그리고 항상 마지막은 아이가 대답하기 아주 쉬운 영어 질문이나 문장으로 끝마쳐야 합니다.
        
        2. 단계별 힌트 제공 (스캐폴딩): 학생이 대답을 어려워하거나, 문법이 틀리거나, 침묵할 때는 다짜고짜 정답을 주지 마세요. 
           "괜찮아, 할 수 있어! 👍 이 단어는 'A'로 시작해~" 혹은 단어의 뜻을 한국어로 슬쩍 알려주는 등 쉬운 힌트를 주어 스스로 영어로 말할 수 있도록 유도하세요.
        
        3. 눈높이 맞춤: 상대는 초등학생입니다. 한 번에 길고 복잡한 문장을 쓰지 마세요. 명확하고 짧은 문장(최대 2~3문장)으로 끊어서 대화하세요.
        
        4. 친근한 어조: 성인 대화가 아니므로 이모지(✨, 💖, 👍, 😮 등)를 풍부하게 사용하여 칭찬과 격려를 아끼지 마세요.
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
                    st.session_state.messages.append({"role": "user", "content": "수업 시작해. 아이에게 반갑게 인사하며 첫 마디를 건네줘."})
                    
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
        # ★ [수정] OpenAI Whisper AI 음성 인식을 지원하는 마이크 버튼으로 교체
        audio_data = mic_recorder(start_prompt="🎙️ 누르고 말하기", stop_prompt="⏹️ 완료 (전송)", just_once=True, key='mic')

    # 오디오 데이터가 들어오면 OpenAI Whisper로 텍스트 변환 진행
    voice_text = ""
    if audio_data:
        with st.spinner("Judy 선생님이 음성을 듣고 있어요... 🎧"):
            try:
                audio_bytes = BytesIO(audio_data['bytes'])
                audio_bytes.name = "audio.mp3"  # Whisper 인식용 가상 파일명 설정
                
                # OpenAI Whisper API 호출 (언어 자동 감지)
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_bytes
                )
                voice_text = transcription.text
            except Exception as e:
                st.error(f"음성 인식 오류가 발생했습니다: {e}")

    if voice_text:
        st.info(f"🗣️ You said: **{voice_text}**")

    text_input = st.chat_input("Judy 선생님과 대화해보세요! (한국어/영어 모두 가능)")
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
