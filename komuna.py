"""
Orrien arteko kode komuna: problema, exekuzioa (cache-arekin),
parametro-hautatzailea eta Plotly irudien laguntzaileak.
"""
import math
import random

import plotly.graph_objects as go
import streamlit as st

import analisia
import metrikak
import nsga2
from algoritmoak import ALGORITMOAK, EZ_BIDERAGARRIA
from metrikak import ERREF_PUNTUA, HV_ATALASEA
KOLOREAK = {
    "ez_bid": "#9aa0a6",
    "beste": "#4c78a8",
    "fronte": "#e45756",
    "hv": "#54a24b",
    "igd": "#b279a2",
    "A": "#2a9d8f",
    "B": "#f58518",
}

POPULAZIO_ESTILOAK = [
    dict(name="Ez bideragarriak", mode="markers",
         marker=dict(symbol="x", size=6, color=KOLOREAK["ez_bid"])),
    dict(name="Bideragarriak (beste fronteak)", mode="markers",
         marker=dict(size=7, color=KOLOREAK["beste"], opacity=0.75)),
    dict(name="1. frontea (ez-menderatuak)", mode="markers",
         marker=dict(size=8, color=KOLOREAK["fronte"], line=dict(width=0.5, color="white"))),
]


# ---------------------------------------------------------------------------
# Problema: eskualde bideragarria eta benetako frontea (erreferentzia)
# ---------------------------------------------------------------------------
@st.cache_data
def eskualde_bideragarria(pausoa=0.006, muga=1.25):
    k = int(muga / pausoa) + 1
    bx, by = [], []
    for i in range(k):
        a = i * pausoa
        for j in range(k):
            b = j * pausoa
            if nsga2.bideragarria((a, b)):
                bx.append(a)
                by.append(b)
    return bx, by


@st.cache_data
def benetako_frontea(n=1500, muga=1.25):
    """x1 bakoitzeko x2 bideragarri txikiena, eta horietatik ez-menderatuak."""
    return list(analisia.benetako_frontea(n, muga))


# ---------------------------------------------------------------------------
# Algoritmoa exekutatu eta urrats bakoitzeko datuak eta metrikak kalkulatu
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Algoritmoa exekutatzen...")
def exekutatu(algoritmoa, parametroak, hazia):
    historia = ALGORITMOAK[algoritmoa]["exekutatu"](dict(parametroak), hazia)

    erref_frontea = benetako_frontea()
    erref_igd = erref_frontea[::4]           # IGD azkarrago kalkulatzeko
    hv_optimoa = metrikak.hiperbolumena(erref_frontea, ERREF_PUNTUA)

    urratsak = []
    for populazioa in historia:
        bideragarriak = [(x, f) for x, f in populazioa if f[0] != EZ_BIDERAGARRIA]
        ez_bid = [x for x, f in populazioa if f[0] == EZ_BIDERAGARRIA]
        F = [f for _, f in bideragarriak]
        lehena = set(metrikak.ez_menderatuak(F))
        fronte = sorted(bideragarriak[i][0] for i in lehena)
        beste = [x for i, (x, _) in enumerate(bideragarriak) if i not in lehena]
        fronte_f = [F[i] for i in lehena]
        urratsak.append({
            "fronte": fronte,
            "beste": beste,
            "ez_bid": ez_bid,
            "hv": 100 * metrikak.hiperbolumena(fronte_f, ERREF_PUNTUA) / hv_optimoa,
            "igd": metrikak.igd(fronte_f, erref_igd),
            "n_bid": len(bideragarriak),
            "n_fronte": len(fronte),
        })
    return urratsak


def konbergentzia_urratsa(urratsak, atalasea=HV_ATALASEA):
    """Hiperbolumenak `atalasea` lehen aldiz gainditzen duen urratsa (None, inoiz ez bada)."""
    for g, u in enumerate(urratsak):
        if u["hv"] >= atalasea:
            return g
    return None


# ---------------------------------------------------------------------------
# Interfazeko laguntzaileak
# ---------------------------------------------------------------------------
def aukerak():
    """app.py-ko albo-barran aukeratutako bistaratze-aukerak."""
    return st.session_state["aukerak"]


def albo_edukiontzia():
    """Orri bakoitzaren parametroak albo-barraren goialdean jartzeko edukiontzia."""
    return st.session_state["parametroen_lekua"]


def algoritmo_hautatzailea(edukiontzia, gakoa):
    """Algoritmoa aukeratzeko widgeta (formulariotik kanpo: parametro-zerrenda
    algoritmoaren araberakoa da). Itzultzen du: (algoritmoa, info)."""
    algoritmoa = edukiontzia.selectbox("Algoritmoa", list(ALGORITMOAK), key=f"{gakoa}-alg")
    info = ALGORITMOAK[algoritmoa]
    edukiontzia.caption(info["deskribapena"])
    return algoritmoa, info


def algoritmo_parametroak(gakoa, algoritmoa, lehenetsiak=None):
    """Algoritmoaren parametroen slider-ak. Itzultzen du: parametroak tupla gisa."""
    lehenetsiak = lehenetsiak or {}
    parametroak = {}
    for k, etiketa, bmin, bmax, lehen, pausoa in ALGORITMOAK[algoritmoa]["parametroak"]:
        parametroak[k] = st.slider(etiketa, bmin, bmax, lehenetsiak.get(k, lehen),
                                   step=pausoa, key=f"{gakoa}-{algoritmoa}-{k}")
    return tuple(sorted(parametroak.items()))


