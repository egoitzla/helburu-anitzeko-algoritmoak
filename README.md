# Helburu anitzeko algoritmoak

Helburu anitzeko algoritmo ebolutiboak (**NSGA-II**, **SPEA2** eta **DE / GDE3**) TNK problemaren
gainean, eta haien bilakaera, konparaketa eta analisi estatistikoa egiteko **Streamlit** aplikazio bat.

## Problema (TNK)

Bi helburu minimizatu:

- $f_1(x_1, x_2) = x_1$
- $f_2(x_1, x_2) = x_2$

Murriztapenak:

- $C_1(x_1,x_2) = x_1^2 + x_2^2 - 1 - 0.1\cos\left(16\arctan\frac{x_1}{x_2}\right) \ge 0$
- $C_2(x_1,x_2) = (x_1 - 0.5)^2 + (x_2 - 0.5)^2 \le 0.5$
- $0 \le x_1, x_2 \le \pi$

Soluzio bat bideragarria ez bada, bi helburuei **10** balioa esleitzen zaie.

## Algoritmoak

| Algoritmoa | Fitxategia | Laburpena |
|---|---|---|
| NSGA-II | [`nsga2.py`](nsga2.py), [`nsga2.ipynb`](nsga2.ipynb) | Sailkapen ez-menderatua + pilaketa-distantzia, SBX gurutzaketa eta mutazio polinomiala. |
| SPEA2 | [`spea2.py`](spea2.py), [`spea2.ipynb`](spea2.ipynb) | Kanpoko artxiboa, egokitasuna $F = H + D$ (indarra + k-NN dentsitatea) eta artxiboaren trunkatzea. |
| DE (GDE3) | [`gde3.py`](gde3.py) | Differential Evolution: $v = x_{r_1} + F\,(x_{r_2} - x_{r_3})$, gurutzaketa binomiala (CR) eta dominantzian oinarritutako hautaketa. |

Algoritmo guztiak Python estandarrarekin idatzita daude (`math`, `random`).

## Aplikazioa

| Orria | Zer egiten du |
|---|---|
| **Hasiera** | Problema, eskualde bideragarria, benetako Pareto frontea eta algoritmoen aurkezpena. |
| **Bilakaera** | Algoritmo bat konfiguratu eta exekutatu; populazioa eta metrikak (hiperbolumena, IGD) belaunaldiz belaunaldi animatuta. |
| **Konparaketa** | Bi algoritmo edo konfigurazio alboz albo, animazio sinkronizatu batean. |
| **Dentsitatea** | Hainbat algoritmo N aldiz exekutatu prozesu paraleloetan (hazi berdinekin): metriken eta fronteko soluzioen dentsitate gaussiarrak, laburpen-taula eta CSV deskarga (lerro bat exekuzioko). |

### Exekutatu

[uv](https://docs.astral.sh/uv/) erabiliz:

```bash
uv sync
uv run streamlit run app.py
```

Edo `pip` erabiliz:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Algoritmoak aplikaziorik gabe ere exekuta daitezke: `python nsga2.py`, `python spea2.py` edo `python gde3.py`.

## Egitura

```
app.py            Aplikazioaren sarrera eta nabigazioa
orriak/           Aplikazioaren orriak (hasiera, bilakaera, konparaketa, dentsitatea)
algoritmoak.py    Algoritmoen erregistroa (algoritmo berriak hemen gehitzen dira)
komuna.py         Orrien arteko kode komuna (exekuzioa, widget-ak, Plotly laguntzaileak)
analisia.py       Exekuzio anitzeko analisia, prozesu paraleloetan
metrikak.py       Hiperbolumena, IGD, tartekatzea (spacing) eta ez-menderatuen iragazkia
nsga2.py, spea2.py, gde3.py   Algoritmoak
*.ipynb           Algoritmoen azalpena urratsez urrats
```

### Algoritmo berri bat gehitzea

`algoritmoak.py`-ko `ALGORITMOAK` hiztegian sarrera bat gehitu (deskribapena, parametroak eta
`exekutatu(parametroak, hazia) -> historia` funtzioa). Automatikoki agertuko da orri guztietan.
