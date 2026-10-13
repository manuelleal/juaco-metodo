"""Puntaje de una medición con errores sembrados: HALLAZGOS del auditor ciego contra la CLAVE sellada.

Versión general de `experimentos/medicion_protocolo/20261013/siembra/puntua.py` de JUACO
(https://github.com/manuelleal/juaco). Corrige dos cosas:
  - el sello de la clave se pasa por argumento. El original lo buscaba en una ruta fija junto al script y, en la
    réplica, comparó la clave nueva con el sello de la primera siembra e imprimió "NO COINCIDE" con una clave
    correcta (ERR-198 de JUACO). Aquí, si el sello no coincide, NO se puntúa;
  - acepta copias `cNN` (serie) y `rNN` (réplica) y no las mezcla: `r5`, `R05` y `B03_r05` son `r05`; `c05` es otra
    copia. El original convertía todo a `cNN`.

Uso:
  python herramientas/puntua.py CLAVE.csv HALLAZGOS.csv --sello CLAVE.sha256 [opciones]
  python herramientas/puntua.py CLAVE.csv HALLAZGOS.csv --sha256 HEX [opciones]
  python herramientas/puntua.py CLAVE.csv HALLAZGOS.csv --sin-sello [opciones]   (sólo pruebas; lo dice en la salida)

  --tabla salida.csv          escribe la tabla copia a copia
  --umbral 'medida<0.50'      evalúa un umbral de tu preregistro (repetible). Medidas: total, criterio, instrumento,
                              lectura, falsas_alarmas; operadores < <= > >=; sobre la proporción k/n. Dice además si
                              cambia de lado moviendo UNA copia (regla 10). Sin --umbral no se evalúa ninguno: este
                              script no trae umbrales por defecto.
  --exige-dato                cuenta como confianza baja toda fila alta o media con `dato_que_confirma` vacío. Úsalo
                              sólo si tu preregistro lo dice; sin la opción, esas filas se cuentan y se avisan.

CLAVE.csv     : copia,tiene_defecto,tipo,archivo,linea,descripcion          (una fila por copia; limpias, tipo vacío)
HALLAZGOS.csv : copia,defecto,tipo,archivo,linea,descripcion,dato_que_confirma,confianza,argumento_contrario
                (cero o más filas por copia; agentes/metodo-auditor-ciego.md)

Reglas (las del preregistro de JUACO; si tu preregistro dice otras, cambia el script ANTES de abrir la clave):
  - ACIERTO: copia con defecto con al menos una fila defecto=si cuyo `archivo` coincide, por nombre base, con el de
    la clave. No se exige línea ni tipo (ERR-197 de JUACO: un defecto sembrado en el preregistro y señalado en el
    runner cuenta como fallo; se deja así porque así se preregistró).
  - FALSA ALARMA: copia limpia con alguna fila defecto=si de confianza alta o media.
  - Sensibilidad total y por tipo (criterio, instrumento, lectura/otro) y falsas alarmas, con Wilson al 95 %.
Sale 0 si puntuó; 1 si el sello no coincide o falta; 2 por argumentos o archivos mal formados.
"""
import csv
import hashlib
import math
import os
import re
import sys
import unicodedata

Z95 = 1.959963984540054
TIPOS = ('criterio', 'instrumento', 'lectura')
MEDIDAS = ('total',) + TIPOS + ('falsas_alarmas',)
OPS = {'<': lambda a, b: a < b, '<=': lambda a, b: a <= b, '>': lambda a, b: a > b, '>=': lambda a, b: a >= b}


def sin_tildes(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s or '') if unicodedata.category(c) != 'Mn').strip().lower()


def norm_copia(s):
    """'c5', 'C05', 'B03_c05' -> 'c05'; 'r5', 'B03_r05' -> 'r05'. Otra cosa: en minúsculas, tal cual."""
    t = (s or '').strip().lower()
    m = re.search(r'(?:^|[^a-z0-9])([cr])0*(\d+)$', t)
    return '%s%02d' % (m.group(1), int(m.group(2))) if m else t


def norm_si(s):
    return sin_tildes(s) in ('si', 's', 'yes', 'y', 'true', '1')


def norm_tipo(s):
    t = sin_tildes(s)
    if t.startswith('crit'):
        return 'criterio'
    if t.startswith('instr'):
        return 'instrumento'
    if t.startswith('lect') or t.startswith('otro'):
        return 'lectura'
    return t


def base(ruta):
    return os.path.basename((ruta or '').strip().replace('\\', '/')).lower()


def wilson(k, n, z=Z95):
    if n == 0:
        return (None, None, None)
    p = k / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    medio = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (p, max(0.0, centro - medio), min(1.0, centro + medio))


def fmt(t):
    p, lo, hi = t
    return 'sin datos' if p is None else '%.3f [%.3f, %.3f]' % (p, lo, hi)


