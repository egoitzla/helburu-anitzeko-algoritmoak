"""
Helburu anitzeko algoritmoen bistaratzea (Streamlit + Plotly).

Exekutatu:
    .venv/bin/streamlit run app.py

Orriak `orriak/` karpetan daude; algoritmo berriak `algoritmoak.py` fitxategian.
"""
import streamlit as st


st.set_page_config(page_title="Helburu anitzeko algoritmoak", layout="wide")

orria = st.navigation([
    st.Page("orriak/hasiera.py", title="Hasiera", icon=":material/home:", default=True),
    st.Page("orriak/bilakaera.py", title="Bilakaera", icon=":material/animation:"),
    st.Page("orriak/konparaketa.py", title="Konparaketa", icon=":material/compare:"),
    st.Page("orriak/dentsitatea.py", title="Dentsitatea", icon=":material/bubble_chart:"),
])

# Orri bakoitzak bere parametroak hemen jartzen ditu (albo-barraren goialdean)
st.session_state["parametroen_lekua"] = st.sidebar.container()

# Orri guztietarako bistaratze-aukerak (hemen daudenez, orriz aldatzean mantentzen dira)
with st.sidebar:
    st.divider()
    st.header("Bistaratzea")
    dominioa = st.toggle("Domeinu osoa ikusi [0, π]²", value=False, key="dominioa")
    erref = st.toggle("Benetako frontea erakutsi (erreferentzia)", value=True, key="erref")
    abiadura = st.slider("Milisegundo urratseko", 20, 500, 80, step=10, key="abiadura")

# Modu argia/iluna Streamlit-en gaiaren araberakoa da (⋮ menua → Settings)
argia = st.context.theme.type == "light"

st.session_state["aukerak"] = {
    "dominioa": dominioa,
    "erref": erref,
    "argia": argia,
    "abiadura": abiadura,
    "erref_kolorea": "#c98a00" if argia else "#f2b701",
}

orria.run()
