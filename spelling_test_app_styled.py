
import streamlit as st
import pandas as pd
import random
import time
from gtts import gTTS
import base64
from io import BytesIO
from datetime import datetime, timedelta

# ----------------- CONFIGURATION -----------------
st.set_page_config(page_title="Spelling Test", layout="centered")

# ----------------- STYLES -----------------
st.markdown("""
    <style>
        body {
            background-color: #f0f8ff;
        }
        .main {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 2rem;
        }
        .stTextInput > div > div > input {
            border-radius: 10px;
            padding: 0.5rem;
            font-size: 1rem;
        }
        .stButton > button {
            border-radius: 10px;
            background-color: #4CAF50;
            color: white;
            font-size: 1rem;
            padding: 0.5rem 1rem;
        }
        .timer {
            font-size: 1.5rem;
            font-weight: bold;
            color: #ff4500;
        }
        .correct {
            color: green;
            font-weight: bold;
        }
        .incorrect {
            color: red;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# ----------------- UTILITY FUNCTIONS -----------------
def generate_words(n=10):
    word_list = ["accommodate", "rhythm", "conscience", "embarrass", "maintenance",
                 "pronunciation", "supersede", "threshold", "weird", "recommend",
                 "occasionally", "existence", "perseverance", "questionnaire", "liaison"]
    return random.sample(word_list, n)

def text_to_speech(word):
    tts = gTTS(text=word, lang='en')
    fp = BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    audio_bytes = fp.read()
    b64 = base64.b64encode(audio_bytes).decode()
    audio_html = f'<audio autoplay controls><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    return audio_html

def load_log():
    try:
        return pd.read_csv("attempt_log.csv")
    except:
        return pd.DataFrame(columns=["Name", "Score", "Date", "Time"])

def save_log(log_df):
    log_df.to_csv("attempt_log.csv", index=False)

def can_attempt(name, log_df):
    now = datetime.now()
    recent_attempts = log_df[(log_df["Name"] == name) & 
                             (pd.to_datetime(log_df["Date"] + " " + log_df["Time"]) > now - timedelta(hours=1))]
    return len(recent_attempts) < 2

# ----------------- MAIN APP -----------------
st.markdown("<h1 style='text-align: center; color: #2e8b57;'>📝 Welcome to the Spelling Test</h1>", unsafe_allow_html=True)

name = st.text_input("Enter your name to begin:")

if name:
    log_df = load_log()
    if can_attempt(name, log_df):
        if "start_time" not in st.session_state:
            st.session_state.start_time = time.time()
            st.session_state.words = generate_words()
            st.session_state.answers = []
            st.session_state.score = 0
            st.session_state.current = 0

        elapsed = int(time.time() - st.session_state.start_time)
        remaining = max(0, 300 - elapsed)
        minutes, seconds = divmod(remaining, 60)
        st.markdown(f"<div class='timer'>⏱️ Time Left: {minutes:02d}:{seconds:02d}</div>", unsafe_allow_html=True)

        if remaining == 0:
            st.warning("⏰ Time's up!")
            st.session_state.current = len(st.session_state.words)

        if st.session_state.current < len(st.session_state.words):
            word = st.session_state.words[st.session_state.current]
            st.markdown("### Listen to the word:")
            st.markdown(text_to_speech(word), unsafe_allow_html=True)
            user_input = st.text_input("Type the word you heard:", key=f"input_{st.session_state.current}")
            if st.button("Submit"):
                correct = user_input.strip().lower() == word.lower()
                st.session_state.answers.append((word, user_input, correct))
                if correct:
                    st.success("✅ Correct!", icon="✅")
                    st.session_state.score += 1
                else:
                    st.error(f"❌ Incorrect. The correct spelling is: {word}", icon="❌")
                st.session_state.current += 1
                st.experimental_rerun()
        else:
            st.success(f"🎉 Test completed! Your score: {st.session_state.score}/10")
            now = datetime.now()
            log_df = log_df.append({
                "Name": name,
                "Score": st.session_state.score,
                "Date": now.strftime("%Y-%m-%d"),
                "Time": now.strftime("%H:%M:%S")
            }, ignore_index=True)
            save_log(log_df)
            st.balloons()
    else:
        st.warning("⚠️ You have reached the maximum of 2 attempts in the last hour. Please try again later.")

# ----------------- LEADERBOARD -----------------
st.markdown("---")
st.markdown("## 🏆 Leaderboard")
log_df = load_log()
leaderboard = log_df.groupby("Name")["Score"].max().reset_index().sort_values(by="Score", ascending=False).head(10)
st.dataframe(leaderboard)

# ----------------- ADMIN DASHBOARD -----------------
with st.expander("🔐 Admin Dashboard"):
    st.markdown("### 📅 Filter by Date")
    date_filter = st.date_input("Select date to filter logs", value=None)
    if date_filter:
        filtered = log_df[log_df["Date"] == date_filter.strftime("%Y-%m-%d")]
    else:
        filtered = log_df
    st.dataframe(filtered)

    csv = filtered.to_csv(index=False).encode()
    st.download_button("📥 Download CSV", csv, "attempt_log.csv", "text/csv")
