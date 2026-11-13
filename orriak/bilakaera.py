"""
Algoritmo baten bilakaera: populazioa eta metrikak, urratsez urrats animatuta.
"""
import csv
import io
import math

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import komuna
from algoritmoak import ALGORITMOAK
from komuna import KOLOREAK, ERREF_PUNTUA

# ---------------------------------------------------------------------------
# Parametroak (albo-barran)
# ---------------------------------------------------------------------------
alboa = komuna.albo_edukiontzia()
alboa.header("Algoritmoa")
hautatua, _ = komuna.algoritmo_hautatzailea(alboa, "bil")
# Formularioa: parametroak aldatzean ez da ezer exekutatzen botoia sakatu arte
with alboa.form("bil-formularioa", border=False):
    st.subheader("Parametroak")
    parametroak, hazia = komuna.parametro_widgetak("bil", hautatua)
    sakatuta = st.form_submit_button("▶ Exekutatu", type="primary", width="stretch")

exekutatua = komuna.exekutatutako_konfigurazioa(
    "bil-konfig", (hautatua, parametroak, hazia), sakatuta)
if exekutatua is None:
    komuna.exekutatzeko_zain(f"{hautatua}: Pareto frontea nola eratzen den", "▶ Exekutatu")
algoritmoa, parametroak, hazia = exekutatua
info = ALGORITMOAK[algoritmoa]
urratsak = komuna.exekutatu(algoritmoa, parametroak, hazia)
urrats_izena = info["urratsa"]
G = len(urratsak) - 1

# ---------------------------------------------------------------------------
# Goiburua eta azken emaitzen laburpena
# ---------------------------------------------------------------------------
st.title(f"{algoritmoa}: Pareto frontea nola eratzen den")
st.caption(
    "TNK problema · $f_1 = x_1$ eta $f_2 = x_2$ minimizatu, $C_1$ eta $C_2$ murriztapenekin. "
    "Helburuak aldagaiak berak direnez, puntu bakoitza aldi berean soluzioa eta helburuak da."
)

azkena = urratsak[-1]
k = st.columns(6)
k[0].metric(f"{urrats_izena}k", G)
k[1].metric("Bideragarriak (azkena)", azkena["n_bid"])
k[2].metric("1. frontean (azkena)", azkena["n_fronte"])
k[3].metric("Hiperbolumena", f"{azkena['hv']:.1f} %")
k[4].metric("HV (balioa)", f"{azkena['hv_balioa']:.4f}",
            help=f"Optimoa (benetako frontea): {komuna.hv_optimoa():.4f}")
k[5].metric("IGD", f"{azkena['igd']:.4f}")
st.caption(f"Erabilitako hazia: **{hazia}** (finkatu albo-barran emaitza errepikatzeko)")


# ---------------------------------------------------------------------------
# Irudi animatua: ezkerrean populazioa, eskuinean metrikak hazten
# ---------------------------------------------------------------------------
def serie(gakoa, g):
    return go.Scatter(x=list(range(g + 1)), y=[u[gakoa] for u in urratsak[: g + 1]])


def dinamikoak(g):
    return komuna.populazio_trazak(urratsak[g]) + [
        serie("hv", g), serie("hv_balioa", g), serie("igd", g), serie("n_bid", g),
        serie("n_fronte", g)]


fig = make_subplots(
    rows=4, cols=2, column_widths=[0.58, 0.42],
    specs=[[{"rowspan": 4}, {}], [None, {}], [None, {}], [None, {}]],
    horizontal_spacing=0.08, vertical_spacing=0.07,
    subplot_titles=("Populazioa helburuen espazioan",
                    "Hiperbolumena (% optimoarekiko) ↑",
                    "Hiperbolumena (balioa) ↑",
                    "IGD: benetako frontera distantzia ↓",
                    "Soluzio kopurua"),
)
oinarri_kop = komuna.oinarri_trazak(fig, 1, 1)

artxiboa_du = any(u["artxiboa"] for u in urratsak)
estiloak = komuna.populazio_estiloak(
    artxiboa_du, populazioa_ezkutuan=artxiboa_du and not komuna.aukerak()["populazioa"]) + [
    dict(name="Hiperbolumena", mode="lines", showlegend=False,
         line=dict(color=KOLOREAK["hv"], width=2)),
    dict(name="Hiperbolumena (balioa)", mode="lines", showlegend=False,
         line=dict(color=KOLOREAK["hv"], width=2, dash="dot")),
    dict(name="IGD", mode="lines", showlegend=False,
         line=dict(color=KOLOREAK["igd"], width=2)),
    dict(name="Bideragarriak (kop.)", mode="lines", legend="legend2",
         line=dict(color=KOLOREAK["beste"], width=2)),
    dict(name="1. frontean (kop.)", mode="lines", legend="legend2",
         line=dict(color=KOLOREAK["fronte"], width=2)),
]
kokapenak = [(1, 1)] * 4 + [(1, 2), (2, 2), (3, 2), (4, 2), (4, 2)]
hasiera = dinamikoak(0)
for traza, estiloa, (r, c) in zip(hasiera, estiloak, kokapenak):
    traza.update(**estiloa)
    fig.add_trace(traza, row=r, col=c)
