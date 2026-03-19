from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from openai import OpenAI
import speech_recognition as sr
import tempfile, os, json
from datetime import datetime

client = OpenAI()


def stt() -> str:
    os.makedirs("stt", exist_ok=True)

    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        audio = recognizer.listen(source)

    text = recognizer.recognize_google(audio, language="ko-KR")

    with open(f"stt/{text}.wav", "wb") as f:
        f.write(audio.get_wav_data())
    
    return text

def tts(text: str, input_text: str):
    os.makedirs("tts", exist_ok=True)

    file_path = f"tts/{input_text}(대답).mp3"

    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="shimmer",
        input=text,
    ) as response:
        response.stream_to_file(file_path)

    with open(file_path, "rb") as f:
        st.audio(f.read(), format="audio/mp3")

situation_ex = {
    "남자친구와 싸운 후": "남자친구와 방금 싸운 직후의 냉랭한 상황",
    "남자친구와 평상시 대화": "남자친구와 일상적으로 대화하는 평화로운 상황",
    "친구들과 노는 중": "친한 친구들과 함께 신나게 놀고 있는 상황",
    "가족과 식사 중": "가족과 함께 식사하며 대화하는 상황",
    "직장/학교에서 스트레스받은 후": "직장이나 학교에서 힘든 일이 있었던 상황",
    "기분 좋고 설레는 날": "무언가 좋은 일이 생겨 기분이 들뜬 상황",
    "지루하고 무료한 날": "딱히 할 일 없이 무기력하고 심심한 상황",
}
 
target_ex = {
    "남자친구": "남자친구에게 하는 말",
    "남사친 (남자사람친구)": "남자사람친구에게 하는 말",
    "여자친구 (친구)": "여자친구(동성 친한 친구)에게 하는 말",
    "가족": "가족에게 하는 말",
    "직장 동료 / 선배": "직장 동료나 선배에게 하는 말",
    "단톡방 (여러 명)": "단체 카카오톡 채팅방에서 여러 명에게 하는 말",
}

import json


def translate(user_text: str, situation: str, target: str) -> dict:
 
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        max_tokens=1000,
        messages=[
            {
                "role": "system",
                "content": f"""
                당신은 '여자어 번역기'입니다. 여자가 하는 말의 진짜 숨겨진 의도를 해석해주세요.
 
                [현재 상황]: {situation_ex[situation]}
                [말하는 대상]: {target_ex[target]}

                위 상황과 대상을 반드시 반영하여 해석하세요. 같은 말이라도 상황과 대상에 따라 전혀 다른 의미를 가집니다.

                반드시 아래 JSON 형식으로만 답하세요. 코드블록 없이 순수 JSON만:
                {{
                  "translation": "진짜 의미 설명 (2~3문장, 상황과 대상을 반영한 구체적 해석)",
                  "points": ["포인트1", "포인트2", "포인트3"]
                }}
                """
            },
            {
                "role": "user",
                "content": f'다음 말을 여자어로 번역해줘: "{user_text}"'
            }
        ]
    )
    raw = response.choices[0].message.content.strip().replace("```json", "").replace("```", "")
    return json.loads(raw)


# user_text = "나중에 연락해"
# situation = "남자친구와 싸운 후"
# target    = "남자친구"

# result = translate(user_text, situation, target)

# print("원문:", user_text)
# print("상황:", situation)
# print("대상:", target)
# print()
# print("진짜 의미:")
# print(result["translation"])
# print()
# print("숨겨진 포인트:")
# for i, point in enumerate(result["points"], 1):
#     print(f"  {i}. {point}")

if "stt_result" not in st.session_state:
    st.session_state.stt_result = ""
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.title("여자어 번역기")
st.divider()

col1, col2 = st.columns(2)
with col1:
    situation = st.selectbox("현재 상황", list(situation_ex.keys())) 
with col2:
    target = st.selectbox("현재 상황", list(target_ex.keys()))

st.divider()

audio_value = st.audio_input("버튼을 눌러 말해보세요")

# 음성 입력 (STT)
if audio_value:
    with st.spinner("음성 인식 중..."):
        recognized = stt(audio_value.getvalue())
    if recognized:
        st.session_state.stt_result = recognized
        st.rerun()
    else:
        st.warning("음성을 인식하지 못했습니다. 다시 시도해주세요.")

# 텍스트 입력 
user_text = st.text_input(
    "텍스트 입력 / 수정",
    value = st.session_state.stt_result
)

# 번역, 초기화 버튼
col_btn1, col_btn2 = st.columns([4,1])
with col_btn1:
    translate_btn = st.button(
        "여자어 해석하기",
        disabled=not bool(user_text.strip()),
        use_container_width=True
    )
with col_btn2:
    if st.button("초기화", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.stt_result = ""
        st.rerun()

# 번역 실행
if translate_btn and user_text.strip():
    with st.spinner("여자어 해석 중..."):
        result = translate(user_text.strip(), situation, target)
        st.session_state.chat_history.append({
            "user" : user_text.strip(),
            "result" : result,
            "situation" : situation,
            "target" : target
        })
        st.session_state.stt_result = ""
        tts(result["translation"], user_text.strip())

# 채팅 내역 출력 
if st.session_state.chat_history:
    st.divider()
    st.subheader("대화 내역")

    for entry in reversed(st.session_state.chat_history):
        r = entry["result"]

        st.caption(f'{entry["situation"]} | {entry["target"]} ')

        with st.chat_message("assistant"):
            st.write(r["translation"])
            for point in r.get("points",[]):
                st.markdown(f"- {point}")

        st.divider()

