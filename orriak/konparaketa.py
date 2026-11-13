"""
Bi algoritmo (edo konfigurazio) alboz albo konparatu, animazio sinkronizatu batean.
"""
import math

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import komuna
from algoritmoak import ALGORITMOAK
from komuna import KOLOREAK, HV_ATALASEA

st.title("Bi algoritmoren konparaketa")
st.caption(
    "Bi algoritmo edo konfigurazio alboz albo, urrats berean. Algoritmo bakarra badago ere, "
    "parametro desberdinekin konpara daiteke (adib. η txikiak = esplorazio handiagoa)."
)

komuna.albo_edukiontzia().caption("A eta B konfigurazioak orri nagusian aukeratzen dira.")

# ---------------------------------------------------------------------------
# A eta B konfigurazioak
# ---------------------------------------------------------------------------
LEHENETSIAK = {"A": {}, "B": {"eta_c": 5, "eta_m": 5}}

hautatuak, oraingoa = {}, {}
with st.expander("Konfigurazioak", expanded=True):
    # Algoritmoak formulariotik kanpo: parametro-zerrenda algoritmoaren araberakoa da
    for izena, zutabea in zip("AB", st.columns(2, gap="large")):
        with zutabea:
            st.markdown(f"#### <span style='color:{KOLOREAK[izena]}'>●</span> {izena}",
                        unsafe_allow_html=True)
            hautatuak[izena], _ = komuna.algoritmo_hautatzailea(zutabea, f"konp-{izena}")
    # Formularioa: parametroak aldatzean ez da ezer exekutatzen botoia sakatu arte
    with st.form("konp-formularioa", border=False):
        for izena, zutabea in zip("AB", st.columns(2, gap="large")):
            with zutabea:
                parametroak, hazia = komuna.parametro_widgetak(
                    f"konp-{izena}", hautatuak[izena], LEHENETSIAK[izena])
                oraingoa[izena] = (hautatuak[izena], parametroak, hazia)
        sakatuta = st.form_submit_button("▶ Biak exekutatu", type="primary", width="stretch")

exekutatua = komuna.exekutatutako_konfigurazioa("konp-konfig", oraingoa, sakatuta)
if exekutatua is None:
    st.info("A eta B konfiguratu eta sakatu **▶ Biak exekutatu** algoritmoak exekutatzeko.",
            icon=":material/tune:")
    st.stop()
konfig = {}
for izena, (algoritmoa, parametroak, hazia) in exekutatua.items():
    konfig[izena] = {"algoritmoa": algoritmoa, "info": ALGORITMOAK[algoritmoa],
                     "urratsak": komuna.exekutatu(algoritmoa, parametroak, hazia)}
st.caption("Erabilitako haziak: " + " · ".join(
    f"{izena} = **{h}**" for izena, (_, _, h) in exekutatua.items()))

A, B = konfig["A"]["urratsak"], konfig["B"]["urratsak"]
GA, GB = len(A) - 1, len(B) - 1
G = max(GA, GB)
urrats_izena = (konfig["A"]["info"]["urratsa"]
                if konfig["A"]["info"]["urratsa"] == konfig["B"]["info"]["urratsa"] else "Urratsa")


# ---------------------------------------------------------------------------
# Azken emaitzak: B-ren deltak A-rekiko
# ---------------------------------------------------------------------------
def laburpena(urratsak):
    azkena = urratsak[-1]
    return {
        "hv": azkena["hv"],
        "hv_balioa": azkena["hv_balioa"],
        "igd": azkena["igd"],
        "n_fronte": azkena["n_fronte"],
        "konb": komuna.konbergentzia_urratsa(urratsak),
    }


la, lb = laburpena(A), laburpena(B)
konb_etiketa = f"HV ≥ {HV_ATALASEA:.0f} %"
konb_laguntza = (f"Hiperbolumenak {HV_ATALASEA:.0f} % lehen aldiz gainditzen duen "
                 f"{urrats_izena.lower()}a. Txikiagoa = azkarrago konbergitzen du.")
argia = komuna.aukerak()["argia"]
DELTA_KOLOREAK = ({"hobea": "#1a7f37", "okerragoa": "#cf222e", "berdin": "#6e7781"} if argia else
                  {"hobea": "#3fb950", "okerragoa": "#f85149", "berdin": "#8b949e"})


def delta_etiketa(b, a, formatua, handiagoa_hobea=True):
    """B-ren aldea A-rekiko, koloreztatuta (st.metric-en deltak ez dira modu argira egokitzen)."""
    if a is None or b is None:
        return "&nbsp;"
    aldea = b - a
    if abs(aldea) < 1e-12:
        egoera, gezia = "berdin", "="
    else:
        hobea = (aldea > 0) == handiagoa_hobea
        egoera, gezia = ("hobea" if hobea else "okerragoa"), ("▲" if aldea > 0 else "▼")
    return (f"<span style='color:{DELTA_KOLOREAK[egoera]};font-size:0.9rem;font-weight:600'>"
            f"{gezia} {formatua.format(aldea)}</span>")


