"""REFERENCIA CONGELADA del ejemplo mínimo. No se edita: su sello (sha256) está en ejemplo_minimo/config.toml.

Sistema bajo estudio: un agente epsilon-greedy en un bandido de dos brazos con recompensa gaussiana. A mitad de la
corrida (`invertir_en`) los dos brazos intercambian sus medias, sin aviso. Python puro, determinista por semilla.
"""
import random


def corre(semilla, pasos=4000, eps=0.1, alpha=None, medias=(0.8, 0.2), sigma=0.1, invertir_en=None):
    """Devuelve las trayectorias completas (para el arnés de identidad) y el estado final.

    alpha=None usa el promedio muestral (paso 1/n); un número usa paso constante.
    """
    rng = random.Random(semilla)
    if invertir_en is None:
        invertir_en = pasos // 2
    Q = [0.0, 0.0]
    n = [0, 0]
    mu = list(medias)
    recompensas, acciones, eps_aplicado = [], [], []
    for t in range(pasos):
        if t == invertir_en:
            mu = mu[::-1]
        e = eps
        eps_aplicado.append(e)
        if rng.random() < e:
            a = rng.randrange(2)
        else:
            a = 0 if Q[0] >= Q[1] else 1
        r = rng.gauss(mu[a], sigma)
        n[a] += 1
        paso = alpha if alpha is not None else 1.0 / n[a]
        Q[a] += paso * (r - Q[a])
        recompensas.append(r)
        acciones.append(a)
    return dict(recompensas=recompensas, acciones=acciones, Q=Q, eps_aplicado=eps_aplicado)
