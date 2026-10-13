"""Batería del candidato, copiada de bateria_referencia.py y con las perillas nuevas."""
import candidato

PERILLAS = dict(k=0.3, beta=0.05)
KWARGS_CANDIDATO = dict(pasos=4000, eps=0.01, medias=(0.8, 0.2), sigma=0.05, **PERILLAS)


def corre(semilla, **extra):
    return candidato.corre(semilla, **dict(KWARGS_CANDIDATO, **extra))
