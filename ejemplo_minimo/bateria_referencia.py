"""Batería de la referencia: los argumentos EXACTOS con los que se corre la referencia en este bloque.

Ojo: referencia.corre tiene sus propios valores por defecto (eps=0.1, alpha=None, sigma=0.1). Esta batería pasa otros,
explícitamente. Por eso "por defecto" no existe (regla 12 de PROTOCOLO.md).
"""
import referencia

KWARGS_REFERENCIA = dict(pasos=4000, eps=0.01, alpha=0.1, medias=(0.8, 0.2), sigma=0.05)


def corre(semilla, **extra):
    return referencia.corre(semilla, **dict(KWARGS_REFERENCIA, **extra))
