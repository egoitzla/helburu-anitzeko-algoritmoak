"""
Exekuzio anitzeko analisia: hainbat algoritmo, bakoitza N aldiz (hazi berdinekin),
prozesu paraleloetan. Metriken dentsitatea eta azken soluzioen dentsitatea frontean
zehar, kurba gaussiarren bidez (KDE). CSV deskarga: lerro bat exekuzioko.
"""
import math
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import analisia
import komuna
from algoritmoak import ALGORITMOAK
from komuna import HV_ATALASEA

ALG_KOLOREAK = ["#4c78a8", "#f58518", "#54a24b", "#e45756", "#b279a2", "#72b7b2"]

# (zutabea CSVan, etiketa, handiagoa hobea?)
METRIKAK = [
    ("hv_ehunekoa", "Hiperbolumena (%) ↑", True),
    ("hv_balioa", "Hiperbolumena (balioa) ↑", True),
    ("igd", "IGD ↓", False),
    ("konbergentzia_belaunaldia", f"HV ≥ {HV_ATALASEA:.0f} % belaunaldia ↓", False),
    ("denbora_s", "Denbora (s) ↓", False),
]



def gardena(hex_kolorea, alfa=0.25):
    """#rrggbb -> rgba(r, g, b, alfa), kurben azpiko betegarrirako."""
    r, g, b = (int(hex_kolorea[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alfa})"


def kde(balioak, x, banda=None):
    """Kernel gaussiarreko dentsitate-estimazioa (KDE) `x` puntuetan.
    Banda-zabalera lehenetsia: Scott-en araua (1.06 · σ · n^(-1/5))."""
    v = np.asarray(balioak, dtype=float)
    if banda is None:
        sigma = v.std(ddof=1) if len(v) > 1 else 0.0
        banda = 1.06 * sigma * len(v) ** -0.2
    if banda <= 0:
        return None
    z = (np.asarray(x)[:, None] - v[None, :]) / banda
    return np.exp(-0.5 * z ** 2).sum(axis=1) / (len(v) * banda * np.sqrt(2 * np.pi))


st.title("Dentsitatea: exekuzio anitzeko analisia")
st.caption(
    "Aukeratutako algoritmo bakoitza N aldiz exekutatzen da, prozesu paraleloetan. "
    "Exekuzio bakoitzak hazi bera erabiltzen du algoritmo guztietan, konparaketa bidezkoa izan dadin."
)
komuna.albo_edukiontzia().caption("Konfigurazioa orri nagusian aukeratzen da.")

# ---------------------------------------------------------------------------
# Konfigurazioa
# ---------------------------------------------------------------------------
cpu = os.cpu_count() or 1
with st.expander("Konfigurazioa", expanded="dents-emaitzak" not in st.session_state):
    # Formulariotik kanpo: parametroen zutabeak hautatutako algoritmoen araberakoak dira
    hautatuak = st.multiselect("Algoritmoak", list(ALGORITMOAK), default=list(ALGORITMOAK),
                               key="dents-algoritmoak")
    with st.form("dents-formularioa", border=False):
        parametroak = {}
        if hautatuak:
            for alg, zutabea in zip(hautatuak, st.columns(len(hautatuak), gap="large")):
                with zutabea:
                    st.markdown(f"**{alg}**")
                    parametroak[alg] = dict(komuna.algoritmo_parametroak("dents", alg))
        st.divider()
        z1, z2, z3 = st.columns(3, gap="large")
        with z1:
            exekuzioak = int(st.number_input("Exekuzio kopurua (algoritmo bakoitzeko)",
                                             min_value=2, max_value=500, value=10, step=1,
                                             key="dents-exekuzioak"))
        with z2:
            langileak = st.slider("Prozesu paraleloak", 1, cpu, cpu, key="dents-langileak")
        with z3:
            oinarria = komuna.hazia_widgetak("dents", etiketa="Ausazko hasierako hazia",
                                             finko_etiketa="Hasierako hazia (ausazkoa ez bada)")
        st.caption("k. exekuzioak `hasierako hazia + k − 1` hazia erabiltzen du, algoritmo guztietan berdina.")
        sakatuta = st.form_submit_button("▶ Exekutatu", type="primary", width="stretch")

if sakatuta:
    if not hautatuak:
        st.warning("Aukeratu gutxienez algoritmo bat.")
    else:
        haziak = [oinarria + k for k in range(exekuzioak)]
        guztira = len(hautatuak) * exekuzioak
        barra = st.progress(0.0, text=f"0 / {guztira} exekuzio")
        emaitzak = analisia.exekutatu_guztiak(
            parametroak, haziak, langileak,
            aurrerapena=lambda e, g: barra.progress(e / g, text=f"{e} / {g} exekuzio"))
        barra.empty()
        st.session_state["dents-emaitzak"] = {
            "emaitzak": emaitzak,
            "parametroak": parametroak,
            "algoritmoak": list(hautatuak),
            "haziak": haziak,
        }
        st.rerun()  # Konfigurazio-panela tolestuta erakusteko

res = st.session_state.get("dents-emaitzak")
if res is None:
    st.info("Algoritmoak eta parametroak aukeratu, exekuzio kopurua zehaztu eta sakatu "
            "**▶ Exekutatu**.", icon=":material/tune:")
    st.stop()

algoritmoak = res["algoritmoak"]
kolorea = {alg: ALG_KOLOREAK[i % len(ALG_KOLOREAK)] for i, alg in enumerate(algoritmoak)}

# ---------------------------------------------------------------------------
# Datu-taula: lerro bat exekuzioko
# ---------------------------------------------------------------------------
lerroak = []
for alg, k, hazia, m, _ in res["emaitzak"]:
    lerroa = {"algoritmoa": alg, "exekuzioa": k, "hazia": hazia}
    lerroa.update({f"p_{izena}": balioa for izena, balioa in res["parametroak"][alg].items()})
    lerroa.update({
        "hv_ehunekoa": m["hv"],
        "hv_balioa": m["hv_balioa"],
        "igd": m["igd"],
        "konbergentzia_belaunaldia": m["konbergentzia"],
        "denbora_s": m["denbora_s"],
    })
    lerroak.append(lerroa)
df = pd.DataFrame(lerroak)
# Zutabeen ordena: identifikazioa, parametroak (p_*), metrikak
p_zutabeak = [z for z in df.columns if z.startswith("p_")]
df = df[["algoritmoa", "exekuzioa", "hazia"] + p_zutabeak + [z for z, _, _ in METRIKAK]]

st.caption(f"{len(res['haziak'])} exekuzio algoritmo bakoitzeko · haziak "
           f"{res['haziak'][0]}–{res['haziak'][-1]}")

# ---------------------------------------------------------------------------
# Laburpena: batez bestekoa ± desbideratzea
# ---------------------------------------------------------------------------
st.subheader("Laburpena")


def formatua(zutabea):
    return "{:.2f}" if zutabea in ("hv_ehunekoa",
                                    "konbergentzia_belaunaldia", "denbora_s") else "{:.5f}"


laburpena = []
for alg in algoritmoak:
    d = df[df["algoritmoa"] == alg]
    lerroa = {"Algoritmoa": alg}
    for zutabea, etiketa, _ in METRIKAK:
        balioak = d[zutabea].dropna()
        f = formatua(zutabea)
        if balioak.empty:
            lerroa[etiketa] = "—"
        else:
            lerroa[etiketa] = f"{f.format(balioak.mean())} ± {f.format(balioak.std(ddof=1) if len(balioak) > 1 else 0)}"
    iritsi = d["konbergentzia_belaunaldia"].notna().sum()
    lerroa[f"HV ≥ {HV_ATALASEA:.0f} % lortu"] = f"{iritsi} / {len(d)}"
    laburpena.append(lerroa)
st.dataframe(pd.DataFrame(laburpena), hide_index=True, width="stretch")
st.caption("Batez bestekoa ± desbideratze estandarra exekuzioetan zehar. Konbergentziak HV atalasera "
           "iritsi diren exekuzioak bakarrik hartzen ditu kontuan.")

# ---------------------------------------------------------------------------
# Metriken dentsitatea: kurba gaussiarrak (KDE)
# ---------------------------------------------------------------------------
st.subheader("Metriken dentsitatea")
fig = make_subplots(rows=math.ceil(len(METRIKAK) / 2), cols=2, subplot_titles=[e for _, e, _ in METRIKAK],
                    vertical_spacing=0.1, horizontal_spacing=0.06)
for i, (zutabea, _, _) in enumerate(METRIKAK):
    r, c = divmod(i, 2)
    guztiak = df[zutabea].dropna().to_numpy(dtype=float)
    if guztiak.size == 0:
        continue
    behe, goi = guztiak.min(), guztiak.max()
    tartea = goi - behe if goi > behe else max(abs(goi) * 0.02, 1e-6)
    x = np.linspace(behe - 0.25 * tartea, goi + 0.25 * tartea, 300)
    for alg in algoritmoak:
        balioak = df.loc[df["algoritmoa"] == alg, zutabea].dropna().to_numpy(dtype=float)
        if balioak.size == 0:
            continue
        y = kde(balioak, x)
        if y is None:
            # Exekuzio guztiek balio bera: marra bertikala
            fig.add_trace(go.Scatter(x=[balioak[0]] * 2, y=[0, 1], mode="lines",
                                     line=dict(color=kolorea[alg], width=3),
                                     name=alg, legendgroup=alg, showlegend=(i == 0),
                                     hovertemplate=f"{alg}: denak %{{x:.5g}}<extra></extra>"),
                      row=r + 1, col=c + 1)
            continue
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines", fill="tozeroy",
                                 line=dict(color=kolorea[alg], width=2),
                                 fillcolor=gardena(kolorea[alg]), name=alg, legendgroup=alg, showlegend=(i == 0),
                                 hovertemplate=f"{alg}<br>%{{x:.5g}}<extra></extra>"),
                      row=r + 1, col=c + 1)
        # Batez bestekoa: marra etena
        fig.add_vline(x=float(balioak.mean()), line=dict(color=kolorea[alg], width=1, dash="dash"),
                      row=r + 1, col=c + 1)
    fig.update_yaxes(showticklabels=False, rangemode="tozero", row=r + 1, col=c + 1)
