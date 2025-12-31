import streamlit as st
import random


def generate_assignments(names, seed):
    random.seed(seed)
    shuffled = names[:]
    random.shuffle(shuffled)

    assignments = {}
    for i in range(len(shuffled)):
        assignments[shuffled[i]] = shuffled[(i + 1) % len(shuffled)]

    return assignments


st.set_page_config(page_title="Secret Santa", page_icon="🎁")

st.title("🎁 Secret Santa")

# --- Session state initialization ---
if "names" not in st.session_state:
    st.session_state.names = []

if "assignments" not in st.session_state:
    st.session_state.assignments = {}

if "revealed" not in st.session_state:
    st.session_state.revealed = set()

if "locked" not in st.session_state:
    st.session_state.locked = False


# --- Setup phase ---
if not st.session_state.locked:
    st.subheader("Setup")

    seed = st.text_input("Seed eingeben")
    names_input = st.text_area(
        "Teilnehmer (ein Name pro Zeile)",
        height=200,
    )

    names = [n.strip() for n in names_input.splitlines() if n.strip()]

    if st.button("Start"):
        if len(names) < 2:
            st.error("Es werden mindestens zwei Teilnehmer benötigt")
        elif len(set(names)) != len(names):
            st.error("Namen müssen eindeutig sein")
        else:
            st.session_state.names = names
            st.session_state.assignments = generate_assignments(names, seed)
            st.session_state.revealed = set()
            st.session_state.locked = True
            st.success("Zuweisungen erstellt")


# --- Reveal phase ---
else:
    st.subheader("Zuweisung anzeigen")

    name = st.selectbox("Dein Name", st.session_state.names)

    if name in st.session_state.revealed:
        st.warning("Du hast deine Zuweisung bereits gesehen")
    else:
        if st.button("Zuweisung anzeigen"):
            recipient = st.session_state.assignments[name]
            st.success(f"{name}, du musst **{recipient}** etwas geben")
            st.session_state.revealed.add(name)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Reset"):
            st.session_state.revealed.clear()
            st.success("Zurückgesetzt – alle können erneut schauen")

    with col2:
        if st.button("Neustart"):
            st.session_state.clear()
            st.experimental_rerun()
