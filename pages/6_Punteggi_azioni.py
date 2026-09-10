import streamlit as st
from sheets import get_punteggi_azioni
import pandas as pd
import plotly.express as px

st.title("")

with st.spinner("Caricamento punteggi azioni"):
    df = get_punteggi_azioni()

    if len(df) == 0:
        st.warning("Nessun dato disponibile")
        st.stop()

    # Converti Punteggio in numerico
    df["Punteggio"] = pd.to_numeric(df["Punteggio"], errors="coerce")
    df["Selezioni"] = pd.to_numeric(df["Selezioni"], errors="coerce")
    
    # Nascondi elementi non selezionati (N = 0)
    df = df[df["Selezioni"] > 0]
    
    if len(df) == 0:
        st.warning("Nessuna azione selezionata")
        st.stop()

    # Ordina dal punteggio minore al maggiore
    df = df.sort_values("Punteggio", ascending=True).reset_index(drop=True)
    
    # Crea testo combinato: punteggio (# selezioni)
    df["Testo"] = df["Punteggio"].astype(int).astype(str) + " (#" + df["Selezioni"].astype(int).astype(str) + ")"

    fig = px.bar(
        df,
        x="Punteggio",
        y="Azione",
        orientation="h",
        text="Testo",
        color_discrete_sequence=["#4F46E5"]
    )

    fig.update_layout(
        title="📊 Punteggi Azioni",
        template="plotly_white",
        showlegend=False,
        height=max(400, len(df) * 40),

        # margins
        margin=dict(l=20, r=20, t=60, b=20),

        # smaller labels
        yaxis=dict(
            automargin=True,
            tickfont=dict(size=10)
        ),
        xaxis=dict(
            automargin=True,
            tickfont=dict(size=10),
            range=[0, None]  # Forza l'asse x a partire da 0
        )
    )

    fig.update_traces(
        textposition="outside",
        textfont=dict(size=10),
        cliponaxis=False
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "responsive": True,
            "scrollZoom": False,      # disable pinch zoom
            "displayModeBar": False,  # hide toolbar
            "staticPlot": True        # completely disable interactions
        }
    )
