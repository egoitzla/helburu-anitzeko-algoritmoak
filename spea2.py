"""
SPEA2 algoritmoaren oinarrizko bertsioa (Zitzler, Laumanns eta Thiele, 2001).

Problema (ikus README.md):
    min f1(x1, x2) = x1
    min f2(x1, x2) = x2

    Murriztapenak:
        C1: x1^2 + x2^2 - 1 - 0.1*cos(16*arctan(x1/x2)) >= 0
        C2: (x1 - 0.5)^2 + (x2 - 0.5)^2 <= 0.5
        0 <= x1, x2 <= pi

    Soluzio bat bideragarria ez bada, bi helburuei 10 balioa esleitzen zaie.

Python estandarra bakarrik erabiltzen da (math, random). matplotlib instalatuta
badago, azken Pareto frontea irudikatzen da.

NSGA-II-rekin alderatuta, problema eta operadore genetikoak (SBX eta mutazio
polinomiala) berdinak dira; aldatzen dena hau da:
    - Kanpoko artxiboa (N_ARTXIBOA tamaina finkoa) ez-menderatuak gordetzeko.
    - Egokitasuna: F(i) = H(i) + D(i)
        S(i) = i-k menderatzen dituen soluzio kopurua (indarra)
        H(i) = i menderatzen duten soluzioen S-en batura (egokitasun gordina)
        D(i) = 1 / (sigma_i^k + 2), k. auzokide hurbilenarekiko distantzia (dentsitatea)
    - Ingurune-hautaketa: ez-menderatuak artxibora; gehiegi badira, trunkatu
      (auzokide hurbilena duena kendu behin eta berriz); gutxiegi badira,
      menderatu onenekin bete.
"""

import math
import random

# ---------------------------------------------------------------------------
# Parametroak
# ---------------------------------------------------------------------------
POP_TAMAINA = 100        # Populazioaren tamaina (N)
ARTXIBO_TAMAINA = 100    # Artxiboaren tamaina (N̄)
BELAUNALDIAK = 200       # Belaunaldi kopurua
GURUTZAKETA_PROB = 0.9   # Gurutzaketa probabilitatea
MUTAZIO_PROB = 0.5       # Mutazio probabilitatea (aldagai bakoitzeko: 1/n, n=2)
ETA_C = 20               # SBX gurutzaketaren banaketa-indizea
ETA_M = 20               # Mutazio polinomialaren banaketa-indizea
BEHE_MUGA = 0.0
GOI_MUGA = math.pi
EZ_BIDERAGARRIA = 10.0   # Soluzio ez bideragarriei esleitzen zaien balioa
HAZIA = random.randrange(1_000_000)  # Ausazko hazia (finkatu, adib. 1, emaitza errepikatzeko)
COS_KOEF = 0.1          # C1 murriztapeneko cos-aren koefizientea (TNK problema)


# ---------------------------------------------------------------------------
# Problema: helburu funtzioak eta murriztapenak
# ---------------------------------------------------------------------------
def c1(x1, x2):
    # atan2(x1, x2) = arctan(x1/x2) x2 > 0 denean, eta x2 = 0 kasuan ere ondo dabil
    return x1 ** 2 + x2 ** 2 - 1 - COS_KOEF * math.cos(16 * math.atan2(x1, x2))


def c2(x1, x2):
    return (x1 - 0.5) ** 2 + (x2 - 0.5) ** 2


def bideragarria(x):
    x1, x2 = x
    return c1(x1, x2) >= 0 and c2(x1, x2) <= 0.5


def ebaluatu(x):
    """Helburu funtzioen balioak itzultzen ditu: (f1, f2)."""
    if not bideragarria(x):
        return (EZ_BIDERAGARRIA, EZ_BIDERAGARRIA)
    return (x[0], x[1])


# ---------------------------------------------------------------------------
# Dominantzia
# ---------------------------------------------------------------------------
def menderatzen_du(a, b):
    """True, a-k b menderatzen badu (minimizazioa)."""
    hobea_edo_berdina = all(ai <= bi for ai, bi in zip(a, b))
    hobea_bat = any(ai < bi for ai, bi in zip(a, b))
    return hobea_edo_berdina and hobea_bat


def distantzia(a, b):
    """Distantzia euklidearra helburuen espazioan."""
    return math.dist(a, b)


