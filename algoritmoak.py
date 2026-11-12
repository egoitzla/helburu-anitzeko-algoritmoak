"""
Aplikazioan erakusten diren algoritmoen erregistroa.

Algoritmo berri bat gehitzeko, ALGORITMOAK hiztegian sarrera bat gehitu:
  - "deskribapena": testu laburra.
  - "urratsa": iterazioaren izena ("Belaunaldia", "Iterazioa"...).
  - "parametroak": [(gakoa, etiketa, min, max, lehenetsia, pausoa), ...]
  - "exekutatu": funtzioa(parametroak: dict, hazia: int) -> historia,
        non historia[k] = k. urratseko soluzioen zerrenda [(x, f), ...]
        eta soluzio ez bideragarriek f = (EZ_BIDERAGARRIA, EZ_BIDERAGARRIA) duten.
"""
import gde3
import nsga2
import spea2


def _nsga2_exekutatu(p, hazia):
    nsga2.POP_TAMAINA = p["n"]
    nsga2.BELAUNALDIAK = p["belaunaldiak"]
    nsga2.GURUTZAKETA_PROB = p["pc"]
    nsga2.MUTAZIO_PROB = p["pm"]
    nsga2.ETA_C = p["eta_c"]
    nsga2.ETA_M = p["eta_m"]
    nsga2.HAZIA = hazia
    historia = []
    nsga2.nsga2(historia=historia, isilik=True)
    return [list(zip(P, P_helb)) for P, P_helb in historia]


def _spea2_exekutatu(p, hazia):
    spea2.POP_TAMAINA = p["n"]
    spea2.ARTXIBO_TAMAINA = p["artxiboa"]
    spea2.BELAUNALDIAK = p["belaunaldiak"]
    spea2.GURUTZAKETA_PROB = p["pc"]
    spea2.MUTAZIO_PROB = p["pm"]
    spea2.ETA_C = p["eta_c"]
    spea2.ETA_M = p["eta_m"]
    spea2.HAZIA = hazia
    historia = []
    spea2.spea2(historia=historia, isilik=True)
    return [list(zip(A, A_helb)) for A, A_helb in historia]


def _gde3_exekutatu(p, hazia):
    gde3.POP_TAMAINA = p["n"]
    gde3.BELAUNALDIAK = p["belaunaldiak"]
    gde3.F = p["F"]
    gde3.CR = p["CR"]
    gde3.HAZIA = hazia
    historia = []
    gde3.gde3(historia=historia, isilik=True)
    return [list(zip(P, P_helb)) for P, P_helb in historia]


ALGORITMOAK = {
    "NSGA-II": {
        "deskribapena": "Sailkapen ez-menderatua + pilaketa-distantzia, SBX gurutzaketa "
                        "eta mutazio polinomiala.",
        "urratsa": "Belaunaldia",
        "parametroak": [
            ("n", "Populazioaren tamaina (N)", 20, 300, nsga2.POP_TAMAINA, 10),
            ("belaunaldiak", "Belaunaldiak", 10, 400, nsga2.BELAUNALDIAK, 10),
            ("pc", "Gurutzaketa probabilitatea $p_c$", 0.0, 1.0, nsga2.GURUTZAKETA_PROB, 0.05),
            ("pm", "Mutazio probabilitatea $p_m$ (aldagaiko)", 0.0, 1.0, nsga2.MUTAZIO_PROB, 0.05),
            ("eta_c", "η_c (SBX)", 1, 100, nsga2.ETA_C, 1),
            ("eta_m", "η_m (mutazioa)", 1, 100, nsga2.ETA_M, 1),
        ],
        "exekutatu": _nsga2_exekutatu,
    },
    "SPEA2": {
        "deskribapena": "Kanpoko artxiboa + egokitasuna F = H + D (indarra eta k-NN "
                        "dentsitatea), artxiboaren trunkatzea, SBX gurutzaketa eta "
                        "mutazio polinomiala. Belaunaldi bakoitzean artxiboa erakusten da.",
        "urratsa": "Belaunaldia",
        "parametroak": [
            ("n", "Populazioaren tamaina (N)", 20, 300, spea2.POP_TAMAINA, 10),
            ("artxiboa", "Artxiboaren tamaina (N̄)", 10, 300, spea2.ARTXIBO_TAMAINA, 10),
            ("belaunaldiak", "Belaunaldiak", 10, 400, spea2.BELAUNALDIAK, 10),
            ("pc", "Gurutzaketa probabilitatea $p_c$", 0.0, 1.0, spea2.GURUTZAKETA_PROB, 0.05),
            ("pm", "Mutazio probabilitatea $p_m$ (aldagaiko)", 0.0, 1.0, spea2.MUTAZIO_PROB, 0.05),
            ("eta_c", "η_c (SBX)", 1, 100, spea2.ETA_C, 1),
            ("eta_m", "η_m (mutazioa)", 1, 100, spea2.ETA_M, 1),
        ],
        "exekutatu": _spea2_exekutatu,
    },
    "DE (GDE3)": {
        "deskribapena": "Differential Evolution helburu anitzekin: bektore mutantea "
                        "v = x_r1 + F·(x_r2 − x_r3), gurutzaketa binomiala (CR) eta GDE3 "
                        "hautaketa (gurasoa vs proba-bektorea, dominantziaz), NSGA-II-ren "
                        "murrizketarekin.",
        "urratsa": "Belaunaldia",
        "parametroak": [
            ("n", "Populazioaren tamaina (NP)", 20, 300, gde3.POP_TAMAINA, 10),
            ("belaunaldiak", "Belaunaldiak", 10, 400, gde3.BELAUNALDIAK, 10),
            ("F", "Eskala-faktorea F", 0.05, 1.0, gde3.F, 0.05),
            ("CR", "Gurutzaketa probabilitatea CR", 0.0, 1.0, gde3.CR, 0.05),
        ],
        "exekutatu": _gde3_exekutatu,
    },
}

EZ_BIDERAGARRIA = nsga2.EZ_BIDERAGARRIA
