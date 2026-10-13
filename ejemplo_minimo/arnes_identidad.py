"""ARNÉS DE IDENTIDAD del ejemplo mínimo. Se corre ANTES de mirar números (corre.py lo llama y aborta si falla).

  python ejemplo_minimo/arnes_identidad.py

Casos (semillas 1-5 x 4 escenarios = 20 comparaciones por caso):
  J1  candidato con k=0 (apagado) == referencia, en TODAS las trayectorias (recompensas, acciones, epsilon) y en Q;
  J2  candidato con k=0 y beta=0.5 == referencia: la lectura de la sorpresa SÓLO MIDE (beta no toca nada si k=0);
  C1  control que DEBE fallar: candidato con k=0.3 difiere de la referencia en al menos 18 de 20 comparaciones
      (si no difiere, la perilla está desconectada).
Escenarios: valores por defecto del módulo; los de la batería de la referencia; inversión temprana; paso 1/n.
No imprime ninguna medida de resultado.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import candidato  # noqa: E402
import referencia  # noqa: E402
from bateria_referencia import KWARGS_REFERENCIA  # noqa: E402

SEMILLAS = [1, 2, 3, 4, 5]
ESCENARIOS = {
    'defectos_del_modulo': dict(pasos=1500),
    'bateria_referencia': dict(KWARGS_REFERENCIA, pasos=1500),
    'inversion_temprana': dict(KWARGS_REFERENCIA, pasos=1500, invertir_en=300),
    'paso_1_sobre_n': dict(KWARGS_REFERENCIA, pasos=1500, alpha=None),
}
CLAVES = ['recompensas', 'acciones', 'eps_aplicado', 'Q']


def iguales(a, b):
    return all(a[c] == b[c] for c in CLAVES)


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    casos ={'J1 k=0 == referencia': [0, 0], 'J2 k=0,beta=0.5 == referencia': [0, 0], 'C1 k=0.3 difiere': [0, 0]}
    for s in SEMILLAS:
        for kw in ESCENARIOS.values():
            ref = referencia.corre(s, **kw)
            for nombre, perillas, quiere_igual in (('J1 k=0 == referencia', dict(k=0.0), True),
                                                   ('J2 k=0,beta=0.5 == referencia', dict(k=0.0, beta=0.5), True),
                                                   ('C1 k=0.3 difiere', dict(k=0.3), False)):
                c = candidato.corre(s, **dict(kw, **perillas))
                casos[nombre][0] += iguales(ref, c) == quiere_igual
                casos[nombre][1] += 1
    mal = False
    for nombre, (a, b) in casos.items():
        if nombre.startswith('C1'):
            bien = a >= b - 2
            print('%s: %d/%d comparaciones distintas%s' % (nombre, a, b, '' if bien else '  <-- PERILLA DESCONECTADA'))
        else:
            bien = a == b
            print('%s: %d/%d idénticas%s' % (nombre, a, b, ' (BIT A BIT)' if bien else '  <-- DIFERENCIA'))
        mal |= not bien
    print('ARNÉS:', 'BIEN' if not mal else 'MAL')
    return 0 if not mal else 1


if __name__ == '__main__':
    sys.exit(main())