fig.update_layout(height=300 * math.ceil(len(METRIKAK) / 2) + 40, margin=dict(l=10, r=10, t=40, b=10),
                  legend=dict(orientation="h", y=-0.06, x=0), hovermode="x unified")
komuna.grafikoa_erakutsi(fig)
st.caption("Kurba bakoitza algoritmo baten exekuzioen banaketa da (kernel gaussiarreko dentsitate-"
           "estimazioa): gailurra = balio ohikoena, zabalera = aldakortasuna. Marra etenak batez "
           "bestekoa. Kurba estu eta altua = algoritmo egonkorra; kurbak gainjarrita = alde "
           "handirik ez. Exekuzio guztiek balio bera badute, marra bertikal bat ageri da.")

# ---------------------------------------------------------------------------
# Soluzioen dentsitatea frontean
# ---------------------------------------------------------------------------
st.subheader("Soluzioen dentsitatea frontean")


@st.cache_data
def frontearen_luzera():
    """Benetako frontea eta puntu bakoitzaren posizio normalizatua frontean zehar
    (arku-luzera, 0 = goi-ezkerreko muturra, 1 = behe-eskuinekoa). Fronteko hutsuneak
    (zati ez-optimoak) ez dira luzeran kontatzen."""
    R = np.asarray(komuna.benetako_frontea(), dtype=float)
    tarteak = np.sqrt((np.diff(R, axis=0) ** 2).sum(axis=1))
    tarteak[tarteak > 0.02] = 0.0          # hutsuneak saltatu
    s = np.concatenate([[0.0], np.cumsum(tarteak)])
    return R, s / s[-1]


