# -*- coding: utf-8 -*-
"""ARNÉS DE IDENTIDAD, ejemplo comentado. Se corre ANTES de mirar números. Un proceso, segundos, sin dependencias.

    python herramientas/arnes_identidad_ejemplo.py [semillas]      por defecto 0,1,2,3,4

Es la estructura del arnés de JUACO `exploratorio/investigacion_20261009/cuarentena_consecuencia/arnes_identidad.py`
(https://github.com/manuelleal/juaco), con un sistema de juguete escrito aquí mismo para que corra solo. El original
comparaba una memoria por votos con una variante con "cuarentena" de fuentes nuevas; el juguete hace lo mismo en
pequeño. Cambia el sistema por el tuyo y conserva las seis partes:

  (0) las copias por ancla son bit a bit iguales a su origen (sha256 contra el sello);
  (1) con las perillas APAGADAS, el candidato == la referencia en CADA consulta de CADA ronda (no sólo al final);
  (2) un control que DEBE fallar: con la perilla ENCENDIDA el candidato difiere en al menos una consulta
      (si no difiere, la perilla está desconectada: ERR-88 de JUACO);
  (3) lo que debe ser igual para todos los brazos lo es: aquí el "oráculo" depende sólo de (semilla, ronda, hecho);
  (4) comprobaciones del instrumento que no son resultado (aquí: que consultar no modifica el estado del candidato);
  (5) la optimización (caché) no cambia nada: misma salida con y sin ella.

Regla de oro: el arnés NO imprime ninguna medida de resultado (aciertos, envenenadas, recompensas). Sólo identidad.
Sale con código 0 si todo es BIT A BIT y con 1 si algo difiere: el runner lo llama y aborta si falla.
"""
import functools
import hashlib
import os
import random
import sys

RONDAS = 4


# --------------------------------------------------------------------------------------------- el sistema de juguete
def construye_entorno(semilla):
    """Entorno determinista: 6 hechos con valor verdadero, 8 fuentes (2 mentirosas), eventos repartidos en rondas."""
    rng = random.Random(semilla)
    hechos = {h: rng.randrange(3) for h in range(6)}
    mentirosas = set(rng.sample(range(8), 2))
    eventos = []
    for ronda in range(1, RONDAS + 1):
        for _ in range(10):
            fuente, h = rng.randrange(8), rng.randrange(6)
            valor = (hechos[h] + 1) % 3 if fuente in mentirosas else hechos[h]
            eventos.append(dict(ronda=ronda, fuente=fuente, hecho=h, valor=valor))
    orden = {r: sorted(set(e['hecho'] for e in eventos if e['ronda'] == r)) for r in range(1, RONDAS + 1)}
    return dict(hechos=hechos, eventos=eventos, orden=orden)


def oraculo(semilla, ronda, hecho):
    """El mismo dado para todos los brazos: depende sólo de (semilla, ronda, hecho), no del estado de nadie."""
    h = hashlib.sha256(b'%d|%d|%d' % (semilla, ronda, hecho)).digest()
    return h[0] < 64   # revela el valor verdadero con probabilidad 1/4


class MemoriaVoto:
    """REFERENCIA: responde el valor con más votos si tiene al menos `minimo`; si no, None."""

    def __init__(self, minimo=2):
        self.minimo = minimo
        self.votos = {}

    def ensena(self, fuente, hecho, valor, ronda):
        self.votos.setdefault(hecho, []).append((fuente, valor, ronda))

    def consulta(self, hecho):
        cuenta = {}
        for _, v, _ in self.votos.get(hecho, []):
            cuenta[v] = cuenta.get(v, 0) + 1
        if not cuenta:
            return None
        v, n = max(sorted(cuenta.items()), key=lambda kv: kv[1])
        return v if n >= self.minimo else None

    def fin_ronda(self, ronda):
        pass


class MemoriaCuarentena(MemoriaVoto):
    """CANDIDATO: una fuente no cuenta hasta `cuarentena` rondas después de su primera aparición.
    Perilla apagada: cuarentena = 0 (debe ser bit a bit la referencia)."""

    def __init__(self, minimo=2, cuarentena=0):
        super().__init__(minimo)
        self.cuarentena = cuarentena
        self.primera = {}
        self.ronda = 1

    def ensena(self, fuente, hecho, valor, ronda):
        self.primera.setdefault(fuente, ronda)
        super().ensena(fuente, hecho, valor, ronda)

    def consulta(self, hecho):
        if self.cuarentena == 0:
            return super().consulta(hecho)
        guardados = self.votos.get(hecho, [])
        self.votos[hecho] = [x for x in guardados if self.ronda - self.primera[x[0]] >= self.cuarentena]
        try:
            return super().consulta(hecho)
        finally:
            self.votos[hecho] = guardados

    def fin_ronda(self, ronda):
        self.ronda = ronda + 1


