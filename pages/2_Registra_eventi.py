import streamlit as st
from sheets import get_actions, get_prove, save_prove, refresh_cache

st.title("Registra eventi avvenuti")

with st.spinner("..."):
    prove = get_prove()
    azioni = get_actions()

selected_prova = st.selectbox(
    "Durante quale prova?",
    options=prove
)

selected_azioni = st.multiselect(
    "Cosa è successo?",
    options=azioni
)

if st.button("Registra eventi"):
    if len(selected_azioni) == 0:
        st.error("Devi selezionare almeno un'azione")
    else:
        save_prove(selected_prova, selected_azioni)
        refresh_cache()  # Refresh cache per aggiornare i punteggi dinamici
        st.success("Evento registrato!")