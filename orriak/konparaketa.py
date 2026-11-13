"""
Hainbat algoritmo (edo konfigurazio) konparatu, animazio sinkronizatu batean:
konfigurazio bakoitzaren populazioa bere grafikoan, metrikak gainjarrita, eta
fronte guztiak plano berean, koloreen bidez bereizita.
"""
import math

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import komuna
from algoritmoak import ALGORITMOAK
from komuna import HV_ATALASEA

MIN_KONF, MAX_KONF = 2, 6
IZENAK = "ABCDEF"
KONF_KOLOREAK = ["#2a9d8f", "#f58518", "#17becf", "#e377c2", "#bcbd22", "#8c564b"]
ALGORITMO_IZENAK = list(ALGORITMOAK)


def lehenetsiak(i):
    """i. konfigurazioaren algoritmoa eta parametro lehenetsiak (A eta B lehen bezala)."""
    if i == 1:
        return 0, {"eta_c": 5, "eta_m": 5}          # B: NSGA-II, η txikiekin
    if i >= 2:
        return (i - 1) % len(ALGORITMO_IZENAK), {}   # C: SPEA2, D: DE (GDE3), ...
    return 0, {}


def burua(i, testua=""):
    return (f"#### <span style='color:{KONF_KOLOREAK[i]}'>●</span> {IZENAK[i]}"
            + (f" <span style='font-weight:400;font-size:0.9rem'>{testua}</span>" if testua else ""))


st.title("Algoritmoen konparaketa")
st.caption(
    "Bi algoritmo edo gehiago (gehienez sei) urrats berean. Algoritmo bakarra badago ere, "
    "parametro desberdinekin konpara daiteke (adib. η txikiak = esplorazio handiagoa)."
)
komuna.albo_edukiontzia().caption("Konfigurazioak orri nagusian aukeratzen dira.")

# ---------------------------------------------------------------------------
# Konfigurazioak
# ---------------------------------------------------------------------------
st.session_state.setdefault("konp-kop", MIN_KONF)
kop = st.session_state["konp-kop"]

hautatuak, oraingoa = [], {}
with st.expander("Konfigurazioak", expanded=True):
    b1, b2, _ = st.columns([1.5, 1.2, 3.3])
    if b1.button("＋ Konfigurazioa gehitu", disabled=kop >= MAX_KONF, width="stretch"):
        st.session_state["konp-kop"] = kop + 1
        st.rerun()
    if b2.button("－ Azkena kendu", disabled=kop <= MIN_KONF, width="stretch"):
        st.session_state["konp-kop"] = kop - 1
        st.rerun()

    zut_kop = min(kop, 3)
    # Algoritmoak formulariotik kanpo: parametro-zerrenda algoritmoaren araberakoa da
    for hasiera in range(0, kop, zut_kop):
        for i, zutabea in zip(range(hasiera, min(hasiera + zut_kop, kop)),
                              st.columns(zut_kop, gap="large")):
            with zutabea:
                st.markdown(burua(i), unsafe_allow_html=True)
                alg, _ = komuna.algoritmo_hautatzailea(zutabea, f"konp-{IZENAK[i]}",
                                                       lehenetsiak(i)[0])
                hautatuak.append(alg)

    # Formularioa: parametroak aldatzean ez da ezer exekutatzen botoia sakatu arte
    with st.form("konp-formularioa", border=False):
        for hasiera in range(0, kop, zut_kop):
            for i, zutabea in zip(range(hasiera, min(hasiera + zut_kop, kop)),
                                  st.columns(zut_kop, gap="large")):
                with zutabea:
                    st.markdown(burua(i, hautatuak[i]), unsafe_allow_html=True)
                    parametroak, hazia = komuna.parametro_widgetak(
                        f"konp-{IZENAK[i]}", hautatuak[i], lehenetsiak(i)[1])
                    oraingoa[IZENAK[i]] = (hautatuak[i], parametroak, hazia)
        sakatuta = st.form_submit_button("▶ Guztiak exekutatu", type="primary", width="stretch")

exekutatua = komuna.exekutatutako_konfigurazioa("konp-konfig", oraingoa, sakatuta)
if exekutatua is None:
    st.info("Konfigurazioak aukeratu eta sakatu **▶ Guztiak exekutatu** algoritmoak exekutatzeko.",
            icon=":material/tune:")
    st.stop()

konfig = []
for i, (izena, (algoritmoa, parametroak, hazia)) in enumerate(exekutatua.items()):
    konfig.append({"izena": izena, "kolorea": KONF_KOLOREAK[i], "algoritmoa": algoritmoa,
                   "info": ALGORITMOAK[algoritmoa],
                   "urratsak": komuna.exekutatu(algoritmoa, parametroak, hazia)})
st.caption("Erabilitako haziak: " + " · ".join(
    f"{izena} = **{h}**" for izena, (_, _, h) in exekutatua.items()))

N = len(konfig)
for k in konfig:
    k["G"] = len(k["urratsak"]) - 1
    k["etiketa"] = f"{k['izena']}: {k['algoritmoa']}"