# ---------------------------------------------------------------------------
# SPEA2 egokitasuna: F(i) = H(i) + D(i)
# ---------------------------------------------------------------------------
def egokitasuna(helburuak):
    """
    Soluzio bakoitzaren egokitasuna (txikiagoa = hobea) eta distantzia-matrizea.
    F(i) < 1  <=>  i ez-menderatua da.
    """
    n = len(helburuak)

    # Indarra S(i): i-k menderatzen dituen soluzio kopurua
    menderatzaileak = [[] for _ in range(n)]   # menderatzaileak[i]: i menderatzen dutenak
    indarra = [0] * n
    for i in range(n):
        for j in range(n):
            if i != j and menderatzen_du(helburuak[i], helburuak[j]):
                indarra[i] += 1
                menderatzaileak[j].append(i)

    # Egokitasun gordina H(i): i menderatzen dutenen indarren batura
    gordina = [sum(indarra[j] for j in menderatzaileak[i]) for i in range(n)]

    # Dentsitatea D(i) = 1 / (sigma_i^k + 2), k = sqrt(N + N̄)
    dist = [[distantzia(helburuak[i], helburuak[j]) for j in range(n)] for i in range(n)]
    k = int(math.sqrt(POP_TAMAINA + ARTXIBO_TAMAINA))
    k = min(max(k, 1), n - 1)
    dentsitatea = []
    for i in range(n):
        auzokideak = sorted(dist[i][j] for j in range(n) if j != i)
        dentsitatea.append(1.0 / (auzokideak[k - 1] + 2.0))

    F = [gordina[i] + dentsitatea[i] for i in range(n)]
    return F, dist


# ---------------------------------------------------------------------------
# Ingurune-hautaketa: hurrengo artxiboa (N̄ indibiduo)
# ---------------------------------------------------------------------------
def trunkatu(hautagaiak, dist, tamaina):
    """
    Ez-menderatu gehiegi daudenean: auzokide hurbilena (berdinketan, 2. hurbilena,
    etab.) duen soluzioa kendu behin eta berriz, `tamaina` geratu arte.
    """
    geratzen = list(hautagaiak)
    # Soluzio bakoitzeko gainerakoekiko distantziak, txikienetik handienera
    auzokideak = {i: sorted(dist[i][j] for j in geratzen if j != i) for i in geratzen}
    while len(geratzen) > tamaina:
        # Distantzia-zerrendak hiztegi-ordenan alderatu: txikiena da kentzekoa
        kendu = min(geratzen, key=lambda i: auzokideak[i])
        geratzen.remove(kendu)
        del auzokideak[kendu]
        for i in geratzen:
            auzokideak[i].remove(dist[i][kendu])
    return geratzen


def ingurune_hautaketa(populazioa, helburuak, F, dist):
    """Ez-menderatuak (F < 1) artxibora; gero trunkatu edo menderatuekin bete."""
    ez_menderatuak = [i for i in range(len(F)) if F[i] < 1]
    if len(ez_menderatuak) > ARTXIBO_TAMAINA:
        hautatuak = trunkatu(ez_menderatuak, dist, ARTXIBO_TAMAINA)
    else:
        # Gutxiegi: F txikiena duten menderatuekin bete
        hautatuak = sorted(range(len(F)), key=lambda i: F[i])[:ARTXIBO_TAMAINA]
    return ([populazioa[i] for i in hautatuak],
            [helburuak[i] for i in hautatuak],
            [F[i] for i in hautatuak])


# ---------------------------------------------------------------------------
# Operadore genetikoak (NSGA-II-ren berdinak, txapelketa izan ezik)
# ---------------------------------------------------------------------------
def txapelketa_bitarra(F):
    """Bi indibiduo ausaz hartu (itzulerarekin) eta F txikiena duena itzuli."""
    a = random.randrange(len(F))
    b = random.randrange(len(F))
    return a if F[a] <= F[b] else b


def mugatu(v):
    return min(max(v, BEHE_MUGA), GOI_MUGA)


def sbx_gurutzaketa(g1, g2):
    """Simulated Binary Crossover (SBX)."""
    if random.random() > GURUTZAKETA_PROB:
        return g1[:], g2[:]
    s1, s2 = [], []
    for x1, x2 in zip(g1, g2):
        u = random.random()
        if u <= 0.5:
            beta = (2 * u) ** (1 / (ETA_C + 1))
        else:
            beta = (1 / (2 * (1 - u))) ** (1 / (ETA_C + 1))
        s1.append(mugatu(0.5 * ((1 + beta) * x1 + (1 - beta) * x2)))
        s2.append(mugatu(0.5 * ((1 - beta) * x1 + (1 + beta) * x2)))
    return s1, s2