@functools.lru_cache(maxsize=None)
def _parecido_cache(a, b):
    return _parecido(a, b)


def _parecido(a, b):
    """Una función cara del instrumento que en producción se memoiza (parte 5)."""
    return sum((i * 31 + a) % 7 == (i * 17 + b) % 7 for i in range(200)) / 200.0


# --------------------------------------------------------------------------------------------- el arnés
def parte0_copias():
    """(0) Sellos: cada congelado de ejemplo_minimo/config.toml contra su sha256. En tu proyecto: tus copias por ancla."""
    try:
        import tomllib
    except ImportError:
        print('(0) sin tomllib (Python < 3.11): se omite')
        return False
    cfg = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ejemplo_minimo', 'config.toml')
    if not os.path.exists(cfg):
        print('(0) no hay %s: se omite' % cfg)
        return False
    with open(cfg, 'rb') as f:
        congelados = tomllib.load(f).get('congelados', {})
    mal = False
    for rel, sello in sorted(congelados.items()):
        p = os.path.join(os.path.dirname(cfg), rel)
        real = hashlib.sha256(open(p, 'rb').read()).hexdigest()[:16] if os.path.exists(p) else 'NO EXISTE'
        print('(0) %s %s %s' % ('sello OK  ' if real == sello else 'SELLO ROTO', sello, rel))
        mal |= real != sello
    return mal


def huella(semilla, parecido):
    m = construye_entorno(semilla)
    return [parecido(e['hecho'], e['fuente']) for e in m['eventos']]


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    sems = [int(x) for x in sys.argv[1].split(',')] if len(sys.argv) > 1 else [0, 1, 2, 3, 4]
    mal = parte0_copias()

    # (5) la caché no cambia nada
    h_lento, h_rapido = huella(0, _parecido), huella(0, _parecido_cache)
    print('(5) CACHÉ: %d llamadas, idénticas sin/con: %s' % (len(h_lento), h_lento == h_rapido))
    mal |= h_lento != h_rapido

    total = {'apagada_vs_referencia': [0, 0], 'encendida_difiere': [0, 0]}
    for s in sems:
        m = construye_entorno(s)
        ref, apagada, encendida = MemoriaVoto(2), MemoriaCuarentena(2, cuarentena=0), MemoriaCuarentena(2, cuarentena=1)
        ajenas = 0
        for ronda in range(1, RONDAS + 1):
            for e in [x for x in m['eventos'] if x['ronda'] == ronda]:
                for M in (ref, apagada, encendida):
                    M.ensena(e['fuente'], e['hecho'], e['valor'], ronda)
            for h in m['orden'][ronda]:
                antes = {k: list(v) for k, v in encendida.votos.items()}
                a, b, c = ref.consulta(h), apagada.consulta(h), encendida.consulta(h)
                total['apagada_vs_referencia'][0] += (a == b)          # (1) en CADA consulta de CADA ronda
                total['apagada_vs_referencia'][1] += 1
                total['encendida_difiere'][0] += (a != c)              # (2) cuenta las consultas que difieren
                total['encendida_difiere'][1] += 1
                ajenas += encendida.votos != antes                     # (4) consultar no debe modificar el estado
            for M in (ref, apagada, encendida):
                M.fin_ronda(ronda)
        dados = [oraculo(s, r, h) for r in m['orden'] for h in m['orden'][r]]
        dados2 = [oraculo(s, r, h) for r in m['orden'] for h in m['orden'][r]]
        # (3) e (4): se imprimen datos del INSTRUMENTO, nunca del resultado
        print('semilla %d: eventos %d, consultas %d, revelaciones %d (dado repetible: %s), consultas que mutan estado %d'
              % (s, len(m['eventos']), len(dados), sum(dados), dados == dados2, ajenas))
        mal |= (dados != dados2) or ajenas != 0

    a, b = total['apagada_vs_referencia']
    print('IDENTIDAD perilla apagada == referencia: %d/%d consultas idénticas' % (a, b)
          + (' (BIT A BIT)' if a == b else '  <-- DIFERENCIA'))
    mal |= a != b
    c, d = total['encendida_difiere']
    print('CONTROL QUE DEBE FALLAR perilla encendida: difiere en %d/%d consultas' % (c, d)
          + ('  (bien: la perilla está conectada)' if c > 0 else '  <-- NO DIFIERE: perilla desconectada'))
    mal |= c == 0
    print('ARNÉS:', 'BIEN' if not mal else 'MAL')
    return 1 if mal else 0


if __name__ == '__main__':
    sys.exit(main())