R, s_erref = frontearen_luzera()
banda = st.select_slider("Leuntzea (kernel gaussiarraren banda-zabalera)",
                         options=[0.005, 0.01, 0.02, 0.03, 0.05, 0.08], value=0.02,
                         key="dents-banda")
xs = np.linspace(0, 1, 400)

ezker, eskuin = st.columns([3, 2], gap="medium")

# 1D: dentsitatea frontean zehar (1 = banaketa uniformea)
fig = go.Figure()
fig.add_hline(y=1, line=dict(dash="dash", width=1, color="#9aa0a6"),
              annotation_text="uniformea", annotation_position="top left")
puntuak_alg = {}
for alg in algoritmoak:
    P = np.asarray([p for a, *_, frontea in res["emaitzak"] if a == alg for p in frontea],
                   dtype=float).reshape(-1, 2)
    puntuak_alg[alg] = P
    if len(P) == 0:
        continue
    hurbilena = np.sqrt(((P[:, None, :] - R[None, :, :]) ** 2).sum(axis=2)).argmin(axis=1)
    posizioak = s_erref[hurbilena]
    # Ertzetan islatu (0 eta 1), muturretan dentsitatea erdira ez jaisteko
    islatuak = np.concatenate([posizioak, -posizioak, 2 - posizioak])
    dentsitatea = kde(islatuak, xs, banda) * 3
    fig.add_trace(go.Scatter(x=xs, y=dentsitatea, name=alg, mode="lines",
                             line=dict(color=kolorea[alg], width=2.5),
                             hovertemplate=f"{alg}<br>posizioa %{{x:.2f}}<br>dentsitatea %{{y:.2f}}<extra></extra>"))
fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10),
                  xaxis=dict(title="Posizioa frontean (0 = f₁ txikiena, 1 = f₂ txikiena)", range=[0, 1]),
                  yaxis=dict(title="Dentsitatea (1 = uniformea)", rangemode="tozero"),
                  legend=dict(orientation="h", y=1.08, x=0))
with ezker:
    komuna.grafikoa_erakutsi(fig)

# 2D: exekuzio guztietako puntuak helburuen espazioan, gainjarrita
fig = go.Figure()
if komuna.aukerak()["erref"]:
    fig.add_trace(go.Scatter(x=R[:, 0], y=R[:, 1], mode="lines", name="Benetako frontea",
                             line=dict(width=1, color=komuna.aukerak()["erref_kolorea"]),
                             hoverinfo="skip"))
for alg in algoritmoak:
    P = puntuak_alg[alg]
    fig.add_trace(go.Scatter(x=P[:, 0], y=P[:, 1], mode="markers", name=alg,
                             marker=dict(size=4, color=kolorea[alg], opacity=0.25),
                             hovertemplate=f"{alg}<br>f₁ %{{x:.3f}}<br>f₂ %{{y:.3f}}<extra></extra>"))
fig.update_layout(height=420, margin=dict(l=10, r=10, t=30, b=10), showlegend=False,
                  xaxis=dict(title="f₁", range=[0, 1.1], constrain="domain"),
                  yaxis=dict(title="f₂", range=[0, 1.1], scaleanchor="x", scaleratio=1,
                             constrain="domain"))
with eskuin:
    komuna.grafikoa_erakutsi(fig)

st.caption("Exekuzio guztietako azken 1. fronteko puntuak elkartuta. Ezkerrean, puntu bakoitza "
           "benetako fronteko punturik hurbilenera proiektatzen da eta frontean zeharreko "
           "posizioaren (arku-luzera normalizatua, hutsuneak kontatu gabe) dentsitate gaussiarra (KDE) "
           "marrazten da: 1 inguruko lerro laua = soluzioak uniformeki banatuta; gailurrak = pilaketak; "
           "0 = estali gabeko zatiak. Eskuinean, puntu guztiak gainjarrita (zenbat eta ilunago, "
           "orduan eta puntu gehiago).")

# ---------------------------------------------------------------------------
# Datuak eta CSV deskarga
# ---------------------------------------------------------------------------
st.subheader("Exekuzioak")
st.dataframe(df, hide_index=True, width="stretch")
st.download_button("⬇ CSV deskargatu (lerro bat exekuzioko)", df.to_csv(index=False).encode("utf-8"),
                   file_name="dentsitatea_exekuzioak.csv", mime="text/csv")
