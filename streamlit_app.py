import streamlit as st
import requests
import json
from datetime import datetime
import random

st.set_page_config(page_title="LUCAS 리듬 자동화 대시보드", layout="wide")

st.title("LUCAS 업무 리듬 분석 & 자동화")
st.markdown("명령 → 감정 분석 → Slack/Notion 연동 → 자동 리포트")

if "log" not in st.session_state:
    st.session_state.log = []

def analyze_emotion(command):
    delay = round(len(command) * 0.1, 2)
    emotion = round(100 - delay * 25, 1)
    return delay, emotion

def send_slack_alert(message):
    webhook = st.secrets.get("SLACK_WEBHOOK_URL")
    if webhook:
        requests.post(webhook, json={"text": message})

def send_notion_log(command, score):
    token = st.secrets.get("NOTION_SECRET_TOKEN")
    db_id = st.secrets.get("NOTION_DATABASE_ID")
    if not token or not db_id:
        return
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    payload = {
        "parent": {"database_id": db_id},
        "properties": {
            "Name": {"title": [{"text": {"content": command}}]},
            "Emotion": {"rich_text": [{"text": {"content": f"{score}"}}]}
        }
    }
    requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload)

with st.form("lucas_command"):
    command = st.text_input("명령어 입력 (예: 'IR 피치덱 만들어줘')")
    submitted = st.form_submit_button("분석 및 자동화 실행")

    if submitted and command:
        delay, emotion = analyze_emotion(command)
        st.success(f"감정 점수: {emotion}/100 | 응답 지연 추정: {delay}s")
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "emotion_level": emotion
        }
        st.session_state.log.append(log_entry)

        # Trigger actions
        if emotion < 60:
            send_slack_alert(f"[LUCAS ALERT] 감정 점수 낮음: {emotion}/100
명령: {command}")
        send_notion_log(command, emotion)

st.subheader("최근 실행 로그")
st.json(st.session_state.log)

if st.session_state.log:
    st.subheader("감정 점수 추이")
    st.line_chart([x["emotion_level"] for x in st.session_state.log])