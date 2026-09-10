import streamlit as st
from sheets import salva_pronostici
import time

st.title("Salva Pronostici")


@st.dialog("Salva pronostici")
def popup_salva_pronostici():
    password = st.text_input("Inserisci la password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Conferma"):
            if password == "paradossale":
                with st.spinner("Salvataggio pronostici in corso..."):
                    salva_pronostici()
                st.success("Pronostici salvati con successo!")
                
                with st.spinner("Reindirizzamento a classifica..."):
                    time.sleep(1)
                    st.switch_page("pages/3_Classifica.py")
            else:
                st.error("Password errata.")

    with col2:
        if st.button("Annulla"):
            st.rerun()


if st.button("Salva pronostici"):
    popup_salva_pronostici()
