"""
Hasiera-orria: problema, algoritmoak eta aplikazioaren orrien aurkezpena.
"""
import streamlit as st
from plotly.subplots import make_subplots

import komuna
from algoritmoak import ALGORITMOAK
from komuna import ERREF_PUNTUA

st.title("Helburu anitzeko optimizazioa")
st.caption(
    "Algoritmo ebolutibo eleanitzak TNK problemaren gainean: nola eratzen den Pareto frontea "
    "belaunaldiz belaunaldi, eta algoritmoak elkarren artean nola konparatzen diren."
)

# ---------------------------------------------------------------------------
# Problema
# ---------------------------------------------------------------------------
ezker, eskuin = st.columns([1, 1], gap="large")

with ezker:
    st.subheader("Problema (TNK)")
    st.markdown(r"""
Bi helburu **minimizatu**:

$$f_1(x_1, x_2) = x_1$$

$$f_2(x_1, x_2) = x_2$$

Murriztapenak:

$$C_1:\; x_1^2 + x_2^2 - 1 - 0.1\cos\!\left(16\arctan\frac{x_1}{x_2}\right) \ge 0$$

$$C_2:\; (x_1 - 0.5)^2 + (x_2 - 0.5)^2 \le 0.5$$

$$0 \le x_1, x_2 \le \pi$$

Soluzio bat bideragarria ez bada, bi helburuei **10** balioa esleitzen zaie.

Helburuak aldagaiak berak direnez, erabakien espazioa eta helburuen espazioa bat dira:
eskuineko irudiko puntu bakoitza soluzio bat da. $C_1$-eko kosinuak ertza uhindu egiten du,
eta horregatik Pareto frontea **etena** da: zati batzuk ez dira optimoak.
""")

with eskuin:
    fig = make_subplots(rows=1, cols=1)
    komuna.oinarri_trazak(fig, 1, 1)
    komuna.populazio_ardatzak(fig, 1, 1)
    fig.update_layout(
        height=460, margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", y=-0.15, x=0),
    )
    komuna.grafikoa_erakutsi(fig)
    st.caption("Grisez, eskualde bideragarria; horiz, benetako Pareto frontea (sare fin batean kalkulatua). Bilakaera eta Konparaketa orrietan erreferentzia gisa erabiltzen da.")

st.divider()

# ---------------------------------------------------------------------------
# Algoritmoak (algoritmoak.py-ko erregistrotik automatikoki)
# ---------------------------------------------------------------------------
st.subheader("Algoritmoak")
zutabeak = st.columns(len(ALGORITMOAK), gap="medium")
for zutabea, (izena, info) in zip(zutabeak, ALGORITMOAK.items()):
    with zutabea.container(border=True):
        st.markdown(f"#### {izena}")
        st.write(info["deskribapena"])
        st.caption(f"{len(info['parametroak'])} parametro · urratsa: {info['urratsa'].lower()}a")

st.caption("Algoritmo berri bat gehitzeko, `algoritmoak.py` fitxategiko erregistroan sarrera bat gehitu: "
           "automatikoki agertuko da hemen eta beste orrietan.")

st.divider()

# ---------------------------------------------------------------------------
# Orriak
# ---------------------------------------------------------------------------
st.subheader("Zer egin daiteke")
a, b, c = st.columns(3, gap="medium")
with a.container(border=True):
    st.page_link("orriak/bilakaera.py", label="**Bilakaera**", icon=":material/animation:")
    st.write("Algoritmo bat aukeratu, parametroak doitu eta populazioa urratsez urrats animatuta "
             "ikusi, hiperbolumena eta IGD-a aldi berean hazten diren bitartean. Azken frontea "
             "CSV gisa deskarga daiteke.")
with b.container(border=True):
    st.page_link("orriak/konparaketa.py", label="**Konparaketa**", icon=":material/compare:")
    st.write("Bi algoritmo edo konfigurazio alboz albo, animazio sinkronizatu batean. Metrikak "
             "gainjarrita eta B-ren aldeak A-rekiko.")
with c.container(border=True):
    st.page_link("orriak/dentsitatea.py", label="**Dentsitatea**", icon=":material/bubble_chart:")
    st.write("Hainbat algoritmo N aldiz exekutatu, paraleloan eta hazi berdinekin: metriken "
             "banaketa (biolinak), soluzioen dentsitatea frontean eta CSV deskarga "
             "(lerro bat exekuzioko).")

# ---------------------------------------------------------------------------
# Metrikak
# ---------------------------------------------------------------------------
with st.expander("Metrikak eta hazia"):
    st.markdown(f"""
- **Hiperbolumena (HV) ↑**: 1. fronteak menderatzen duen azalera
  $({ERREF_PUNTUA[0]}, {ERREF_PUNTUA[1]})$ erreferentzia-punturaino, benetako frontearenarekiko
  ehunekotan. Konbergentzia eta dibertsitatea batera neurtzen ditu.
- **IGD ↓** (*Inverted Generational Distance*): benetako fronteko puntu bakoitzetik lortutako
  fronteko puntu hurbilenera dagoen batez besteko distantzia. 0 = frontea guztiz estalita.
- **Hazia**: lehenetsita ausazkoa da, *Exekutatu* sakatzen den bakoitzean berria. Erabilitakoa
  emaitzen azpian agertzen da; albo-barran finkatuz gero, emaitza bera errepikatzen da.
""")
