"""
Differential Evolution helburu anitzeko problemetarako: GDE3 algoritmoa
(Kukkonen eta Lampinen, 2005), oinarrizko bertsioa.

Problema eta NSGA-II-ren sailkapen ez-menderatua + pilaketa-distantzia
nsga2.py-tik hartzen dira; hemen DE-ren berezko zatiak bakarrik daude:

    Belaunaldi bakoitzean, populazioko x_i bakoitzeko (helburu-bektorea):
      1. Bektore mutantea (DE/rand/1):  v = x_r1 + F * (x_r2 - x_r3)
         r1, r2, r3: populazioko ausazko soluzioak, elkarren artean eta i-rekin
         desberdinak.
      2. Proba-bektorea (gurutzaketa binomiala): posizio bakoitza CR
         probabilitatearekin v-tik hartzen da, bestela x_i-tik (j_rand posizioa
         beti v-tik, gutxienez bat aldatzeko).
      3. Hautaketa (GDE3):
           u-k x_i ahulki menderatzen badu  -> u sartzen da x_i-ren ordez
           x_i-k u menderatzen badu         -> x_i geratzen da
           bestela (ez-menderatuak)         -> biak geratzen dira
    Populazioa N baino handiagoa bada, NSGA-II-n bezala murrizten da: fronte
    ez-menderatuak eta, azken frontean, pilaketa-distantzia handienak.
"""

import random

import nsga2
from nsga2 import BEHE_MUGA, EZ_BIDERAGARRIA, GOI_MUGA, ebaluatu, menderatzen_du

# ---------------------------------------------------------------------------
# Parametroak
# ---------------------------------------------------------------------------
POP_TAMAINA = 100        # Populazioaren tamaina (NP)
BELAUNALDIAK = 200       # Belaunaldi kopurua
F = 0.5                  # Eskala-faktorea, (0, 1] tartean
CR = 0.9                 # Gurutzaketa-probabilitatea (posizio bakoitzeko)
HAZIA = random.randrange(1_000_000)  # Ausazko hazia (finkatu, adib. 1, emaitza errepikatzeko)


def mugatu(v):
    return min(max(v, BEHE_MUGA), GOI_MUGA)


def ahulki_menderatzen_du(a, b):
    """True, a helburu guztietan b baino okerragoa ez bada."""
    return all(ai <= bi for ai, bi in zip(a, b))


# ---------------------------------------------------------------------------
# DE operadoreak
# ---------------------------------------------------------------------------
def bektore_mutantea(P, i):
    """DE/rand/1: v = x_r1 + F * (x_r2 - x_r3)."""
    r1, r2, r3 = random.sample([k for k in range(len(P)) if k != i], 3)
    return [mugatu(P[r1][j] + F * (P[r2][j] - P[r3][j])) for j in range(len(P[i]))]


def proba_bektorea(x, v):
    """Gurutzaketa binomiala: posizio bakoitza CR probabilitatearekin v-tik."""
    j_rand = random.randrange(len(x))
    return [v[j] if (random.random() <= CR or j == j_rand) else x[j] for j in range(len(x))]


# ---------------------------------------------------------------------------
# Populazioa N-ra murriztu (NSGA-II-ren irizpidea)
# ---------------------------------------------------------------------------
def murriztu(populazioa, helburuak, tamaina):
    fronteak, _ = nsga2.sailkapen_ez_menderatua(helburuak)
    hautatuak = []
    for fronte in fronteak:
        if len(hautatuak) + len(fronte) <= tamaina:
            hautatuak.extend(fronte)
        else:
            dist = nsga2.pilaketa_distantzia(fronte, helburuak)
            falta = tamaina - len(hautatuak)
            hautatuak.extend(sorted(fronte, key=lambda i: dist[i], reverse=True)[:falta])
            break
    return [populazioa[i] for i in hautatuak], [helburuak[i] for i in hautatuak]


# ---------------------------------------------------------------------------
# GDE3 algoritmo nagusia
# ---------------------------------------------------------------------------
def gde3(historia=None, isilik=False):
    """
    historia: zerrenda bat ematen bada, belaunaldi bakoitzeko populazioa
    (P, P_helb) gordetzen da bertan (0. elementua = hasierako populazioa).
    """
    random.seed(HAZIA)

    # 1. Hasierako populazioa ausaz sortu eta ebaluatu
    P = [[random.uniform(BEHE_MUGA, GOI_MUGA) for _ in range(2)]
         for _ in range(POP_TAMAINA)]
    P_helb = [ebaluatu(x) for x in P]
    if historia is not None:
        historia.append(([x[:] for x in P], list(P_helb)))

    for belaunaldia in range(1, BELAUNALDIAK + 1):
        hurrengoa, hurrengoa_helb = [], []
        for i, (x, fx) in enumerate(zip(P, P_helb)):
            # 2. Mutantea eta proba-bektorea sortu, eta ebaluatu
            u = proba_bektorea(x, bektore_mutantea(P, i))
            fu = ebaluatu(u)

            # 3. Hautaketa: u vs x_i
            if ahulki_menderatzen_du(fu, fx):
                hurrengoa.append(u); hurrengoa_helb.append(fu)
            elif menderatzen_du(fx, fu):
                hurrengoa.append(x); hurrengoa_helb.append(fx)
            else:
                hurrengoa += [x, u]; hurrengoa_helb += [fx, fu]

        # 4. N baino gehiago badaude, murriztu
        P, P_helb = hurrengoa, hurrengoa_helb
        if len(P) > POP_TAMAINA:
            P, P_helb = murriztu(P, P_helb, POP_TAMAINA)
        if historia is not None:
            historia.append(([x[:] for x in P], list(P_helb)))

        if not isilik and belaunaldia % 20 == 0:
            bider = sum(1 for f in P_helb if f[0] != EZ_BIDERAGARRIA)
            print(f"Belaunaldia {belaunaldia:4d} | bideragarriak: {bider:3d}")

    # 5. Azken Pareto frontea (lehen fronteko soluzio bideragarriak)
    fronteak, _ = nsga2.sailkapen_ez_menderatua(P_helb)
    pareto = [(P[i], P_helb[i]) for i in fronteak[0] if P_helb[i][0] != EZ_BIDERAGARRIA]
    pareto.sort(key=lambda s: s[1][0])
    return pareto


if __name__ == "__main__":
    pareto = gde3()
    print(f"Hazia: {HAZIA}")
    print(f"\nPareto fronteko soluzio kopurua: {len(pareto)}")
    for x, f in pareto[:10]:
        print(f"  x = ({x[0]:.4f}, {x[1]:.4f})  ->  f = ({f[0]:.4f}, {f[1]:.4f})")
    if len(pareto) > 10:
        print("  ...")