G = max(k["G"] for k in konfig)
urrats_motak = {k["info"]["urratsa"] for k in konfig}
urrats_izena = urrats_motak.pop() if len(urrats_motak) == 1 else "Urratsa"


# ---------------------------------------------------------------------------
# Azken emaitzak: besteen aldeak A-rekiko
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


konb_etiketa = f"HV ≥ {HV_ATALASEA:.0f} %"
konb_laguntza = (f"Hiperbolumenak {HV_ATALASEA:.0f} % lehen aldiz gainditzen duen "
                 f"{urrats_izena.lower()}a. Txikiagoa = azkarrago konbergitzen du.")
argia = komuna.aukerak()["argia"]
DELTA_KOLOREAK = ({"hobea": "#1a7f37", "okerragoa": "#cf222e", "berdin": "#6e7781"} if argia else
                  {"hobea": "#3fb950", "okerragoa": "#f85149", "berdin": "#8b949e"})


def delta_etiketa(b, a, formatua, handiagoa_hobea=True):
    """Konfigurazio baten aldea A-rekiko, koloreztatuta."""
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
laburpenak = [laburpena(k["urratsak"]) for k in konfig]
for i, (k, l) in enumerate(zip(konfig, laburpenak)):
    etiketa_zut, *kolak = st.columns([1] + [1] * len(metrika_zerrenda), vertical_alignment="center")
    etiketa_zut.markdown(burua(i, k["algoritmoa"]), unsafe_allow_html=True)
    for kol, (etiketa, gakoa, fbal, fald, handiagoa, laguntza) in zip(kolak, metrika_zerrenda):
        balioa = "—" if l[gakoa] is None else fbal.format(l[gakoa])
        kol.metric(etiketa, balioa, help=laguntza)
        if i > 0:
            kol.markdown(delta_etiketa(l[gakoa], laburpenak[0][gakoa], fald, handiagoa),
                         unsafe_allow_html=True)
st.caption("Azpiko aldeak A-rekiko dira. Berdea = A baino hobea, gorria = okerragoa.")


def serie(urratsak, gakoa, g):
    g = min(g, len(urratsak) - 1)
    return go.Scatter(x=list(range(g + 1)), y=[u[gakoa] for u in urratsak[: g + 1]])


# ---------------------------------------------------------------------------
# 1. irudia: populazio bakoitza bere grafikoan, eta metrikak gainjarrita
# ---------------------------------------------------------------------------
st.subheader("Populazioak eta metrikak")
zut = min(N, 3)
pop_errenkadak = math.ceil(N / zut)
metrika_errenkadak = [("hv", "Hiperbolumena (% optimoarekiko) ↑"),
                      ("hv_balioa", "Hiperbolumena (balioa) ↑"),
                      ("igd", "IGD: benetako frontera distantzia ↓")]
