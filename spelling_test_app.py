
import streamlit as st
import random
import time
import json
import os
from datetime import datetime, timedelta
from gtts import gTTS
import base64

# -------------------------------
# Configuration
# -------------------------------
WORD_LIST = [
    "accommodate", "acknowledgment", "argument", "calendar", "conscience",
    "conscientious", "conscious", "definitely", "discipline", "embarrass",
    "exaggerate", "existence", "foreign", "grateful", "guarantee",
    "harass", "humorous", "independent", "interrupt", "knowledge",
    "liaison", "maintenance", "millennium", "noticeable", "occasionally",
    "occurrence", "persistent", "personnel", "possession", "privilege"
]

LEADERBOARD_FILE = "leaderboard.json"
USER_HISTORY_FILE = "user_history.json"
NUM_QUESTIONS = 10
TIME_LIMIT = 60  # seconds

# -------------------------------
# Helper Functions
# -------------------------------
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def get_audio_base64(word):
    tts = gTTS(word)
    tts.save("temp.mp3")
    with open("temp.mp3", "rb") as audio_file:
        audio_bytes = audio_file.read()
    return base64.b64encode(audio_bytes).decode()

def update_leaderboard(name, score, duration):
    leaderboard = load_json(LEADERBOARD_FILE)
    leaderboard[name] = {"score": score, "time": duration, "timestamp": datetime.now().isoformat()}
    save_json(LEADERBOARD_FILE, leaderboard)

def can_take_test(name):
    history = load_json(USER_HISTORY_FILE)
    if name in history:
        last_attempt = datetime.fromisoformat(history[name])
        return datetime.now() - last_attempt > timedelta(hours=24)
    return True

def record_attempt(name):
    history = load_json(USER_HISTORY_FILE)
    history[name] = datetime.now().isoformat()
    save_json(USER_HISTORY_FILE, history)

# -------------------------------
# Streamlit UI
# -------------------------------
st.title("📝 Spelling Test for Customer Care Team")

name = st.text_input("Enter your full name")

if name:
    if not can_take_test(name):
        st.warning("⏳ You can only take the test once every 24 hours. Please try again later.")
        st.stop()

    if "start" not in st.session_state:
        st.session_state.start = False

    if not st.session_state.start:
        if st.button("Start Test"):
            st.session_state.start = True
            st.session_state.words = random.sample(WORD_LIST, NUM_QUESTIONS)
            st.session_state.answers = {}
            st.session_state.start_time = time.time()
    else:
        elapsed = time.time() - st.session_state.start_time
        remaining = TIME_LIMIT - int(elapsed)

        if remaining <= 0:
            st.warning("⏰ Time's up!")
            submitted = True
        else:
            st.info(f"⏱️ Time remaining: {remaining} seconds")
            submitted = st.button("Submit Answers")

        for i, word in enumerate(st.session_state.words):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.session_state.answers[word] = st.text_input(f"Spell word #{i+1}", key=f"word_{i}")
            with col2:
                audio_b64 = get_audio_base64(word)
                st.audio(f"data:audio/mp3;base64,{audio_b64}", format="audio/mp3")

        if submitted:
            score = sum(1 for word in st.session_state.words if st.session_state.answers.get(word, "").strip().lower() == word.lower())
            duration = int(time.time() - st.session_state.start_time)
            st.success(f"✅ You scored {score} out of {NUM_QUESTIONS} in {duration} seconds.")
            update_leaderboard(name, score, duration)
            record_attempt(name)
            st.session_state.start = False

# -------------------------------
# Leaderboard
# -------------------------------
st.subheader("🏆 Leaderboard")
leaderboard = load_json(LEADERBOARD_FILE)
if leaderboard:
    sorted_board = sorted(leaderboard.items(), key=lambda x: (-x[1]["score"], x[1]["time"]))
    for i, (user, data) in enumerate(sorted_board[:10], 1):
        st.write(f"{i}. {user} — {data['score']} pts in {data['time']}s")
else:
    st.write("No scores yet.")
