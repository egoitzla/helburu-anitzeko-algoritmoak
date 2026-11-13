"""
Exekuzio anitzeko analisia: algoritmo bakoitza hainbat aldiz (hazi desberdinekin)
exekutatu, prozesu paraleloetan, eta exekuzio bakoitzeko metrikak itzuli.

Modulu honek ez du Streamlit erabiltzen: prozesu langileek inportatzen dute.
"""
import contextlib
import functools
import math
import multiprocessing
import os
import sys
import time
import types
from concurrent.futures import ProcessPoolExecutor, as_completed

import metrikak
import nsga2
from algoritmoak import ALGORITMOAK, EZ_BIDERAGARRIA
from metrikak import ERREF_PUNTUA, HV_ATALASEA


@functools.lru_cache(maxsize=None)
def benetako_frontea(n=1500, muga=1.25):
    """x1 bakoitzeko x2 bideragarri txikiena, eta horietatik ez-menderatuak."""
    ertza = []
    for i in range(n + 1):
        a = muga * i / n
        for j in range(n + 1):
            b = muga * j / n
            if nsga2.bideragarria((a, b)):
                ertza.append((a, b))
                break
    frontea, onena = [], float("inf")
    for a, b in sorted(ertza):
        if b < onena:
            frontea.append((a, b))
            onena = b
    return tuple(frontea)


def lehen_frontea(populazioa):
    """Populazio bateko soluzio bideragarri ez-menderatuen helburuak."""
    F = [f for _, f in populazioa if f[0] != EZ_BIDERAGARRIA]
    return [F[i] for i in metrikak.ez_menderatuak(F)]


def exekuzio_bat(algoritmoa, parametroak, hazia):
    """
    Algoritmoa behin exekutatu eta metrikak kalkulatu.
    Itzultzen du: metriken hiztegia eta azken fronteko puntuak.
    """
    hasiera = time.perf_counter()
    historia = ALGORITMOAK[algoritmoa]["exekutatu"](dict(parametroak), hazia)
    denbora = time.perf_counter() - hasiera

    erref = benetako_frontea()
    hv_optimoa = metrikak.hiperbolumena(erref, ERREF_PUNTUA)

    # Konbergentzia: HV-ak atalasea lehen aldiz gainditzen duen urratsa
    konb = None
    for g, populazioa in enumerate(historia):
        hv_g = 100 * metrikak.hiperbolumena(lehen_frontea(populazioa), ERREF_PUNTUA) / hv_optimoa
        if hv_g >= HV_ATALASEA:
            konb = g
            break

    frontea = sorted(lehen_frontea(historia[-1]))
    return {
        "hv": 100 * metrikak.hiperbolumena(frontea, ERREF_PUNTUA) / hv_optimoa,
        "hv_balioa": metrikak.hiperbolumena(frontea, ERREF_PUNTUA),
        "igd": metrikak.igd(frontea, erref),
        "tartekatzea": metrikak.tartekatzea(frontea),
        "n_fronte": len(frontea),
        "konbergentzia": konb if konb is not None else math.nan,
        "denbora_s": denbora,
    }, frontea


def _lana(algoritmoa, parametroak, exekuzioa, hazia):
    metrikak_, frontea = exekuzio_bat(algoritmoa, parametroak, hazia)
    return algoritmoa, exekuzioa, hazia, metrikak_, frontea


@contextlib.contextmanager
def _main_modulurik_gabe():
    """
    Streamlit-ek aplikazioa `__main__` modulu gisa exekutatzen du, eta "spawn" moduko
    prozesu berriek `__main__` berriz inportatzen dute: app.py langile bakoitzean
    exekutatuko litzateke. Prozesuak sortu bitartean `__main__` hutsa jartzen da.
    """
    jatorrizkoa = sys.modules["__main__"]
    sys.modules["__main__"] = types.ModuleType("__main__")
    try:
        yield
    finally:
        sys.modules["__main__"] = jatorrizkoa


def exekutatu_guztiak(konfigurazioak, haziak, langileak=None, aurrerapena=None):
    """
    konfigurazioak: {algoritmoa: parametroak (hiztegia)}
    haziak: exekuzio bakoitzeko hazia (algoritmo guztiek berdinak erabiltzen dituzte).
    aurrerapena: funtzioa(eginda, guztira), aukerakoa.
    Itzultzen du: emaitzen zerrenda (algoritmoa, exekuzioa, hazia, metrikak, frontea),
    algoritmoaren eta exekuzioaren arabera ordenatuta.
    """
    lanak = [(alg, tuple(sorted(p.items())), k, h)
             for alg, p in konfigurazioak.items() for k, h in enumerate(haziak, start=1)]
    langileak = max(1, min(langileak or os.cpu_count() or 1, len(lanak)))
    emaitzak = []
    testuingurua = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=langileak, mp_context=testuingurua) as exekutatzailea:
        with _main_modulurik_gabe():
            etorkizunak = [exekutatzailea.submit(_lana, *lana) for lana in lanak]
        for eginda, etorkizuna in enumerate(as_completed(etorkizunak), start=1):
            emaitzak.append(etorkizuna.result())
            if aurrerapena:
                aurrerapena(eginda, len(lanak))
    orden = list(konfigurazioak)
    emaitzak.sort(key=lambda e: (orden.index(e[0]), e[1]))
    return emaitzak
