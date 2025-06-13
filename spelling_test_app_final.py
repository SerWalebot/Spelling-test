
import streamlit as st
import random
import time
import pandas as pd
from gtts import gTTS
import base64
from io import BytesIO
from datetime import datetime, timedelta

# ------------------ Configuration ------------------
WORDS = ["accommodate", "acknowledgment", "conscience", "conscientious", "embarrass",
         "exhilarate", "harass", "indispensable", "millennium", "noticeable",
         "occasionally", "occurrence", "possession", "recommend", "rhythm",
         "separate", "threshold", "twelfth", "vacuum", "weird"]

MAX_ATTEMPTS = 2
ATTEMPT_INTERVAL = timedelta(hours=1)
TEST_DURATION = 180  # 3 minutes in seconds
NUM_QUESTIONS = 10
LOG_FILE = "attempt_log.csv"

# ------------------ Utility Functions ------------------
def generate_audio(word):
    tts = gTTS(text=word, lang='en')
    fp = BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    b64 = base64.b64encode(fp.read()).decode()
    return f"data:audio/mp3;base64,{b64}"

def load_log():
    try:
        return pd.read_csv(LOG_FILE)
    except FileNotFoundError:
        return pd.DataFrame(columns=["Name", "Score", "TimeTaken", "Timestamp", "Incorrect"])

def save_log(name, score, time_taken, incorrect_words):
    log = load_log()
    new_entry = {
        "Name": name,
        "Score": score,
        "TimeTaken": f"{time_taken:.1f}s",
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Incorrect": "; ".join([f"{w} → {u}" for w, u in incorrect_words])
    }
    log = pd.concat([log, pd.DataFrame([new_entry])], ignore_index=True)
    log.to_csv(LOG_FILE, index=False)

def get_attempts(name):
    log = load_log()
    now = datetime.now()
    recent = log[(log["Name"] == name) & 
                 (pd.to_datetime(log["Timestamp"]) > now - ATTEMPT_INTERVAL)]
    return len(recent)

def feedback(score):
    if score >= 8:
        return "🎉 Excellent work! You're a spelling star!"
    elif score >= 5:
        return "🙂 Good effort! Keep practicing!"
    else:
        return "😢 Don't worry, try again and you'll improve!"

# ------------------ App Layout ------------------
st.set_page_config(page_title="Spelling Test", layout="centered")
st.markdown("<h1 style='text-align:center; color:#4CAF50;'>📝 Spelling Test</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>Welcome! You have 3 minutes to complete 10 spelling questions. Good luck! 🍀</p>", unsafe_allow_html=True)

# ------------------ Session State ------------------
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "words" not in st.session_state:
    st.session_state.words = random.sample(WORDS, NUM_QUESTIONS)
if "answers" not in st.session_state:
    st.session_state.answers = [""] * NUM_QUESTIONS
if "name" not in st.session_state:
    st.session_state.name = ""

# ------------------ Name Entry ------------------
if not st.session_state.name:
    name = st.text_input("Enter your name to begin:", key="name_input")
    if name:
        if get_attempts(name) >= MAX_ATTEMPTS:
            st.error("❌ You have reached the maximum of 2 attempts in the past hour.")
        else:
            st.session_state.name = name
            st.session_state.start_time = time.time()
            st.experimental_rerun()
    st.stop()

# ------------------ Timer ------------------
elapsed = time.time() - st.session_state.start_time
remaining = max(0, TEST_DURATION - int(elapsed))
minutes, seconds = divmod(remaining, 60)
st.markdown(f"<h4 style='color:#FF5722;'>⏱️ Time Remaining: {minutes:02d}:{seconds:02d}</h4>", unsafe_allow_html=True)

if remaining == 0 and not st.session_state.submitted:
    st.warning("⏰ Time's up! Submitting your answers...")
    st.session_state.submitted = True

# ------------------ Test Form ------------------
if not st.session_state.submitted:
    with st.form("spelling_test_form"):
        for i, word in enumerate(st.session_state.words):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.audio(generate_audio(word), format="audio/mp3")
            with col2:
                st.session_state.answers[i] = st.text_input(f"Word {i+1}", value=st.session_state.answers[i], key=f"word_{i}", disabled=st.session_state.submitted, label_visibility="collapsed", placeholder="Type the word you heard", help="Spellcheck is disabled", args=(), kwargs={}, type="default")
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state.submitted = True

# ------------------ Results ------------------
if st.session_state.submitted:
    correct = 0
    incorrect_words = []
    for i, word in enumerate(st.session_state.words):
        user_input = st.session_state.answers[i].strip().lower()
        if user_input == word.lower():
            correct += 1
        else:
            incorrect_words.append((word, user_input or "[blank]"))

    time_taken = time.time() - st.session_state.start_time
    save_log(st.session_state.name, correct, time_taken, incorrect_words)

    st.success(f"✅ Test completed! You scored {correct}/10 in {time_taken:.1f} seconds.")
    st.markdown(f"<h3 style='text-align:center;'>{feedback(correct)}</h3>", unsafe_allow_html=True)

    if incorrect_words:
        st.markdown("### ❌ Words you missed:")
        for correct_word, user_word in incorrect_words:
            st.markdown(f"- **{correct_word}** → *{user_word}*")

    st.markdown("---")
    st.markdown("### 🏆 Leaderboard (Top Scores)")
    log = load_log()
    top_scores = log.sort_values(by=["Score", "TimeTaken"], ascending=[False, True]).head(10)
    st.dataframe(top_scores[["Name", "Score", "TimeTaken", "Timestamp"]].reset_index(drop=True))
