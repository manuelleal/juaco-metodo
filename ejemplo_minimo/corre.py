"""Ejemplo mínimo del protocolo, de punta a punta, en Python puro y en segundos.

  python ejemplo_minimo/corre.py           todo: sellos, anclas, identidad, campo a campo, humo, serie, réplica, veredicto
  python ejemplo_minimo/corre.py --humo    sólo hasta el humo (pasos 1 a 5)

Pasos (cada uno aborta si falla, salvo el 4, que trae un defecto SEMBRADO a propósito y muestra cómo se atrapa):
  1. Sellos: la referencia y el preregistro son los congelados (herramientas/guardia.py --check). Cotejo: cada valor
     de la tabla "## Parámetros sellados" del PREREGISTRO es el que usa este runner (PREREGISTRADO, abajo), con
     herramientas/coteja_preregistro.py; si algo difiere, no se corre nada (en --humo sólo avisa).
  2. Anclas: candidato.py es exactamente lo que construye construye_candidato.py (nadie lo editó a mano).
  3. Identidad: arnes_identidad.py, con la perilla apagada el candidato es bit a bit la referencia.
  4. Entrada campo a campo de la batería copiada contra la de la referencia. Aquí salta ERR-001 (argumento omitido);
     se mide qué habría dicho el veredicto con el defecto (semillas 901-920, fuera de la serie) y se corrige.
  5. Humo: semilla 99, todos los brazos; ESCRIBE datos/humo.json y lo relee.
  6. Serie 101-120 -> datos/serie_101-120.json.
  7. Réplica 121-140 -> datos/replica_121-140.json.
  8. Veredicto por la letra del PREREGISTRO, releyendo los JSON; escribe VEREDICTO.md, la clasificación de ERR-001 y
     registro/errores.csv con herramientas/construye_errores.py.
Todo es determinista: correrlo dos veces escribe los mismos bytes.
"""
import hashlib
import inspect
import json
import os
import statistics
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
sys.path.insert(1, os.path.join(RAIZ, 'herramientas'))

import arnes_identidad  # noqa: E402
import bateria_copiada  # noqa: E402
import bateria_referencia  # noqa: E402
import candidato  # noqa: E402
import construye_candidato  # noqa: E402
import coteja_preregistro  # noqa: E402
import referencia  # noqa: E402

SERIE, REPLICA, HUMO, CONTRAFACTUAL = range(101, 121), range(121, 141), [99], range(901, 921)
FECHA_ERR = '2026-10-13'
LINEA_ERR = 9   # línea de VEREDICTO.md donde se define ERR-001; debe coincidir con [fuentes] de config.toml
UMBRAL_PAREADO, MARGEN_P1, COTA_P3, HUECO = 15, 0.02, -0.01, (0.30, 0.78)
DESPLAZA_PLACEBO = 10000   # PLACEBO = la referencia con la semilla + 10000 (otro ruido)

# Lo que este runner usa de verdad, con los nombres de "## Parámetros sellados" del PREREGISTRO. Son las variables
# vivas, no números copiados: si alguien cambia un umbral aquí o una perilla en la batería, el cotejo del paso 1 lo ve.
PREREGISTRADO = dict(
    SERIE=SERIE, REPLICA=REPLICA, HUMO=HUMO, CONTRAFACTUAL=CONTRAFACTUAL,
    UMBRAL_PAREADO=UMBRAL_PAREADO, MARGEN_P1=MARGEN_P1, COTA_P3=COTA_P3, HUECO=HUECO,
    DESPLAZA_PLACEBO=DESPLAZA_PLACEBO,
    k=bateria_copiada.PERILLAS['k'], beta=bateria_copiada.PERILLAS['beta'],
    pasos=bateria_referencia.KWARGS_REFERENCIA['pasos'], eps=bateria_referencia.KWARGS_REFERENCIA['eps'],
    alpha=bateria_referencia.KWARGS_REFERENCIA['alpha'], medias=bateria_referencia.KWARGS_REFERENCIA['medias'],
    sigma=bateria_referencia.KWARGS_REFERENCIA['sigma'],
)


