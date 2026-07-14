
import streamlit as st
from sheets import get_classifica
import plotly.express as px

st.title("")

with st.spinner("Caricamento classifica"):
    df = get_classifica()

    # st.dataframe(df, use_container_width=True)

    df = df.sort_values("Punteggio", ascending=False).reset_index(drop=True)

    df["Colore"] = "#4F46E5"  # default
    if len(df) > 0:
        df.loc[0, "Colore"] = "gold"
    if len(df) > 1:
        df.loc[1, "Colore"] = "silver"
    if len(df) > 2:
        df.loc[2, "Colore"] = "#CD7F32"  # bronzo

    fig = px.bar(
        df.sort_values("Punteggio"),
        x="Punteggio",
        y="Giocatore",
        orientation="h",
        text="Punteggio",
        color="Colore",
        color_discrete_map="identity"
    )

    fig.update_layout(
        title="🏆 Classifica",
        template="plotly_white",
        showlegend=False,
        height=max(400, len(df) * 40),
    )

    fig.update_traces(textposition="outside")

    st.plotly_chart(fig, use_container_width=True)