dinamiko_idx = list(range(oinarri_kop, oinarri_kop + len(hasiera)))

fig.frames = [go.Frame(name=str(g), data=dinamikoak(g), traces=dinamiko_idx)
              for g in range(G + 1)]

# Ardatzak: finkoak, animazioan zehar ez aldatzeko
komuna.populazio_ardatzak(fig, 1, 1)
igd_max = max((u["igd"] for u in urratsak if not math.isnan(u["igd"])), default=1)
n_max = max(u["n_bid"] + len(u["ez_bid"]) for u in urratsak)
hv_opt = komuna.hv_optimoa()
for r in (1, 2, 3, 4):
    fig.update_xaxes(range=[0, G], row=r, col=2)
fig.update_xaxes(title_text=urrats_izena, row=4, col=2)
fig.update_yaxes(range=[0, 105], ticksuffix=" %", row=1, col=2)
fig.update_yaxes(range=[0, hv_opt * 1.05], row=2, col=2)
fig.add_hline(y=hv_opt, line=dict(dash="dash", width=1, color="#9aa0a6"),
              annotation_text=f"optimoa {hv_opt:.4f}", annotation_position="bottom right",
              row=2, col=2)
fig.update_yaxes(range=[0, igd_max * 1.05], row=3, col=2)
fig.update_yaxes(range=[0, n_max * 1.05], row=4, col=2)

fig.update_layout(
    height=900,
    margin=dict(t=40, l=60, r=20, b=40),
    legend=dict(x=0.01, y=0.01, xanchor="left", yanchor="bottom",
                bgcolor="rgba(127,127,127,0.15)"),
    legend2=dict(x=0.99, y=0.02, xanchor="right", yanchor="bottom",
                 bgcolor="rgba(127,127,127,0.15)"),
)
komuna.animazio_kontrolak(fig, G, urrats_izena)
komuna.grafikoa_erakutsi(fig)

# ---------------------------------------------------------------------------
# Azken frontea: taula eta deskarga
# ---------------------------------------------------------------------------
with st.expander(f"Azken Pareto frontea ({azkena['n_fronte']} soluzio)"):
    # f = x soluzio bideragarrietan; artxiboa badago, artxiboaren frontea
    errenkadak = [{"x1": round(x[0], 6), "x2": round(x[1], 6)} for x in azkena["fronte_csv"]]
    st.dataframe(errenkadak, width="stretch", height=260)
    buf = io.StringIO()
    idazlea = csv.DictWriter(buf, fieldnames=["x1", "x2"])
    idazlea.writeheader()
    idazlea.writerows(errenkadak)
    st.download_button("CSV deskargatu", buf.getvalue(),
                       file_name=f"{algoritmoa.lower()}_pareto.csv", mime="text/csv")

with st.expander("Nola irakurri"):
    st.markdown(
        f"""
**Populazioa** (ezkerrean)

- **0. {urrats_izena.lower()}**: ausazko puntuak $[0,\\pi]^2$ eremuan; ia guztiak ez bideragarriak dira.
- **Lehen urratsak**: hautaketak ez bideragarriak kentzen ditu (helburuak = 10) eta
  populazioa ilargi-erdi grisaren barruan sartzen da.
- **Ondoren**: gurutzaketak eta mutazioak puntuak $C_1$-en ertz uhindura aldera bultzatzen
  dituzte, eta dibertsitate-mekanismoak frontearen zati guztietan banatzen ditu.
- **Kanpoko artxiboa duten algoritmoetan (SPEA2)**: puntu beteak belaunaldi horretako
  populazioa dira, eta **zirkulu more hutsak artxiboa**. Artxiboa da algoritmoaren emaitza,
  eta metrikak (hiperbolumena, IGD, 1. frontean) harekin kalkulatzen dira.

**Metrikak** (eskuinean, animazioarekin batera hazten dira)

- **Hiperbolumena**: 1. fronteak menderatzen duen azalera, $({ERREF_PUNTUA[0]}, {ERREF_PUNTUA[1]})$
  erreferentzia-punturaino, benetako frontearenarekiko ehunekotan. Konbergentzia eta
  dibertsitatea batera neurtzen ditu; 100 % = benetako frontea bezain ona.
- **Hiperbolumena (balioa)**: azalera bera, ehunekora pasatu gabe. Marra etenak benetako
  frontearen balioa (optimoa) adierazten du.
- **IGD**: benetako fronteko puntu bakoitzetik 1. fronteko punturik hurbilenerainoko
  batez besteko distantzia. 0-ra hurbiltzen bada, frontea ondo hurbildu eta estali da.
- **Soluzio kopurua**: populazioko bideragarriak eta 1. frontekoak.

Metrikek ez dute algoritmoaren barnekorik erabiltzen: algoritmo guztiekin berdin kalkulatzen
dira, eta horrela konparagarriak dira.
"""
    )
