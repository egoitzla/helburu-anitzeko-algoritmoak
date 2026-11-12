"""
Helburu anitzeko optimizazioko metrikak (2 helburu, minimizazioa).

Algoritmoaren menpekoak ez dira: edozein algoritmoren populazioarekin erabil daitezke.
"""
import math

import numpy as np

ERREF_PUNTUA = (1.2, 1.2)   # Hiperbolumenaren erreferentzia-puntua
HV_ATALASEA = 95.0          # "Konbergentzia-abiadura": HV honetara iristeko urratsa


def ez_menderatuak(helburuak):
    """Inork menderatzen ez dituen soluzioen indizeak."""
    emaitza = []
    for i, a in enumerate(helburuak):
        menderatua = False
        for j, b in enumerate(helburuak):
            if i != j and all(bk <= ak for ak, bk in zip(a, b)) and any(bk < ak for ak, bk in zip(a, b)):
                menderatua = True
                break
        if not menderatua:
            emaitza.append(i)
    return emaitza


def hiperbolumena(puntuak, erref):
    """
    Bi helburuko hiperbolumena: puntuek menderatzen duten eta `erref` puntuak
    mugatzen duen azalera. Puntuak ez-menderatuak izan behar dira.
    """
    barrukoak = sorted(p for p in puntuak if p[0] < erref[0] and p[1] < erref[1])
    hv, aurreko_f2 = 0.0, erref[1]
    for f1, f2 in barrukoak:
        if f2 < aurreko_f2:
            hv += (erref[0] - f1) * (aurreko_f2 - f2)
            aurreko_f2 = f2
    return hv


def igd(puntuak, erreferentzia):
    """
    Inverted Generational Distance: erreferentziako fronteko puntu bakoitzetik
    multzoko punturik hurbilenera dagoen distantziaren batez bestekoa.
    Txikiagoa = hobea (0 = benetako frontea guztiz estalita).
    """
    if not puntuak:
        return math.nan
    A = np.asarray(erreferentzia, dtype=float)[:, None, :]
    B = np.asarray(puntuak, dtype=float)[None, :, :]
    return float(np.sqrt(((A - B) ** 2).sum(axis=2)).min(axis=1).mean())


def tartekatzea(puntuak):
    """
    Spacing: auzokide hurbilenarekiko distantzien desbideratze estandarra.
    Txikiagoa = soluzioak uniformeago banatuta. 2 puntu baino gutxiago: NaN.
    """
    if len(puntuak) < 2:
        return math.nan
    P = np.asarray(puntuak, dtype=float)
    D = np.sqrt(((P[:, None, :] - P[None, :, :]) ** 2).sum(axis=2))
    np.fill_diagonal(D, np.inf)
    return float(D.min(axis=1).std())