def hazia_widgetak(gakoa, lehenetsiak=None,
                   etiketa="Ausazko hazia (exekuzio bakoitzean berria)",
                   finko_etiketa="Hazia (ausazkoa ez bada)"):
    """Ausazko/finko hazia aukeratzeko widgetak. Itzultzen du: hazia (int)."""
    lehenetsiak = lehenetsiak or {}
    ausazkoa = st.checkbox(etiketa, value=lehenetsiak.get("ausazkoa", True),
                           key=f"{gakoa}-ausazkoa")
    finkoa = int(st.number_input(finko_etiketa, value=lehenetsiak.get("hazia", 1),
                                 step=1, key=f"{gakoa}-hazia"))
    # Ausazko hazia rerun bakoitzean ateratzen da, baina exekutatutako_konfigurazioa-k
    # Exekutatu sakatzean bakarrik gordetzen du: beraz, botoi-sakatze bakoitzeko bat.
    return random.randrange(1_000_000) if ausazkoa else finkoa


def parametro_widgetak(gakoa, algoritmoa, lehenetsiak=None):
    """Algoritmoaren parametroen widgetak eta hazia, uneko testuinguruan (adib.
    formulario baten barruan). Itzultzen du: (parametroak tupla gisa, hazia)."""
    parametroak = algoritmo_parametroak(gakoa, algoritmoa, lehenetsiak)
    return parametroak, hazia_widgetak(gakoa, lehenetsiak)


def exekutatutako_konfigurazioa(gakoa, oraingoa, botoia_sakatuta):
    """Exekutatu botoia sakatzean uneko konfigurazioa gorde eta itzuli; bestela,
    azkenekoz exekutatutakoa (None, oraindik ezer exekutatu ez bada). Horrela,
    orrira sartzean edo parametroak editatzean ez da ezer exekutatzen."""
    if botoia_sakatuta:
        st.session_state[gakoa] = oraingoa
    return st.session_state.get(gakoa)


def exekutatzeko_zain(izenburua, botoia):
    """Oraindik ezer exekutatu ez denean: izenburua eta jarraibidea erakutsi eta gelditu."""
    st.title(izenburua)
    st.info(f"Parametroak konfiguratu eta sakatu **{botoia}** algoritmoa exekutatzeko.",
            icon=":material/tune:")
    st.stop()


def puntuak(zerrenda):
    # Zerrenda hutsa bada [None] itzuli: bestela Plotly-k animazioan aurreko puntuak uzten ditu
    if not zerrenda:
        return [None], [None]
    return [p[0] for p in zerrenda], [p[1] for p in zerrenda]


def populazio_trazak(urratsa):
    """Urrats bateko populazioaren 3 trazak (ez bideragarriak, besteak, 1. frontea)."""
    return [go.Scatter(x=x, y=y) for x, y in
            (puntuak(urratsa["ez_bid"]), puntuak(urratsa["beste"]), puntuak(urratsa["fronte"]))]


def oinarri_trazak(fig, row, col, showlegend=True):
    """Eskualde bideragarria eta benetako frontea (finkoak). Gehitutako traza kopurua itzultzen du."""
    a = aukerak()
    bx, by = eskualde_bideragarria()
    erref = benetako_frontea() if a["erref"] else []
    fig.add_trace(go.Scatter(x=bx, y=by, mode="markers", name="Eskualde bideragarria",
                             hoverinfo="skip", showlegend=showlegend,
                             marker=dict(size=3, color="rgba(160,160,160,0.25)")),
                  row=row, col=col)
    fig.add_trace(go.Scatter(x=[p[0] for p in erref], y=[p[1] for p in erref],
                             mode="markers", name="Benetako frontea", hoverinfo="skip",
                             showlegend=showlegend,
                             marker=dict(size=3, color=a["erref_kolorea"])),
                  row=row, col=col)
    return 2


def populazio_ardatzak(fig, row, col):
    """Helburuen espazioko ardatzak: finkoak eta eskala berekoak."""
    muga = math.pi if aukerak()["dominioa"] else 1.25
    x_izena = fig.get_subplot(row, col).xaxis.plotly_name.replace("axis", "")
    fig.update_xaxes(range=[0, muga], title_text="f₁ = x₁", constrain="domain", row=row, col=col)
    fig.update_yaxes(range=[0, muga], title_text="f₂ = x₂", scaleanchor=x_izena, scaleratio=1,
                     constrain="domain", row=row, col=col)


def animazio_kontrolak(fig, G, urrats_izena):
    """Hasi / Gelditu botoiak eta urratsen slider-a."""
    abiadura = aukerak()["abiadura"]
    berehala = dict(frame=dict(duration=0, redraw=False), mode="immediate",
                    transition=dict(duration=0))
    fig.update_layout(
        updatemenus=[dict(
            type="buttons", direction="left", x=0, y=-0.06, xanchor="left", yanchor="top",
            buttons=[
                dict(label="▶ Hasi", method="animate",
                     args=[None, dict(frame=dict(duration=abiadura, redraw=False),
                                      transition=dict(duration=0), fromcurrent=True)]),
                dict(label="⏸ Gelditu", method="animate", args=[[None], berehala]),
            ],
        )],
        sliders=[dict(
            active=0, x=0.12, y=-0.04, len=0.88, xanchor="left", yanchor="top",
            currentvalue=dict(prefix=f"{urrats_izena}: "),
            steps=[dict(label=str(g), method="animate", args=[[str(g)], berehala])
                   for g in range(G + 1)],
        )],
    )


def grafikoa_erakutsi(fig):
    """Plotly irudia erakutsi, modu argia/iluna kontuan hartuta."""
    if aukerak()["argia"]:
        fig.update_layout(template="plotly_white")
        st.plotly_chart(fig, width="stretch", theme=None)
    else:
        st.plotly_chart(fig, width="stretch")