metrika_zerrenda = [
    # (etiketa, gakoa, balioaren formatua, aldearen formatua, handiagoa hobea, laguntza)
    ("Hiperbolumena", "hv", "{:.1f} %", "{:+.1f} pp", True, None),
    ("HV (balioa)", "hv_balioa", "{:.4f}", "{:+.4f}", True, None),
    ("IGD", "igd", "{:.4f}", "{:+.4f}", False, None),
    ("1. frontean", "n_fronte", "{}", "{:+d}", True, None),
    (konb_etiketa, "konb", "{}", "{:+d}", False, konb_laguntza),
]
# A eta B lerro banatan: bost txartel albo batean erdiko zabaleran ez dira sartzen
for izena, l in (("A", la), ("B", lb)):
    etiketa_zut, *k = st.columns([0.6] + [1] * len(metrika_zerrenda), vertical_alignment="center")
    etiketa_zut.markdown(f"#### <span style='color:{KOLOREAK[izena]}'>●</span> {izena}",
                         unsafe_allow_html=True)
    for kol, (etiketa, gakoa, fbal, fald, handiagoa, laguntza) in zip(k, metrika_zerrenda):
        balioa = "—" if l[gakoa] is None else fbal.format(l[gakoa])
        kol.metric(etiketa, balioa, help=laguntza)
        if izena == "B":
            kol.markdown(delta_etiketa(l[gakoa], la[gakoa], fald, handiagoa),
                         unsafe_allow_html=True)
st.caption("B-ren azpiko aldeak A-rekiko dira. Berdea = B hobea, gorria = B okerragoa.")


# ---------------------------------------------------------------------------
# Irudi animatua: goian bi populazioak, behean metrikak gainjarrita
# ---------------------------------------------------------------------------
def serie(urratsak, gakoa, g):
    g = min(g, len(urratsak) - 1)
    return go.Scatter(x=list(range(g + 1)), y=[u[gakoa] for u in urratsak[: g + 1]])


def dinamikoak(g):
    return (komuna.populazio_trazak(A[min(g, GA)]) + komuna.populazio_trazak(B[min(g, GB)])
            + [serie(A, "hv", g), serie(B, "hv", g), serie(A, "hv_balioa", g),
               serie(B, "hv_balioa", g), serie(A, "igd", g), serie(B, "igd", g)])


fig = make_subplots(
    rows=3, cols=2, row_heights=[0.56, 0.22, 0.22],
    specs=[[{}, {}], [{}, {}], [{"colspan": 2}, None]],
    horizontal_spacing=0.08, vertical_spacing=0.08,
    subplot_titles=(f"A: {konfig['A']['algoritmoa']}", f"B: {konfig['B']['algoritmoa']}",
                    "Hiperbolumena (% optimoarekiko) ↑", "Hiperbolumena (balioa) ↑",
                    "IGD: benetako frontera distantzia ↓"),
)
oinarri_kop = komuna.oinarri_trazak(fig, 1, 1) + komuna.oinarri_trazak(fig, 1, 2, showlegend=False)

lerroa = lambda izena, legenda: dict(  # noqa: E731
    name=izena, mode="lines", showlegend=legenda, legend="legend2",
    line=dict(color=KOLOREAK[izena], width=2))
estiloak = (komuna.POPULAZIO_ESTILOAK
            + [dict(e, showlegend=False) for e in komuna.POPULAZIO_ESTILOAK]
            + [lerroa("A", True), lerroa("B", True), lerroa("A", False), lerroa("B", False),
               lerroa("A", False), lerroa("B", False)])
kokapenak = [(1, 1)] * 3 + [(1, 2)] * 3 + [(2, 1), (2, 1), (2, 2), (2, 2), (3, 1), (3, 1)]
hasiera = dinamikoak(0)
for traza, estiloa, (r, c) in zip(hasiera, estiloak, kokapenak):
    traza.update(**estiloa)
    fig.add_trace(traza, row=r, col=c)
dinamiko_idx = list(range(oinarri_kop, oinarri_kop + len(hasiera)))

fig.frames = [go.Frame(name=str(g), data=dinamikoak(g), traces=dinamiko_idx)
              for g in range(G + 1)]

komuna.populazio_ardatzak(fig, 1, 1)
komuna.populazio_ardatzak(fig, 1, 2)
igd_max = max((u["igd"] for u in A + B if not math.isnan(u["igd"])), default=1)
hv_opt = komuna.hv_optimoa()
for r, c in ((2, 1), (2, 2), (3, 1)):
    fig.update_xaxes(range=[0, G], row=r, col=c)
fig.update_xaxes(title_text=urrats_izena, row=3, col=1)
fig.update_yaxes(range=[0, 105], ticksuffix=" %", row=2, col=1)
fig.update_yaxes(range=[0, hv_opt * 1.05], row=2, col=2)
fig.add_hline(y=hv_opt, line=dict(dash="dash", width=1, color="#9aa0a6"),
              annotation_text=f"optimoa {hv_opt:.4f}", annotation_position="bottom right",
              row=2, col=2)
fig.update_yaxes(range=[0, igd_max * 1.05], row=3, col=1)

goiko_behea = fig.layout.yaxis.domain[0]
fig.update_layout(
    height=1150,
    margin=dict(t=40, l=60, r=20, b=40),
    legend=dict(x=0.01, y=goiko_behea + 0.01, xanchor="left", yanchor="bottom",
                bgcolor="rgba(127,127,127,0.15)"),
    legend2=dict(x=0.45, y=0.02, xanchor="right", yanchor="bottom", orientation="h",
                 bgcolor="rgba(127,127,127,0.15)"),
)
komuna.animazio_kontrolak(fig, G, urrats_izena)
komuna.grafikoa_erakutsi(fig)

if GA != GB:
    st.info(f"A-k {GA} eta B-k {GB} {urrats_izena.lower()} ditu: laburrenak bere azken "
            "egoeran jarraitzen du besteak amaitu arte.")