errenkadak = pop_errenkadak + len(metrika_errenkadak)
pop_kokapenak = [(i // zut + 1, i % zut + 1) for i in range(N)]

izenburuak = [k["etiketa"] for k in konfig] + [""] * (pop_errenkadak * zut - N)
izenburuak += [e for _, e in metrika_errenkadak]
specs = ([[{} for _ in range(zut)] for _ in range(pop_errenkadak)]
         + [[{"colspan": zut}] + [None] * (zut - 1) for _ in metrika_errenkadak])
pop_altuera, metrika_altuera = 420, 220
fig = make_subplots(
    rows=errenkadak, cols=zut, specs=specs, subplot_titles=izenburuak,
    row_heights=[pop_altuera] * pop_errenkadak + [metrika_altuera] * len(metrika_errenkadak),
    horizontal_spacing=0.06, vertical_spacing=0.06 if errenkadak <= 4 else 0.045,
)
oinarri_kop = sum(komuna.oinarri_trazak(fig, r, c, showlegend=(i == 0))
                  for i, (r, c) in enumerate(pop_kokapenak))

artxiboa_du = any(u["artxiboa"] for k in konfig for u in k["urratsak"])
denetan_artxiboa = all(any(u["artxiboa"] for u in k["urratsak"]) for k in konfig)
populazio_estiloak = komuna.populazio_estiloak(
    artxiboa_du, populazioa_ezkutuan=denetan_artxiboa and not komuna.aukerak()["populazioa"])


def dinamikoak(g):
    trazak = []
    for k in konfig:
        trazak += komuna.populazio_trazak(k["urratsak"][min(g, k["G"])])
    for gakoa, _ in metrika_errenkadak:
        trazak += [serie(k["urratsak"], gakoa, g) for k in konfig]
    return trazak


estiloak, kokapenak = [], []
for i, (r, c) in enumerate(pop_kokapenak):
    estiloak += populazio_estiloak if i == 0 else komuna.populazio_estiloak(artxiboa_du, legenda=False)
    kokapenak += [(r, c)] * 4
for m, _ in enumerate(metrika_errenkadak):
    for k in konfig:
        estiloak.append(dict(name=k["etiketa"], mode="lines", showlegend=(m == 0),
                             legend="legend2", line=dict(color=k["kolorea"], width=2)))
        kokapenak.append((pop_errenkadak + m + 1, 1))

hasierakoak = dinamikoak(0)
for traza, estiloa, (r, c) in zip(hasierakoak, estiloak, kokapenak):
    traza.update(**estiloa)
    fig.add_trace(traza, row=r, col=c)
dinamiko_idx = list(range(oinarri_kop, oinarri_kop + len(hasierakoak)))
fig.frames = [go.Frame(name=str(g), data=dinamikoak(g), traces=dinamiko_idx)
              for g in range(G + 1)]

for r, c in pop_kokapenak:
    komuna.populazio_ardatzak(fig, r, c)
hv_opt = komuna.hv_optimoa()
igd_max = max((u["igd"] for k in konfig for u in k["urratsak"] if not math.isnan(u["igd"])),
              default=1)
tarteak = {"hv": [0, 105], "hv_balioa": [0, hv_opt * 1.05], "igd": [0, igd_max * 1.05]}
for m, (gakoa, _) in enumerate(metrika_errenkadak):
    r = pop_errenkadak + m + 1
    fig.update_xaxes(range=[0, G], row=r, col=1)
    fig.update_yaxes(range=tarteak[gakoa], ticksuffix=" %" if gakoa == "hv" else None, row=r, col=1)
fig.update_xaxes(title_text=urrats_izena, row=errenkadak, col=1)
fig.add_hline(y=hv_opt, line=dict(dash="dash", width=1, color="#9aa0a6"),
              annotation_text=f"optimoa {hv_opt:.4f}", annotation_position="bottom right",
              row=pop_errenkadak + 2, col=1)

guztira = pop_altuera * pop_errenkadak + metrika_altuera * len(metrika_errenkadak) + 120
behea_pop = fig.get_subplot(pop_errenkadak, 1).yaxis.domain[0]
fig.update_layout(
    height=guztira,
    margin=dict(t=40, l=60, r=20, b=40),
    legend=dict(x=0.01, y=behea_pop + 0.005, xanchor="left", yanchor="bottom",
                bgcolor="rgba(127,127,127,0.15)"),
    legend2=dict(x=0.99, y=1.0, xanchor="right", yanchor="bottom", orientation="h",
                 yref="paper", bgcolor="rgba(127,127,127,0.15)"),
)
# Lerroen legenda lehen metrika-grafikoaren izenburuaren gainean, ez zapaltzeko
fig.update_layout(legend2=dict(
    y=fig.get_subplot(pop_errenkadak + 1, 1).yaxis.domain[1] + 30 / guztira * 1.0 + 0.004))
komuna.animazio_kontrolak(fig, G, urrats_izena)
komuna.grafikoa_erakutsi(fig)

if len({k["G"] for k in konfig}) > 1:
    st.info(f"Konfigurazioek {urrats_izena.lower()} kopuru desberdina dute: laburrenak bere "
            "azken egoeran jarraitzen du besteak amaitu arte.")

# ---------------------------------------------------------------------------
# 2. irudia: fronte guztiak plano berean
# ---------------------------------------------------------------------------
st.subheader("Denak plano berean")
st.caption("Konfigurazio bakoitzaren 1. frontea (artxiboa duten algoritmoetan, artxiboarena) "
           "helburuen espazio berean, bere kolorearekin, urratsez urrats.")


def fronte_trazak(g):
    trazak = []
    for k in konfig:
        u = k["urratsak"][min(g, k["G"])]
        x, y = komuna.puntuak(u["fronte_csv"])
        trazak.append(go.Scatter(x=x, y=y))
    return trazak


fig2 = go.Figure()
fig2.set_subplots(rows=1, cols=1)
oinarri2 = komuna.oinarri_trazak(fig2, 1, 1)
for traza, k in zip(fronte_trazak(0), konfig):
    traza.update(name=k["etiketa"], mode="markers",
                 marker=dict(size=8, color=k["kolorea"], line=dict(width=0.5, color="white")),
                 hovertemplate=f"{k['etiketa']}<br>f₁ %{{x:.3f}}<br>f₂ %{{y:.3f}}<extra></extra>")
    fig2.add_trace(traza, row=1, col=1)
fig2.frames = [go.Frame(name=str(g), data=fronte_trazak(g),
                        traces=list(range(oinarri2, oinarri2 + N)))
               for g in range(G + 1)]
komuna.populazio_ardatzak(fig2, 1, 1)
fig2.update_layout(
    height=680, margin=dict(t=20, l=60, r=20, b=40),
    legend=dict(x=0.01, y=0.01, xanchor="left", yanchor="bottom",
                bgcolor="rgba(127,127,127,0.15)"),
)
komuna.animazio_kontrolak(fig2, G, urrats_izena)
komuna.grafikoa_erakutsi(fig2)
