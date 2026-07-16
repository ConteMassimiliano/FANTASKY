import streamlit as st
from sheets import archivia
import time

st.title("Per Admin")


@st.dialog("Archivia settimana")
def popup_archivia():
    password = st.text_input("Inserisci la password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Conferma"):
            if password == "paradossale":
                with st.spinner("Archiviazione in corso..."):
                    archivia()
                st.success("Settimana archiviata con successo.")
                
                with st.spinner("Reindirizzamento a classifica..."):
                    time.sleep(1)
                    st.switch_page("pages/3_Classifica.py")
            else:
                st.error("Password errata.")

    with col2:
        if st.button("Annulla"):
            st.rerun()


if st.button("Archivia settimana"):
    popup_archivia()
