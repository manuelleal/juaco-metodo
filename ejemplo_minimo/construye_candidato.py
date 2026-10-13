"""Construye candidato.py desde referencia.py POR ANCLAS (regla 2 de PROTOCOLO.md).

  python ejemplo_minimo/construye_candidato.py          escribe candidato.py e imprime su sello

Qué garantiza: (a) el origen es exactamente la referencia sellada (si su sha cambió, aborta); (b) cada ancla aparece
UNA vez en el origen (si no, aborta: el origen no es el que se creía); (c) todo lo demás queda byte a byte igual.
candidato.py es un archivo GENERADO: no se edita a mano. corre.py vuelve a construirlo en memoria y aborta si no
coincide con el que está en disco.

Perilla nueva: k (ganancia de la sorpresa sobre epsilon). Perilla de lectura: beta (constante del promedio móvil de la
sorpresa). Apagado: k = 0.0, con el que el candidato debe ser bit a bit la referencia (arnes_identidad.py).
Memoria nueva: un escalar (sb, la sorpresa media).
"""
import hashlib
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIGEN = os.path.join(AQUI, 'referencia.py')
DESTINO = os.path.join(AQUI, 'candidato.py')
SHA_ORIGEN = 'e6155bea36a2799b'   # el sello de referencia.py en config.toml

ANCLAS = [
    # (texto que debe aparecer UNA vez en el origen, texto que lo sustituye)
    ('"""REFERENCIA CONGELADA del ejemplo mínimo. No se edita: su sello (sha256) está en ejemplo_minimo/config.toml.\n',
     '"""CANDIDATO del ejemplo mínimo. GENERADO por construye_candidato.py desde referencia.py: no se edita a mano.\n'
     '\n'
     'Cambio: epsilon sube con la sorpresa media sb = promedio móvil de |r - Q[a]| (perilla k, apagada en 0.0).\n'),
    ("sigma=0.1, invertir_en=None):",
     "sigma=0.1, invertir_en=None, k=0.0, beta=0.05):"),
    ("    n = [0, 0]\n",
     "    n = [0, 0]\n"
     "    sb = 0.0   # memoria nueva: la sorpresa media (causal: el paso t usa la de los pasos anteriores)\n"),
    ("        e = eps\n",
     "        e = min(1.0, eps + k * sb) if k else eps\n"),
    ("        n[a] += 1\n",
     "        s = abs(r - Q[a])\n"
     "        n[a] += 1\n"),
    ("        Q[a] += paso * (r - Q[a])\n",
     "        Q[a] += paso * (r - Q[a])\n"
     "        sb = (1.0 - beta) * sb + beta * s\n"),
]


def sha16_bytes(b):
    return hashlib.sha256(b).hexdigest()[:16]


def construye():
    with open(ORIGEN, 'rb') as f:
        crudo = f.read()
    if sha16_bytes(crudo) != SHA_ORIGEN:
        sys.exit('ABORTO: referencia.py no es la sellada (%s != %s)' % (sha16_bytes(crudo), SHA_ORIGEN))
    texto = crudo.decode('utf-8')
    for viejo, nuevo in ANCLAS:
        n = texto.count(viejo)
        if n != 1:
            sys.exit('ABORTO: el ancla aparece %d veces (se exige 1): %r' % (n, viejo[:60]))
        texto = texto.replace(viejo, nuevo)
    return texto.encode('utf-8')


if __name__ == '__main__':
    b = construye()
    with open(DESTINO, 'wb') as f:
        f.write(b)
    print('candidato.py escrito, sha16 %s (origen %s)' % (sha16_bytes(b), SHA_ORIGEN))
