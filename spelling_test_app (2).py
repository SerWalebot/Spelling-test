
import streamlit as st
import random
import time
import pandas as pd
from gtts import gTTS
import base64
from io import BytesIO
from datetime import datetime, timedelta

# ----------------------------
# Configuration
# ----------------------------
WORDS = [
    "accommodate", "acknowledgment", "acquaintance", "aesthetic", "amateur",
    "apparent", "argument", "balloon", "beginning", "believe", "calendar",
    "category", "cemetery", "changeable", "collectible", "column", "committed",
    "conscience", "conscious", "consensus", "daiquiri", "definitely", "discipline",
    "drunkenness", "embarrass", "equipment", "exhilarate", "existence", "experience",
    "fiery", "foreign", "gauge", "grateful", "guarantee", "harass", "height",
    "hierarchy", "humorous", "ignorance", "immediate", "independent", "interrupt",
    "irresistible", "knowledge", "leisure", "library", "lightning", "maintenance",
    "maneuver", "medieval", "millennium", "miniature", "mischievous", "neighbor",
    "noticeable", "occasion", "occurrence", "pastime", "perseverance", "personnel",
    "playwright", "possession", "precede", "principal", "privilege", "questionnaire",
    "recommend", "referred", "relevant", "restaurant", "rhythm", "schedule",
    "separate", "sergeant", "supersede", "surprise", "tomorrow", "twelfth",
    "tyranny", "until", "vacuum", "weather", "weird", "wherever", "withhold"
]

NUM_QUESTIONS = 10
TIME_LIMIT = 5 * 60  # 5 minutes
ATTEMPT_INTERVAL = timedelta(hours=1)
LOG_FILE = "attempt_log.csv"

# ----------------------------
# Utility Functions
# ----------------------------
def generate_audio(word):
    tts = gTTS(text=word, lang='en')
    fp = BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    audio_bytes = fp.read()
    return audio_bytes

def get_audio_download_link(audio_bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    return f"data:audio/mp3;base64,{b64}"

def load_log():
    try:
        return pd.read_csv(LOG_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Name", "Score", "Timestamp"])

def save_log(log_df):
    log_df.to_csv(LOG_FILE, index=False)

def can_attempt(name, log_df):
    now = datetime.now()
    user_logs = log_df[log_df["Name"] == name]
    recent_attempts = user_logs[pd.to_datetime(user_logs["Timestamp"]) > now - ATTEMPT_INTERVAL]
    return len(recent_attempts) < 2

# ----------------------------
# Main App
# ----------------------------
st.set_page_config(page_title="Spelling Test", layout="centered")
st.title("📝 Spelling Test")
st.markdown("Welcome to the spelling test! You have 5 minutes to complete 10 questions. Click the 🔊 button to hear each word.")

log_df = load_log()

# Admin dashboard
with st.sidebar:
    st.header("🔐 Admin Dashboard")
    password = st.text_input("Enter admin password", type="password")
    if password == "admin123":
        st.success("Access granted")
        date_filter = st.date_input("Filter by date", value=None)
        if date_filter:
            filtered = log_df[pd.to_datetime(log_df["Timestamp"]).dt.date == date_filter]
        else:
            filtered = log_df
        st.dataframe(filtered)
        st.download_button("📥 Download CSV", filtered.to_csv(index=False), file_name="leaderboard.csv")

# User input
name = st.text_input("Enter your full name to begin:")

if name:
    if not can_attempt(name, log_df):
        st.warning("You have reached the maximum of 2 attempts in the past hour. Please try again later.")
        st.stop()

    if "start_time" not in st.session_state:
        st.session_state.start_time = time.time()
        st.session_state.words = random.sample(WORDS, NUM_QUESTIONS)
        st.session_state.answers = [""] * NUM_QUESTIONS
        st.session_state.submitted = False

    elapsed = time.time() - st.session_state.start_time
    remaining = max(0, TIME_LIMIT - int(elapsed))
    minutes, seconds = divmod(remaining, 60)
    st.info(f"⏱️ Time remaining: {minutes:02d}:{seconds:02d}")

    if remaining == 0:
        st.warning("Time is up! Please submit your answers.")
        st.session_state.submitted = True

    # Display questions
    for i, word in enumerate(st.session_state.words):
        col1, col2 = st.columns([1, 5])
        with col1:
            audio_bytes = generate_audio(word)
            st.audio(audio_bytes, format="audio/mp3")
        with col2:
            st.session_state.answers[i] = st.text_input(f"Word {i+1}", value=st.session_state.answers[i])

    if st.button("Submit") or st.session_state.submitted:
        score = sum([1 for i in range(NUM_QUESTIONS) if st.session_state.answers[i].strip().lower() == st.session_state.words[i].lower()])
        st.success(f"✅ You scored {score} out of {NUM_QUESTIONS}")
        new_entry = pd.DataFrame([{
            "Name": name,
            "Score": score,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        log_df = pd.concat([log_df, new_entry], ignore_index=True)
        save_log(log_df)
        st.session_state.submitted = True

        # Leaderboard
        st.markdown("### 🏆 Leaderboard")
        leaderboard = log_df.groupby("Name")["Score"].max().reset_index().sort_values(by="Score", ascending=False)
        st.dataframe(leaderboard)