def sha16(ruta):
    with open(ruta, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def paso(n, texto):
    print('\n[%d/8] %s' % (n, texto))


def aborta(motivo):
    print('ABORTO: ' + motivo)
    sys.exit(1)


# ------------------------------------------------------------------------------------------------ medidas
def resume(d):
    rec = d['recompensas']
    n = len(rec)
    q = n // 4
    return dict(Q3=sum(rec[2 * q:3 * q]) / q, total=sum(rec) / n, eps_medio=sum(d['eps_aplicado']) / n,
                huella=hashlib.sha256(repr(rec).encode()).hexdigest()[:16])


def corre_semilla(s, kw_cand):
    """Los cuatro brazos del preregistro en una semilla."""
    ref = resume(bateria_referencia.corre(s))
    cand = resume(candidato.corre(s, **kw_cand))
    const = resume(bateria_referencia.corre(s, eps=cand['eps_medio']))   # control de cantidad
    placebo = resume(bateria_referencia.corre(s + DESPLAZA_PLACEBO))     # mismo sistema, otro ruido
    return dict(REF=ref, CAND=cand, CONST=const, PLACEBO=placebo)


def corre_serie(semillas, kw_cand, ruta):
    datos = dict(semillas=list(semillas), kwargs_candidato={k: list(v) if isinstance(v, tuple) else v
                                                              for k, v in kw_cand.items()},
                 por_semilla={str(s): corre_semilla(s, kw_cand) for s in semillas})
    with open(ruta, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(datos, f, indent=1, sort_keys=True)
        f.write('\n')
    return ruta


def puertas(datos):
    """Evalúa la letra del preregistro sobre un JSON ya escrito (no sobre lo que hay en memoria)."""
    filas = list(datos['por_semilla'].values())
    d = lambda a, b, m: [f[a][m] - f[b][m] for f in filas]
    p1_d, p0_d = d('CAND', 'REF', 'Q3'), d('PLACEBO', 'REF', 'Q3')
    p2_d, p3_d = d('CAND', 'CONST', 'Q3'), d('CAND', 'REF', 'total')
    n = len(filas)
    r = {}
    r['G'] = dict(valor=statistics.median(f['REF']['Q3'] for f in filas))
    r['G']['pasa'] = HUECO[0] <= r['G']['valor'] <= HUECO[1]
    for nombre, dif in (('P1', p1_d), ('P0', p0_d)):
        med, par = statistics.median(dif), sum(x > 0 for x in dif)
        r[nombre] = dict(mediana=med, pareado=par, n=n, pasa_p1=med >= MARGEN_P1 and par >= UMBRAL_PAREADO)
    r['P1']['pasa'] = r['P1']['pasa_p1']
    r['P0']['pasa'] = not r['P0']['pasa_p1']      # el placebo debe CAER el criterio de P1
    med2, par2 = statistics.median(p2_d), sum(x > 0 for x in p2_d)
    r['P2'] = dict(mediana=med2, pareado=par2, n=n, pasa=med2 > 0 and par2 >= UMBRAL_PAREADO)
    r['P3'] = dict(mediana=statistics.median(p3_d), n=n)
    r['P3']['pasa'] = r['P3']['mediana'] >= COTA_P3
    r['alarma_filas_identicas'] = all(f['CAND']['huella'] == f['REF']['huella'] for f in filas)
    r['en_el_umbral'] = [k for k in ('P1', 'P2', 'P0') if abs(r[k]['pareado'] - UMBRAL_PAREADO) <= 1]
    return r


def veredicto(rs, rr):
    if rs['alarma_filas_identicas'] or rr['alarma_filas_identicas']:
        return 'INCOMPLETO (CAND y REF idénticos: una vía está apagada)'
    if not (rs['G']['pasa'] and rr['G']['pasa']):
        return 'INCOMPLETO (falta hueco: el entorno no deja medir)'
    if not (rs['P0']['pasa'] and rr['P0']['pasa']):
        return 'INCOMPLETO (falta un criterio que distinga: el placebo pasa P1)'
    for k in ('P1', 'P2', 'P3'):
        if rs[k]['pasa'] != rr[k]['pasa']:
            return 'INCOMPLETO (falta réplica: serie y réplica no coinciden en %s)' % k
    if not rs['P1']['pasa']:
        return 'NO FUNCIONA'
    if not rs['P2']['pasa'] or not rs['P3']['pasa']:
        return 'HAY ALGO PERO MODESTO'
    return 'FUNCIONA'


# ------------------------------------------------------------------------------------------------ paso 4
def efectivos(fun, kwargs):
    """Argumentos con los que la función correrá de verdad: los de la batería y, si faltan, los defectos del módulo."""
    out = {}
    for nombre, p in inspect.signature(fun).parameters.items():
        if nombre == 'semilla':
            continue
        out[nombre] = (kwargs[nombre], 'batería') if nombre in kwargs else (p.default, 'defecto del módulo')
    return out


def campo_a_campo(kw_cand, perillas):
    ef_r = efectivos(referencia.corre, bateria_referencia.KWARGS_REFERENCIA)
    ef_c = efectivos(candidato.corre, kw_cand)
    difs = []
    for nombre, (v_r, o_r) in ef_r.items():
        v_c, o_c = ef_c.get(nombre, ('FALTA', ''))
        if v_r != v_c:
            difs.append('%s: referencia %r (%s) · candidato %r (%s)' % (nombre, v_r, o_r, v_c, o_c))
    nuevas = sorted(set(ef_c) - set(ef_r))
    no_declaradas = [n for n in nuevas if n not in perillas]
    if no_declaradas:
        difs.append('argumentos nuevos que no son perillas declaradas: %s' % no_declaradas)
    return difs, nuevas


# ------------------------------------------------------------------------------------------------ principal
def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    humo_solo = '--humo' in sys.argv
    t0 = time.time()
    os.makedirs(os.path.join(AQUI, 'datos'), exist_ok=True)

    paso(1, 'Sellos de la referencia congelada y del preregistro')
    r = subprocess.run([sys.executable, os.path.join(RAIZ, 'herramientas', 'guardia.py'), '--check', '--config',
                        os.path.join(AQUI, 'config.toml')], capture_output=True, text=True, encoding='utf-8')
    print(r.stdout.rstrip())
    if r.returncode != 0:
        aborta('un congelado cambió. Regla 1: no se edita; si es a propósito, lo vuelve a sellar una persona.')
    try:
        log = subprocess.run(['git', '-C', AQUI, 'log', '-1', '--format=%h %ad', '--date=short', '--',
                              'PREREGISTRO.md'], capture_output=True, text=True)
        en_git = log.returncode == 0
        commit_prereg = log.stdout.strip()
    except OSError:
        en_git, commit_prereg = False, ''
    if not en_git:
        commit_prereg = 'no verificable (fuera de git)'
        print('AVISO: la carpeta no está en git; no puedo comprobar que el preregistro se commiteó antes (regla 4).')
    elif not commit_prereg:
        if not humo_solo:
            aborta('PREREGISTRO.md no está commiteado. Regla 4: se commitea antes de la corrida larga '
                   '(el humo sí puede correr: --humo).')
        commit_prereg = 'SIN COMMIT'
    print('PREREGISTRO.md commiteado en: %s' % commit_prereg)
    filas, difs = coteja_preregistro.coteja(os.path.join(AQUI, 'PREREGISTRO.md'), PREREGISTRADO)
    coteja_preregistro.imprime(filas)
    if difs:
        texto = '%d diferencia(s) entre PREREGISTRO.md y este runner:\n  - %s' % (len(difs), '\n  - '.join(difs))
        if not humo_solo:
            aborta(texto + '\nRegla 4: lo que corre es lo preregistrado. Si el cambio es a propósito, va en una '
                   'enmienda con su ERR (regla 9) y se vuelve a sellar.')
        print('AVISO (--humo sigue): ' + texto)
    else:
        print('Cotejo preregistro <-> runner: %d/%d iguales' % (len(filas), len(filas)))

    paso(2, 'Construcción por anclas: candidato.py es el generado, byte a byte')
    generado = construye_candidato.construye()
    if hashlib.sha256(generado).hexdigest()[:16] != sha16(os.path.join(AQUI, 'candidato.py')):
        aborta('candidato.py no es lo que construye construye_candidato.py: alguien lo editó a mano.')
    print('candidato.py %s == construido desde referencia.py %s' % (sha16(os.path.join(AQUI, 'candidato.py')),
                                                                     construye_candidato.SHA_ORIGEN))

    paso(3, 'Arnés de identidad (antes de mirar ningún número)')
    if arnes_identidad.main() != 0:
        aborta('el arnés de identidad falló: no hay experimento.')

    paso(4, 'Entrada campo a campo: batería copiada contra batería de la referencia')
    perillas = bateria_copiada.PERILLAS
    difs, nuevas = campo_a_campo(bateria_copiada.KWARGS_CANDIDATO, perillas)
    err = None
    if difs:
        print('DIFERENCIAS (defecto sembrado a propósito, ver LEEME.md):')
        for x in difs:
            print('  - ' + x)
        malo = [corre_semilla(s, bateria_copiada.KWARGS_CANDIDATO) for s in CONTRAFACTUAL]
        dif_malo = [f['CAND']['Q3'] - f['REF']['Q3'] for f in malo]
        cf = dict(mediana=statistics.median(dif_malo), pareado=sum(x > 0 for x in dif_malo), n=len(dif_malo))
        cf['P1'] = 'pasa' if cf['mediana'] >= MARGEN_P1 and cf['pareado'] >= UMBRAL_PAREADO else 'CAE'
        print('Contrafactual con el defecto (semillas 901-920, no cuentan): P1 mediana %+.4f, pareado %d/%d -> %s'
              % (cf['mediana'], cf['pareado'], cf['n'], cf['P1']))
        err = dict(difs=difs, contrafactual=cf)
        kw_cand = dict(bateria_referencia.KWARGS_REFERENCIA, **perillas)   # corrección: regla 12
        print('Corrección: argumentos del candidato = KWARGS_REFERENCIA + PERILLAS %s' % perillas)
        difs2, _ = campo_a_campo(kw_cand, perillas)
        if difs2:
            aborta('la corrección no deja la entrada igual: %s' % difs2)
        print('Tras la corrección: 0 diferencias; perillas nuevas: %s' % nuevas)
    else:
        kw_cand = dict(bateria_copiada.KWARGS_CANDIDATO)
        print('0 diferencias; perillas nuevas: %s' % nuevas)

    paso(5, 'Humo: semilla 99, todos los brazos, escribe y relee datos/humo.json')
    ruta_humo = corre_serie(HUMO, kw_cand, os.path.join(AQUI, 'datos', 'humo.json'))
    with open(ruta_humo, encoding='utf-8') as f:
        h = json.load(f)
    fila = h['por_semilla']['99']
    faltan = [b for b in ('REF', 'CAND', 'CONST', 'PLACEBO') if b not in fila or set(fila[b]) != {
        'Q3', 'total', 'eps_medio', 'huella'}]
    if faltan:
        aborta('el humo no escribió todos los brazos: %s' % faltan)
    print('datos/humo.json escrito y releído (sha16 %s); brazos completos' % sha16(ruta_humo))
    if humo_solo:
        print('\n--humo: me detengo aquí. %.1f s' % (time.time() - t0))
        return 0

    paso(6, 'Serie 101-120')
    ruta_s = corre_serie(SERIE, kw_cand, os.path.join(AQUI, 'datos', 'serie_101-120.json'))
    print('datos/serie_101-120.json (sha16 %s)' % sha16(ruta_s))
    paso(7, 'Réplica 121-140 (semillas nuevas, misma letra)')
    ruta_r = corre_serie(REPLICA, kw_cand, os.path.join(AQUI, 'datos', 'replica_121-140.json'))
    print('datos/replica_121-140.json (sha16 %s)' % sha16(ruta_r))

    paso(8, 'Veredicto por la letra del preregistro, releyendo los JSON')
    with open(ruta_s, encoding='utf-8') as f:
        rs = puertas(json.load(f))
    with open(ruta_r, encoding='utf-8') as f:
        rr = puertas(json.load(f))
    v = veredicto(rs, rr)
    escribe_veredicto(v, rs, rr, err, commit_prereg, ruta_s, ruta_r)
    if err:
        escribe_clasificacion(err)
    r = subprocess.run([sys.executable, os.path.join(RAIZ, 'herramientas', 'construye_errores.py'), '--config',
                        os.path.join(AQUI, 'config.toml')], capture_output=True, text=True, encoding='utf-8')
    print(r.stdout.rstrip())
    if r.returncode != 0:
        aborta('construye_errores.py falló: %s' % r.stderr.strip())
    with open(os.path.join(AQUI, 'VEREDICTO.md'), encoding='utf-8') as f:
        texto = f.read()
    print('\n' + '=' * 100 + '\n' + texto + '=' * 100)
    print('Tiempo total: %.1f s' % (time.time() - t0))
    return 0


def fmt(r, k):
    x = r[k]
    if k == 'G':
        return 'mediana Q3 REF %.4f' % x['valor']
    if k == 'P3':
        return 'mediana %+.4f' % x['mediana']
    return 'mediana %+.4f, %d/%d' % (x['mediana'], x['pareado'], x['n'])


def escribe_veredicto(v, rs, rr, err, commit_prereg, ruta_s, ruta_r):
    rel = lambda p: os.path.relpath(p, AQUI).replace(os.sep, '/')
    L = ['# VEREDICTO: ejemplo mínimo · exploración por sorpresa en un bandido no estacionario', '',
         '**%s**' % v, '',
         '**Preregistro:** `PREREGISTRO.md` (sha16 %s), commit %s.' % (sha16(os.path.join(AQUI, 'PREREGISTRO.md')),
                                                                      commit_prereg),
         '**Resultados:** `%s` (sha16 %s), `%s` (sha16 %s).' % (rel(ruta_s), sha16(ruta_s), rel(ruta_r), sha16(ruta_r)),
         '', '## Errores registrados en este bloque']
    if err:
        cf = err['contrafactual']
        L.append('**ERR-001 (%s):** la batería copiada para el candidato (`bateria_copiada.py`) omitió un argumento que '
                 'la referencia pasa explícitamente — %s — y el candidato habría corrido con el valor por defecto de su '
                 'módulo · causa: instrumento (argumento perdido en la copia; defecto sembrado a propósito para el '
                 'ejemplo) · lo atrapó: la comparación campo a campo del paso 4, antes de la corrida · veredictos que '
                 'toca: ninguno; contrafactual en semillas 901–920 (fuera de la serie): con el defecto, P1 habría dado '
                 'mediana %+.4f y %d/%d pareado, es decir P1 %s · corrección: argumentos del candidato = '
                 '`KWARGS_REFERENCIA` + `PERILLAS` · regla: 12 de `PROTOCOLO.md`.'
                 % (FECHA_ERR, '; '.join(err['difs']), cf['mediana'], cf['pareado'], cf['n'], cf['P1']))
    else:
        L.append('Ninguno.')
    if len(L) < LINEA_ERR or (err and not L[LINEA_ERR - 1].startswith('**ERR-001')):
        aborta('ERR-001 no quedó en la línea %d de VEREDICTO.md (config.toml lo espera ahí)' % LINEA_ERR)
    L += ['', '## Tabla', '',
          '| puerta | predicción (PREREGISTRO §7-§9) | serie 101–120 | réplica 121–140 | pasa |',
          '|---|---|---|---|---|']
    pred = {'G': 'mediana Q3 REF en [0.30, 0.78]', 'P0': 'el placebo CAE el criterio de P1',
            'P1': 'CAND − REF ≥ +0.02 y ≥ 15/20', 'P2': 'CAND − CONST > 0 y ≥ 15/20',
            'P3': 'total CAND − REF ≥ −0.01'}
    for k in ('G', 'P0', 'P1', 'P2', 'P3'):
        ambos = rs[k]['pasa'] and rr[k]['pasa']
        L.append('| %s | %s | %s | %s | %s |' % (k, pred[k], fmt(rs, k), fmt(rr, k),
                                                 'sí' if ambos else ('no' if not (rs[k]['pasa'] or rr[k]['pasa'])
                                                                     else 'no replica')))
    umbral = sorted(set(rs['en_el_umbral']) | set(rr['en_el_umbral']))
    L += ['', '## Lectura honesta', '']
    lect = []
    if rs['P1']['pasa'] and rr['P1']['pasa']:
        lect.append('Por la letra, subir epsilon con la sorpresa mejora la recompensa del cuarto que sigue a la '
                    'inversión en las dos series.')
    else:
        lect.append('Por la letra, P1 no se sostiene en las dos series: el candidato no mejora lo que se predijo.')
    if rs['P2']['pasa'] and rr['P2']['pasa']:
        lect.append('Le gana al control con la misma exploración total: el momento importa, en este entorno.')
    elif rs['P2']['pasa'] or rr['P2']['pasa']:
        lect.append('Contra el control con la misma exploración total (CONST) pasa en una serie y cae en la otra: '
                    'que el momento añada algo sobre la cantidad no está demostrado, y tampoco descartado.')
    else:
        lect.append('No le gana al control con la misma exploración total (CONST): lo que ayuda es explorar más, y '
                    'la sorpresa no añade nada medible sobre esa cantidad.')
    lect.append('Conteos a ±1 del umbral: %s.' % (', '.join(umbral) if umbral else 'ninguno')
                + (' Por la regla 10, eso pide otra réplica antes de afirmar nada fuera de este ejemplo.'
                   if umbral else ''))
    lect.append('Es un juguete con el entorno elegido a favor de la pregunta (PREREGISTRO §5): no dice nada de otros '
                'entornos.')
    L.append(' '.join(lect))
    L += ['', '## Qué sigue', '']
    if v.startswith('INCOMPLETO (falta réplica'):
        L.append('Lo que manda el preregistro (§9): una tercera serie con la misma letra en semillas nuevas (p. ej. '
                 '141–160), declarada antes en una enmienda; el preregistro está sellado, así que la enmienda la '
                 'vuelve a sellar una persona. Este ejemplo se detiene aquí a propósito: no se cambia la letra para '
                 'que el veredicto salga redondo.')
        L.append('')
    L += ['En tu proyecto: copia la estructura (sellos → anclas → identidad → campo a campo → humo → serie → réplica '
          '→ veredicto desde el JSON) y sustituye el sistema de juguete por el tuyo. Ver `LEEME.md`.', '']
    with open(os.path.join(AQUI, 'VEREDICTO.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L))


def escribe_clasificacion(err):
    os.makedirs(os.path.join(AQUI, 'registro'), exist_ok=True)
    c = {'_nota': 'Clasificación a mano de los ERR del ejemplo; la escribe corre.py. Esquema: '
                  'registro/ESQUEMA_errores.md en la raíz del repositorio.',
         '1': dict(id_permanente='ERR-001', tipo='instrumento', quien_lo_cometio='sembrador',
                   quien_lo_atrapo='comparador', tiempo_hasta_detectarlo='antes_de_la_corrida', altero_conclusion='no',
                   hallazgo_sin_accion='no',
                   resumen='La batería copiada omitió alpha; el candidato habría corrido con el valor por defecto '
                           'del módulo.',
                   justificacion_tipo='Argumento perdido al copiar la batería: falla el instrumento, no el sistema.')}
    with open(os.path.join(AQUI, 'registro', 'clasificacion_errores.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(c, f, ensure_ascii=False, indent=1)
        f.write('\n')


if __name__ == '__main__':
    sys.exit(main())