def mutazio_polinomiala(x):
    """Mutazio polinomiala, aldagai bakoitzean MUTAZIO_PROB probabilitatearekin."""
    y = x[:]
    tartea = GOI_MUGA - BEHE_MUGA
    for i in range(len(y)):
        if random.random() < MUTAZIO_PROB:
            u = random.random()
            if u < 0.5:
                delta = (2 * u) ** (1 / (ETA_M + 1)) - 1
            else:
                delta = 1 - (2 * (1 - u)) ** (1 / (ETA_M + 1))
            y[i] = mugatu(y[i] + delta * tartea)
    return y


def ondorengoak_sortu(artxiboa, F):
    """Artxibotik txapelketaz gurasoak hartu eta N ondorengo sortu."""
    ondorengoak = []
    while len(ondorengoak) < POP_TAMAINA:
        g1 = artxiboa[txapelketa_bitarra(F)]
        g2 = artxiboa[txapelketa_bitarra(F)]
        s1, s2 = sbx_gurutzaketa(g1, g2)
        ondorengoak.append(mutazio_polinomiala(s1))
        if len(ondorengoak) < POP_TAMAINA:
            ondorengoak.append(mutazio_polinomiala(s2))
    return ondorengoak


# ---------------------------------------------------------------------------
# SPEA2 algoritmo nagusia
# ---------------------------------------------------------------------------
def spea2(historia=None, isilik=False):
    """
    historia: zerrenda bat ematen bada, belaunaldi bakoitzeko artxiboa
    (A, A_helb) gordetzen da bertan (0. elementua = hasierako populaziotik
    lortutako artxiboa).
    """
    random.seed(HAZIA)

    # 1. Hasierako populazioa ausaz sortu eta ebaluatu; artxiboa hutsik
    P = [[random.uniform(BEHE_MUGA, GOI_MUGA) for _ in range(2)]
         for _ in range(POP_TAMAINA)]
    P_helb = [ebaluatu(x) for x in P]
    A, A_helb = [], []

    for belaunaldia in range(BELAUNALDIAK + 1):
        # 2. Egokitasuna P ∪ A osoan kalkulatu
        R, R_helb = P + A, P_helb + A_helb
        F, dist = egokitasuna(R_helb)

        # 3. Ingurune-hautaketa: hurrengo artxiboa
        A, A_helb, A_F = ingurune_hautaketa(R, R_helb, F, dist)
        if historia is not None:
            historia.append(([x[:] for x in A], list(A_helb)))

        if not isilik and belaunaldia > 0 and belaunaldia % 20 == 0:
            bider = sum(1 for f in A_helb if f[0] != EZ_BIDERAGARRIA)
            ez_mend = sum(1 for f in A_F if f < 1)
            print(f"Belaunaldia {belaunaldia:4d} | artxiboan bideragarriak: {bider:3d} "
                  f"| ez-menderatuak: {ez_mend:3d}")

        # 4. Amaiera-irizpidea
        if belaunaldia == BELAUNALDIAK:
            break

        # 5-6. Gurasoen hautaketa (artxibotik) eta aldakuntza: P berria
        P = ondorengoak_sortu(A, A_F)
        P_helb = [ebaluatu(x) for x in P]

    # 7. Azken Pareto frontea: artxiboko soluzio ez-menderatu bideragarriak
    pareto = [(A[i], A_helb[i]) for i in range(len(A))
              if A_F[i] < 1 and A_helb[i][0] != EZ_BIDERAGARRIA]
    pareto.sort(key=lambda s: s[1][0])
    return pareto


def irudikatu(pareto, fitxategia="pareto_frontea_spea2.png"):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib ez dago instalatuta: irudia ez da sortu.")
        return
    f1 = [s[1][0] for s in pareto]
    f2 = [s[1][1] for s in pareto]
    plt.figure(figsize=(6, 6))
    plt.scatter(f1, f2, s=15, c="tab:blue", label="SPEA2 Pareto frontea")
    plt.xlabel("f1 = x1")
    plt.ylabel("f2 = x2")
    plt.xlim(0, 1.2)
    plt.ylim(0, 1.2)
    plt.gca().set_aspect("equal")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.title("SPEA2: Pareto frontea")
    plt.savefig(fitxategia, dpi=150, bbox_inches="tight")
    print(f"Irudia gordeta: {fitxategia}")


if __name__ == "__main__":
    pareto = spea2()
    print(f"Hazia: {HAZIA}")
    print(f"\nPareto fronteko soluzio kopurua: {len(pareto)}")
    for x, f in pareto[:10]:
        print(f"  x = ({x[0]:.4f}, {x[1]:.4f})  ->  f = ({f[0]:.4f}, {f[1]:.4f})")
    if len(pareto) > 10:
        print("  ...")
    irudikatu(pareto)