def lee(ruta, columnas):
    with open(ruta, encoding='utf-8-sig', newline='') as f:
        r = csv.DictReader(f)
        faltan = [c for c in columnas if c not in (r.fieldnames or [])]
        if faltan:
            raise ValueError('%s: faltan columnas %s' % (ruta, faltan))
        return list(r)


def opcion(args, nombre, con_valor=True):
    """Saca una opción de args; devuelve su valor (o True), o None si no está. Repetible: lista."""
    vals = []
    while nombre in args:
        i = args.index(nombre)
        if con_valor:
            if i + 1 >= len(args):
                raise ValueError('%s necesita un valor' % nombre)
            vals.append(args[i + 1])
            del args[i:i + 2]
        else:
            vals.append(True)
            del args[i]
    return vals


def main(argv):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    args = list(argv[1:])
    try:
        salida = opcion(args, '--tabla')
        sello = opcion(args, '--sello')
        sha = opcion(args, '--sha256')
        sin_sello = opcion(args, '--sin-sello', False)
        exige = bool(opcion(args, '--exige-dato', False))
        umbrales = []
        for u in opcion(args, '--umbral'):
            m = re.match(r'^\s*(\w+)\s*(<=|>=|<|>)\s*([0-9]*\.?[0-9]+)\s*$', u)
            if not m or m.group(1) not in MEDIDAS:
                raise ValueError('umbral mal escrito: %r (p. ej. "falsas_alarmas>0.25"; medidas: %s)'
                                 % (u, ', '.join(MEDIDAS)))
            umbrales.append((m.group(1), m.group(2), float(m.group(3))))
    except ValueError as e:
        print('ERROR: %s' % e)
        return 2
    if len(args) != 2 or any(a.startswith('-') for a in args) or len(sello) + len(sha) + len(sin_sello) != 1:
        print(__doc__)
        print('ERROR: hacen falta CLAVE.csv, HALLAZGOS.csv y exactamente una de --sello, --sha256, --sin-sello.')
        return 2
    r_clave, r_hall = args

    # ------------------------------------------------------------------ sello de la clave, ANTES de leerla
    with open(r_clave, 'rb') as f:
        real = hashlib.sha256(f.read()).hexdigest()
    if sin_sello:
        print('sha256(%s) = %s  ->  SIN SELLO (--sin-sello): este puntaje no vale como medición' % (
            os.path.basename(r_clave), real))
    else:
        if sello:
            with open(sello[0], encoding='utf-8') as f:
                partes = f.read().split()
            esperado = partes[0].strip().lower() if partes else ''
            origen = '%s%s' % (sello[0], ' (dice: %s)' % partes[1] if len(partes) > 1 else '')
        else:
            esperado, origen = sha[0].strip().lower(), '--sha256'
        if not re.fullmatch(r'[0-9a-f]{64}', esperado):
            print('ABORTO: el sello de %s no es un sha256 de 64 hex: %r' % (origen, esperado))
            return 1
        if real != esperado:
            print('ABORTO: sha256(%s) = %s NO COINCIDE con el sello %s de %s. No se puntúa: o la clave cambió '
                  'después de sellarla o el sello es de otra siembra.' % (r_clave, real, esperado, origen))
            return 1
        print('sha256(%s) = %s  ->  COINCIDE con %s' % (os.path.basename(r_clave), real, origen))

    try:
        filas_clave = lee(r_clave, ['copia', 'tiene_defecto', 'tipo', 'archivo'])
        filas_hall = lee(r_hall, ['copia', 'defecto', 'archivo', 'confianza'])
    except (ValueError, OSError) as e:
        print('ERROR: %s' % e)
        return 2

    clave = {}
    for r in filas_clave:
        c = norm_copia(r['copia'])
        if c in clave:
            print('ERROR: la copia %s está dos veces en la clave' % c)
            return 2
        clave[c] = dict(defecto=norm_si(r['tiene_defecto']), tipo=norm_tipo(r.get('tipo')), archivo=base(r.get('archivo')),
                        linea=(r.get('linea') or '').strip())
    hall, ajenas, sin_dato = {}, set(), []
    tiene_col_dato = 'dato_que_confirma' in (filas_hall[0] if filas_hall else {})
    for r in filas_hall:
        c = norm_copia(r.get('copia'))
        if c not in clave:
            ajenas.add(r.get('copia'))
            continue
        conf = sin_tildes(r.get('confianza'))
        si = norm_si(r.get('defecto'))
        if si and conf in ('alta', 'media') and not (r.get('dato_que_confirma') or '').strip():
            sin_dato.append(c)
            if exige:
                conf = 'baja'
        hall.setdefault(c, []).append(dict(defecto=si, archivo=base(r.get('archivo')),
                                           linea=(r.get('linea') or '').strip(), confianza=conf))
    if ajenas:
        print('AVISO: filas de HALLAZGOS con copias que no están en la clave (ignoradas): %s' % sorted(ajenas))
    sin_fila = sorted(c for c in clave if c not in hall)
    if sin_fila:
        print('AVISO: copias sin ninguna fila en HALLAZGOS (%d): %s' % (len(sin_fila), ' '.join(sin_fila)))
    if not tiene_col_dato and filas_hall:
        print('AVISO: HALLAZGOS no trae la columna dato_que_confirma')
    if sin_dato:
        print('AVISO: %d fila(s) de confianza alta o media sin dato_que_confirma (copias %s)%s' % (
            len(sin_dato), ' '.join(sorted(set(sin_dato))),
            ': contadas como baja (--exige-dato)' if exige else ': contadas como están (sin --exige-dato)'))

    tabla = []
    for c in sorted(clave):
        k, filas = clave[c], hall.get(c, [])
        pos = [f for f in filas if f['defecto']]
        linea_ok = None
        if k['defecto']:
            acierta = any(f['archivo'] and f['archivo'] == k['archivo'] for f in pos)
            linea_ok = any(f['archivo'] == k['archivo'] and f['linea'] and f['linea'] == k['linea'] for f in pos)
            res = 'ACIERTO' if acierta else 'FALLO'
        else:
            fa = any(f['confianza'] in ('alta', 'media') for f in pos)
            res = 'FALSA ALARMA' if fa else ('limpia, sin alarma' if not pos else 'limpia, alarma de confianza baja')
        tabla.append(dict(copia=c, tiene_defecto='si' if k['defecto'] else 'no', tipo=k['tipo'],
                          archivo_clave=k['archivo'], linea_clave=k['linea'], filas_auditor=len(filas),
                          filas_defecto_si=len(pos),
                          archivos_auditor=';'.join(sorted({f['archivo'] for f in pos if f['archivo']})),
                          resultado=res, misma_linea='' if linea_ok is None else ('si' if linea_ok else 'no')))

    con = [t for t in tabla if t['tiene_defecto'] == 'si']
    limpias = [t for t in tabla if t['tiene_defecto'] == 'no']
    cuenta = {'total': (sum(t['resultado'] == 'ACIERTO' for t in con), len(con)),
              'falsas_alarmas': (sum(t['resultado'] == 'FALSA ALARMA' for t in limpias), len(limpias))}
    for t in TIPOS:
        g = [x for x in con if x['tipo'] == t]
        cuenta[t] = (sum(x['resultado'] == 'ACIERTO' for x in g), len(g))

    print('\nCopias: %d  (con defecto %d, limpias %d)\n' % (len(tabla), len(con), len(limpias)))
    print('| medida | k / n | proporción [Wilson 95 %] |')
    print('|---|---|---|')
    nombres = {'total': 'sensibilidad total', 'criterio': 'sensibilidad criterio',
               'instrumento': 'sensibilidad instrumento', 'lectura': 'sensibilidad lectura/otro',
               'falsas_alarmas': 'falsas alarmas (limpias con defecto=si de confianza alta o media)'}
    for m in MEDIDAS:
        k_, n_ = cuenta[m]
        print('| %s | %d/%d | %s |' % (nombres[m], k_, n_, fmt(wilson(k_, n_))))
    otros = sorted({x['tipo'] for x in con} - set(TIPOS))
    if otros:
        print('AVISO: tipos en la clave fuera de %s: %s' % (TIPOS, otros))
    print('| (descriptivo) aciertos que además dan la misma línea | %d/%d | |'
          % (sum(t['misma_linea'] == 'si' for t in con), len(con)))

    print('\nTabla copia a copia\n')
    print('| copia | defecto | tipo | archivo (clave) | línea | filas | defecto=si | archivos del auditor | resultado |')
    print('|---|---|---|---|---|---|---|---|---|')
    for t in tabla:
        print('| %s | %s | %s | %s | %s | %d | %d | %s | %s |' % (
            t['copia'], t['tiene_defecto'], t['tipo'], t['archivo_clave'], t['linea_clave'], t['filas_auditor'],
            t['filas_defecto_si'], t['archivos_auditor'], t['resultado']))

    if umbrales:
        print('\nUmbrales pedidos (--umbral), evaluados sin interpretar:')
        for m, op, v in umbrales:
            k_, n_ = cuenta[m]
            if not n_:
                print('- %s %s %g: sin datos (n = 0)' % (m, op, v))
                continue
            lado = OPS[op](k_ / n_, v)
            fragil = any(0 <= k2 <= n_ and OPS[op](k2 / n_, v) != lado for k2 in (k_ - 1, k_ + 1))
            print('- %s %s %g: %s (%d/%d = %.3f)%s' % (m, op, v, 'SI' if lado else 'no', k_, n_, k_ / n_,
                                                       '  <- cambia de lado moviendo UNA copia' if fragil else ''))

    if salida:
        with open(salida[0], 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(tabla[0].keys()))
            w.writeheader()
            w.writerows(tabla)
        print('\ntabla -> %s' % salida[0])
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
