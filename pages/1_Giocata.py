
import streamlit as st
from sheets import get_actions, save_picks

st.title("🎯 Giocata")

if "giocatore" not in st.session_state:
    st.error("Seleziona prima un giocatore")
    st.stop()

giocatore = st.session_state["giocatore"]

st.write(f"Giocatore: **{giocatore}**")

with st.spinner("..."):
    azioni = get_actions()

selected = st.multiselect(
    "Scegli esattamente 5 azioni",
    options=azioni
)

st.write(f"{len(selected)}/5 selezioni")

if st.button("Salva giocata"):
    if len(selected) != 5:
        st.error("Devi scegliere esattamente 5 azioni")
    else:
        with st.spinner("Salvataggio in corso..."):
            save_picks(giocatore, selected)

        st.success("Giocata salvata!")