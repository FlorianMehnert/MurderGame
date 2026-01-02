import enum

import streamlit as st
import random
from streamlit_local_storage import LocalStorage


def generate_assignments(names, seed):
    random.seed(seed)
    shuffled = names[:]
    random.shuffle(shuffled)

    assignments = {}
    for i in range(len(shuffled)):
        assignments[shuffled[i]] = shuffled[(i + 1) % len(shuffled)]

    return assignments

class button_text(enum.Enum):
    setup = "Zuweisungen erstellen"
    reveal = "Zuweisung anzeigen"


if __name__ == '__main__':
    st.set_page_config(page_title="Das Mörder Spiel", page_icon="🥷")

    local_storage = LocalStorage()

    # --- Session state initialization ---
    if "names" not in st.session_state:
        st.session_state.names = []

    # 0: enter names, 1: reveal stage
    if "stage" not in st.session_state:
        st.session_state.stage = 0

    if "assignments" not in st.session_state:
        st.session_state.assignments = {}

    if "revealed" not in st.session_state:
        st.session_state.revealed = set()

    if "locked" not in st.session_state:
        st.session_state.locked = False

    # Load saved values from local storage
    if "initialized" not in st.session_state:
        saved_seed = local_storage.getItem("secret_santa_seed")
        saved_name = local_storage.getItem("secret_santa_name")
        saved_names = local_storage.getItem("secret_santa_names")
        st.session_state.saved_seed = saved_seed if saved_seed else ""
        st.session_state.saved_name = saved_name if saved_name else ""
        st.session_state.saved_names = saved_names if saved_names else ""
        st.session_state.initialized = True

    # --- Setup phase ---
    if not st.session_state.locked:
        st.subheader("Tragt eure Namen ein")
        with st.sidebar:
            seed = st.text_input("Seed der die pseudo zufällige Zuweisung definiert", value=st.session_state.saved_seed)
        names_input = st.text_area(
            "Teilnehmer (ein Name pro Zeile)",
            value="\n".join(st.session_state.saved_names),
            height=200,
        )

        names = [n.strip() for n in names_input.splitlines() if n.strip()]

        button_text = button_text.setup.value if st.session_state.stage == 0 else button_text.reveal.value
        if st.session_state.stage == 1:
            st.toast("Zuweisungen erstellt")

        if st.button(button_text, width="stretch", key="main_button"):
            if len(names) < 2:
                st.error("Es werden mindestens zwei Teilnehmer benötigt")
            elif len(set(names)) != len(names):
                st.error("Namen müssen eindeutig sein")
            else:
                if st.session_state.stage is 0:
                    st.session_state.stage = 1
                    st.rerun()

                st.session_state.names = names
                st.session_state.assignments = generate_assignments(names, seed)
                st.session_state.revealed = set()
                st.session_state.locked = True
                local_storage.setItem("secret_santa_seed", seed, key="secret_santa_seed")
                local_storage.setItem("secret_santa_names", names, key="secret_santa_names")

    # --- Reveal phase ---
    else:
        st.subheader("Zuweisung anzeigen")

        name = st.selectbox(
            "Dein Name",
            st.session_state.names,
            index=st.session_state.names.index(st.session_state.saved_name)
            if st.session_state.saved_name in st.session_state.names else 0
        )

        # Save the selected name to local storage
        if name != st.session_state.saved_name:
            local_storage.setItem("secret_santa_name", name)
            st.session_state.saved_name = name

        if name in st.session_state.revealed:
            st.warning("Du hast deine Zuweisung bereits gesehen")
        else:
            if st.button("Zuweisung anzeigen"):
                recipient = st.session_state.assignments[name]
                st.success(f"{name}, du musst **{recipient}** etwas geben")
                st.session_state.revealed.add(name)

        st.divider()

        if st.button("Reset"):
            st.session_state.revealed.clear()
            st.success("Zurückgesetzt – alle können erneut schauen")
