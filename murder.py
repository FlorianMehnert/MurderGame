import time

import streamlit as st
import random
from streamlit_local_storage import LocalStorage

setup = "Zuweisungen erstellen"
reveal = "Zuweisung anzeigen"


def generate_assignments(names, seed):
    """
    Generates a set of unique secret assignments where each name is assigned
    to another name in the list in a randomized order. The order ensures that no
    name is assigned to itself and the assignments form a circular permutation. The
    randomization process is deterministic based on the provided seed value.

    :param names: List of names to be assigned in the secret Santa arrangement.
                  Each name must be unique in the input list.
    :type names: List[str]
    :param seed: A seed value for the random number generator to ensure the
                 deterministic output of the assignments.
    :type seed: int
    :return: A dictionary of secret Santa assignments, where each key is a name
             from the input list and the value is the name assigned to them.
    :rtype: Dict[str, str]
    """
    random.seed(seed)
    shuffled = names[:]
    random.shuffle(shuffled)

    assignments = {}
    for i in range(len(shuffled)):
        assignments[shuffled[i]] = shuffled[(i + 1) % len(shuffled)]

    return assignments


def setup_phase():
    """
    Handles the setup phase for the application. This function allows users to input names, set a seed
    for deterministic assignment generation, and manage participant configurations. It validates input, updates
    the session state, and generates assignments when appropriate.

    :param none: The function does not accept parameters and operates on the Streamlit session state.

    :raises ValueError: Raises an error when the number of participants is less than two or when duplicate names exist.

    :return: Does not return any explicit value. Modifies the application state via Streamlit session state (`st.session_state`)
             and interacts with Streamlit's UI components.
    """
    if not st.session_state.locked:
        st.subheader("Tragt eure Namen ein")
        with st.sidebar:
            seed = st.text_input("Seed der die pseudo zufällige Zuweisung definiert",
                                 value=st.session_state.saved_seed if st.session_state.saved_seed else "1")
            if st.button("Cookie löschen", icon="🍪"):
                local_storage.deleteAll()
        names_input = st.text_area(
            "Teilnehmer (ein Name pro Zeile)",
            value="\n".join(st.session_state.saved_names),
            height=200,
        )

        names = [n.strip() for n in names_input.splitlines() if n.strip()]

        button_text = setup if st.session_state.stage == 0 else reveal
        if st.session_state.stage == 1:
            st.toast("Zuweisungen erstellt")

        if st.button(button_text, width="stretch", key="main_button"):
            if len(names) < 2:
                st.error("Es werden mindestens zwei Teilnehmer benötigt")
            elif len(set(names)) != len(names):
                st.error("Namen müssen eindeutig sein")
            else:
                st.session_state.names = names
                st.session_state.assignments = generate_assignments(names, seed)
                st.session_state.revealed = set()
                st.session_state.locked = True
                local_storage.setItem("secret_santa_seed", seed, key="secret_santa_seed")
                local_storage.setItem("secret_santa_names", names, key="secret_santa_names")
                st.session_state.stage = 1
                time.sleep(.5)
                st.rerun()


class RevealPhase:
    def reveal(self):
        """
        Reveals and manages the visibility settings for assignments in the session state.

        This method interfaces with the sidebar to allow dynamic interaction through widgets,
        such as sliders, toggles, and buttons, enabling the user to control the visibility
        of certain assignments within the application.

        :param self: An instance of the class that manages assignments visibility.
        :return: Nothing is explicitly returned, as operations are performed directly
                 on the session state and through interactive widgets.
        """
        name = self.widgets()
        with st.sidebar:
            st.session_state.time_to_look_at_assignment = st.slider("Zeit (s) bis die Zuweisung angezeigt wird",
                                                                    min_value=1.0, max_value=10.0,
                                                                    value=st.session_state.time_to_look_at_assignment if st.session_state.time_to_look_at_assignment else 5.0,
                                                                    step=1.0)
            st.session_state.show_known_assignments = st.toggle("Bekannte Zuweisungen anzeigen", value=False)
            if name in st.session_state.revealed and st.button(f"Sichtsperre für {name} zurücksetzen"):
                st.session_state.revealed.remove(name)
                st.success("Zurückgesetzt – alle können erneut schauen")
                st.rerun()

    @st.fragment
    def widgets(self):
        """
        Provides functionality for managing widgets in the reveal stage of the application

        :return: Selected widget name
        :rtype: str
        """
        name = self.selectbox()
        self.reveal_button(name)
        return name

    def selectbox(self):
        """
        Creates and renders a selectbox widget that allows users to choose a name from a filtered
        list of names. The options exclude those already marked as revealed.

        :returns: The selected name from the selectbox widget.
        :rtype: str
        """
        disable_selectbox = False
        if len(set(st.session_state.names).difference(st.session_state.revealed)) == 0:
            disable_selectbox = True

        return st.selectbox(
            "Wähle deinen Namen aus:",
            set(st.session_state.names).difference(
                st.session_state.revealed) if not st.session_state.show_known_assignments else st.session_state.names,
            index=st.session_state.names.index(st.session_state.saved_name)
            if st.session_state.saved_name in st.session_state.names else 0,
            disabled=disable_selectbox
        )

    def reveal_button(self, name):
        """
        Reveals the secret assignment and provides instructions for players in the game. Depending on the
        state of the system and the player's status, it shows specific warnings, messages, and actions.

        :param name: The name of the player whose assignment is being revealed.
        :type name: str

        :return: None
        """
        if name in st.session_state.revealed:
            st.warning("Du hast deine Zuweisung gesehen, viel Glück!")
            remaining_set = tuple(set(st.session_state.assignments.keys()).difference(st.session_state.revealed))
            if remaining_set:
                choice = random.choice(remaining_set)
                st.session_state.saved_name = choice
                st.info(f"Bitte gib das Handy weiter an {choice}")
            else:
                st.title("Jeder weiß jetzt, wem er etwas geben muss. Das Mörder Spiel startet damit!")
        else:
            if name and st.button("Zuweisung anzeigen"):
                recipient = st.session_state.assignments[name]
                st.success(f"{name}, du musst **{recipient}** etwas geben")
                st.session_state.revealed.add(name)
                progress_bar = st.progress(0)

                for percent_complete in range(100):
                    time.sleep(0.01 * st.session_state.time_to_look_at_assignment)
                    time_text = int(st.session_state.time_to_look_at_assignment - percent_complete / (
                                100 / st.session_state.time_to_look_at_assignment)) + 1
                    progress_bar.progress(percent_complete + 1,
                                          text=f"{time_text} {"Sekunden" if time_text > 1 else "Sekunde"} verbleibend um dir den Namen zu merken")
                st.rerun(scope="fragment")


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

    if "time_to_look_at_assignment" not in st.session_state:
        st.session_state.time_to_look_at_assignment = 1.0

    if "hide_known_assignments" not in st.session_state:
        st.session_state.show_known_assignments = True

    # Load saved values from local storage
    if "initialized" not in st.session_state:
        saved_seed = local_storage.getItem("secret_santa_seed")
        saved_name = local_storage.getItem("secret_santa_name")
        saved_names = local_storage.getItem("secret_santa_names")
        st.session_state.saved_seed = saved_seed if saved_seed else ""
        st.session_state.saved_name = saved_name if saved_name else ""
        st.session_state.saved_names = saved_names if saved_names else ""
        st.session_state.initialized = True
    if st.session_state.stage == 0:
        setup_phase()
    else:
        RevealPhase().reveal()
