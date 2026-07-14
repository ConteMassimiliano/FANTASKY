
import streamlit as st
from sheets import get_players

st.set_page_config(page_title="FantaSkyline")

st.title("🏆 FantaSkyline")

with st.spinner("..."):
    players = get_players()

giocatore = st.selectbox(
    "Chi sta giocando?",
    players
)

if st.button("Continua"):
    st.session_state["giocatore"] = giocatore
    st.switch_page("pages/1_Giocata.py")
