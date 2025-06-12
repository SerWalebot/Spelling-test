
import streamlit as st
import random
import time
import json
import os
from datetime import datetime, timedelta
from gtts import gTTS
from io import BytesIO

# Constants
WORD_LIST = [
    "accommodate", "acknowledgment", "argument", "calendar", "conscience",
    "conscientious", "conscious", "definitely", "discipline", "embarrass",
    "exaggerate", "existence", "foreign", "grateful", "guarantee",
    "harass", "humorous", "independent", "interrupt", "knowledge",
    "liaison", "maintenance", "millennium", "noticeable", "occasionally",
    "occurrence", "persistent", "pharaoh", "possession", "privilege"
]
LEADERBOARD_FILE = "leaderboard.json"
ATTEMPT_LOG_FILE = "attempt_log.json"
ADMIN_PASSWORD = "admin123"
TEST_DURATION = 180  # seconds
RETRY_INTERVAL = timedelta(hours=3)

# Load leaderboard
def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, "r") as f:
            return json.load(f)
    return []

# Save leaderboard
def save_leaderboard(data):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Load attempt log
def load_attempt_log():
    if os.path.exists(ATTEMPT_LOG_FILE):
        with open(ATTEMPT_LOG_FILE, "r") as f:
            return json.load(f)
    return {}

# Save attempt log
def save_attempt_log(data):
    with open(ATTEMPT_LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Text-to-speech audio
def get_tts_audio(word):
    tts = gTTS(text=word, lang='en')
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    return mp3_fp

# Main app
def main():
    st.title("📝 Spelling Test for Customer Care Team")

    menu = st.sidebar.selectbox("Choose View", ["Take Test", "Admin Dashboard"])

    if menu == "Take Test":
        name = st.text_input("Enter your full name")
        role = st.selectbox("Select your role", ["Agent", "Leader"])

        if name:
            attempt_log = load_attempt_log()
            now = datetime.now()
            last_attempt = attempt_log.get(name)

            if last_attempt:
                last_time = datetime.strptime(last_attempt, "%Y-%m-%d %H:%M:%S")
                if now - last_time < RETRY_INTERVAL:
                    remaining = RETRY_INTERVAL - (now - last_time)
                    st.warning(f"You can take the test again in {str(remaining).split('.')[0]}")
                    return

            if st.button("Start Test"):
                st.session_state["start_time"] = time.time()
                st.session_state["words"] = random.sample(WORD_LIST, 10)
                st.session_state["answers"] = {}
                st.session_state["current_index"] = 0
                st.session_state["name"] = name
                st.session_state["role"] = role
                st.session_state["test_started"] = True

        if st.session_state.get("test_started", False):
            elapsed = time.time() - st.session_state["start_time"]
            remaining_time = TEST_DURATION - int(elapsed)
            if remaining_time <= 0:
                st.warning("⏰ Time's up!")
                score = sum(1 for i, word in enumerate(st.session_state["words"])
                            if st.session_state["answers"].get(i, "").strip().lower() == word.lower())
                duration = int(elapsed)
                leaderboard = load_leaderboard()
                leaderboard.append({
                    "name": st.session_state["name"],
                    "role": st.session_state["role"],
                    "score": score,
                    "time": duration,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                leaderboard = sorted(leaderboard, key=lambda x: (-x["score"], x["time"]))[:10]
                save_leaderboard(leaderboard)

                attempt_log = load_attempt_log()
                attempt_log[st.session_state["name"]] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_attempt_log(attempt_log)

                st.success(f"✅ Test completed! Your score: {score}/10")
                st.balloons()
                st.session_state["test_started"] = False
                return

            st.info(f"⏳ Time remaining: {remaining_time} seconds")

            idx = st.session_state["current_index"]
            if idx < 10:
                word = st.session_state["words"][idx]
                st.subheader(f"Question {idx+1} of 10")

                if st.button("🔊 Hear Word"):
                    audio = get_tts_audio(word)
                    st.audio(audio, format="audio/mp3")

                answer = st.text_input("Type the spelling here:", key=f"answer_{idx}")
                if st.button("Next"):
                    st.session_state["answers"][idx] = answer
                    st.session_state["current_index"] += 1
            else:
                st.warning("Click 'Next' to proceed or wait for time to expire.")

    elif menu == "Admin Dashboard":
        password = st.text_input("Enter admin password", type="password")
        if password == ADMIN_PASSWORD:
            st.success("Access granted ✅")
            leaderboard = load_leaderboard()
            st.subheader("🏆 Leaderboard (Top 10)")
            for entry in leaderboard:
                st.write(f"{entry['name']} ({entry['role']}): {entry['score']}/10 in {entry['time']}s on {entry['timestamp']}")

            st.subheader("📋 Attempt Log")
            attempt_log = load_attempt_log()
            for user, timestamp in attempt_log.items():
                st.write(f"{user} - Last attempt: {timestamp}")
        else:
            st.warning("Incorrect password ❌")

if __name__ == "__main__":
    main()
