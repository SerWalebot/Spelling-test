
import streamlit as st
import random
import json
import os

# Predefined list of words for the spelling test
WORD_LIST = [
    "accommodate", "acknowledgment", "conscientious", "entrepreneur", "guarantee",
    "liaison", "maintenance", "miscellaneous", "negotiate", "occasionally",
    "perseverance", "recommend", "rhythm", "schedule", "threshold",
    "unforeseen", "vacuum", "withhold", "zealous", "bureaucracy"
]

LEADERBOARD_FILE = "leaderboard.json"

def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, "r") as f:
            return json.load(f)
    return []

def save_leaderboard(leaderboard):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(leaderboard, f, indent=4)

def update_leaderboard(name, role, score):
    leaderboard = load_leaderboard()
    leaderboard.append({"name": name, "role": role, "score": score})
    leaderboard = sorted(leaderboard, key=lambda x: x["score"], reverse=True)[:10]
    save_leaderboard(leaderboard)

def main():
    st.title("📚 Spelling Test for Customer Care Team")

    name = st.text_input("Enter your name:")
    role = st.selectbox("Select your role:", ["Agent", "Leader"])

    if name and role:
        if "questions" not in st.session_state:
            st.session_state.questions = random.sample(WORD_LIST, 10)
            st.session_state.answers = [""] * 10
            st.session_state.submitted = False

        st.write("### Spell the following words:")

        for i, word in enumerate(st.session_state.questions):
            st.session_state.answers[i] = st.text_input(f"Word {i+1}:", key=f"word_{i}")

        if st.button("Submit"):
            score = sum(
                1 for i, word in enumerate(st.session_state.questions)
                if st.session_state.answers[i].strip().lower() == word.lower()
            )
            st.session_state.submitted = True
            update_leaderboard(name, role, score)
            st.success(f"✅ You scored {score} out of 10!")

        if st.session_state.submitted:
            st.write("### 🏆 Leaderboard (Top 10)")
            leaderboard = load_leaderboard()
            for entry in leaderboard:
                st.write(f"{entry['name']} ({entry['role']}): {entry['score']}")

if __name__ == "__main__":
    main()
