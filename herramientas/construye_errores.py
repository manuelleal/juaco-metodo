"""Construye registro/errores.csv a partir de las definiciones de los ERR del proyecto y de una clasificación a mano.

Versión general de `informe/construye_errores.py` de JUACO (https://github.com/manuelleal/juaco). La tabla de fuentes,
las rutas y los parámetros salen de config.toml. No corre experimentos: sólo lee archivos y git.

Qué hace, en orden:
  1. ESCANEO. Recorre los .md del proyecto (salvo `[registro].excluir_escaneo`) y anota cada aparición de "ERR-N".
     Da el inventario de números usados y los huecos.
  2. DEFINICIÓN. Para cada número de `[fuentes]`, verifica que la línea indicada contiene `ERR-N` (o el `token`) y
     aborta si no. Extrae el párrafo de la definición de forma determinista.
  3. FECHA. La del primer paréntesis junto al token, si trae una; si no, la del primer commit que introduce la línea;
     si no hay git, `no_determinable`.
  4. UNIÓN. Junta lo extraído con la clasificación (JSON hecho a mano), valida el vocabulario de
     registro/ESQUEMA_errores.md y escribe:
       <carpeta>/errores.csv
       <generado>/definiciones_errores.json, <generado>/resumen_errores.md, <generado>/muestra.csv

Sobre un proyecto sin ningún ERR escribe un errores.csv con sólo el encabezado y un resumen con ceros. Es lo esperado.
Las salidas son deterministas (sin fecha de generación): correrlo dos veces no ensucia git.

Uso:  python herramientas/construye_errores.py [--config ruta/a/config.toml]
      (sin --config usa el config.toml de la carpeta padre de herramientas/)
"""
import argparse
import collections
import csv
import json
import os
import random
import re
import subprocess
import sys

try:
    import tomllib
except ImportError:  # Python < 3.11
    sys.exit('ABORTO: hace falta Python >= 3.11 (módulo tomllib).')

COLUMNAS = ['numero', 'id_permanente', 'fecha', 'tipo', 'quien_lo_cometio', 'quien_lo_atrapo',
            'tiempo_hasta_detectarlo', 'altero_conclusion', 'hallazgo_sin_accion', 'resumen', 'fuente',
            'justificacion_tipo']

VOC_T = {'instrumento', 'criterio', 'generalizacion_indebida_del_criterio', 'fabricacion_o_fuera_de_mandato',
         'concurrencia', 'otro', 'no_encontrado'}
VOC_Q = {'coordinador', 'creador', 'auditor', 'compilador', 'cronista', 'probador', 'explorador', 'investigador',
         'sembrador', 'agente_externo', 'director', 'otra_sesion', 'no_determinable'}
VOC_A = VOC_Q | {'arnes', 'humo', 'guardia', 'comparador', 'placebo'}
VOC_TI = {'misma_sesion', 'antes_de_la_corrida', 'despues_de_la_corrida', 'dias', 'no_determinable'}
VOC_AC = {'si', 'no', 'no_determinable'}
VOC_SA = {'si', 'no'}

MESES = {'ene': 1, 'enero': 1, 'jan': 1, 'january': 1, 'feb': 2, 'febrero': 2, 'february': 2, 'mar': 3, 'marzo': 3,
         'march': 3, 'abr': 4, 'abril': 4, 'apr': 4, 'april': 4, 'may': 5, 'mayo': 5, 'jun': 6, 'junio': 6,
         'june': 6, 'jul': 7, 'julio': 7, 'july': 7, 'ago': 8, 'agosto': 8, 'aug': 8, 'august': 8, 'sep': 9,
         'sept': 9, 'set': 9, 'septiembre': 9, 'setiembre': 9, 'september': 9, 'oct': 10, 'octubre': 10,
         'october': 10, 'nov': 11, 'noviembre': 11, 'november': 11, 'dic': 12, 'diciembre': 12, 'dec': 12,
         'december': 12}
RE_ISO = re.compile(r'\b(\d{4})-(\d{2})-(\d{2})\b')
RE_DIA = re.compile(r'\b(\d{1,2})[- ](%s)\b\.?(?:[- ](\d{4}))?' % '|'.join(sorted(MESES, key=len, reverse=True)),
                    re.I)


class Proyecto:
    def __init__(self, ruta_config):
        self.config_path = os.path.abspath(ruta_config)
        self.base = os.path.dirname(self.config_path)
        with open(self.config_path, 'rb') as f:
            cfg = tomllib.load(f)
        p, r = cfg.get('proyecto', {}), cfg.get('registro', {})
        self.prefijo = p.get('prefijo_err', 'ERR')
        self.anio = int(p.get('anio_por_defecto', 2026))
        self.carpeta = r.get('carpeta', 'registro')
        self.generado = r.get('generado', os.path.join(self.carpeta, 'generado'))
        self.clasificacion = r.get('clasificacion', os.path.join(self.carpeta, 'clasificacion_errores.json'))
        self.excluir = [e.strip('/').replace('\\', '/') for e in r.get('excluir_escaneo', ['.git'])]
        self.tam_muestra = int(r.get('tam_muestra', 20))
        self.semilla_muestra = int(r.get('semilla_muestra', 20260929))
        self.rama = r.get('rama', 'HEAD')
        self.fuentes = {}
        for k, v in cfg.get('fuentes', {}).items():
            try:
                n = int(k)
            except ValueError:
                sys.exit('ABORTO: clave de [fuentes] no numérica: %r' % k)
            self.fuentes[n] = v
        self.re_token = lambda n: r'%s-0*%d(?!\d)' % (re.escape(self.prefijo), n)

    def ruta(self, rel):
        return os.path.join(self.base, rel)


def git(base, *args):
    try:
        r = subprocess.run(['git', '-C', base] + list(args), capture_output=True, text=True, encoding='utf-8',
                           timeout=60)
        return r.stdout if r.returncode == 0 else ''
    except (OSError, subprocess.SubprocessError):
        return ''


def excluido(rel, excluir):
    return any(rel == e or rel.startswith(e + '/') for e in excluir)


def escanea(pj):
    occ = collections.defaultdict(list)
    patron = re.compile(r'%s-0*(\d+)(?!\d)' % re.escape(pj.prefijo))
    for raiz, dirs, archivos in os.walk(pj.base):
        rel = os.path.relpath(raiz, pj.base).replace(os.sep, '/')
        rel = '' if rel == '.' else rel
        dirs[:] = [d for d in dirs if not excluido((rel + '/' + d).lstrip('/'), pj.excluir) and d != '__pycache__']
        for a in sorted(archivos):
            if not a.endswith('.md'):
                continue
            rp = (rel + '/' + a).lstrip('/')
            if excluido(rp, pj.excluir):
                continue
            try:
                with open(os.path.join(raiz, a), encoding='utf-8') as f:
                    lineas = f.read().split('\n')
            except (UnicodeDecodeError, OSError):
                continue
            for i, l in enumerate(lineas, 1):
                for m in patron.finditer(l):
                    occ[int(m.group(1))].append('%s:%d' % (rp, i))
    return occ


def lee_lineas(pj, ruta):
    if ruta.startswith('git:'):
        _, ref, archivo = ruta.split(':', 2)
        return git(pj.base, 'show', '%s:%s' % (ref, archivo)).split('\n')
    with open(pj.ruta(ruta), encoding='utf-8') as f:
        return f.read().split('\n')


def parrafo(pj, lineas, i0, tope=1500):
    """Texto de la definición desde la línea i0 (1-based), determinista."""
    primera = lineas[i0 - 1]
    if primera.lstrip().startswith('|'):
        return primera.strip()[:tope]
    out = [primera.strip()]
    es_titulo = primera.lstrip().startswith('#')
    sangria = len(primera) - len(primera.lstrip())
    blancos = 0
    inicio_err = re.compile(r'^[-*]?\s*\**%s-\d+' % re.escape(pj.prefijo))
    for l in lineas[i0:i0 + 40]:
        s = l.strip()
        if s.startswith('#'):
            break
        if not s:
            blancos += 1
            if not es_titulo or blancos >= 2 or len(out) > 1:
                break
            continue
        ind = len(l) - len(l.lstrip())
        if not es_titulo and (s.startswith('- ') or re.match(r'\d+\. ', s)) and ind <= sangria \
                and primera.lstrip().startswith(('- ', '* ')):
            break
        if inicio_err.match(s) and len(out) > 1:
            break
        out.append(s)
        if sum(len(x) for x in out) > tope:
            break
    return ' '.join(out)[:tope]


def fecha_de_texto(t, anio):
    m = RE_ISO.search(t)
    if m:
        return '%s-%s-%s' % m.groups()
    m = RE_DIA.search(t)
    if m:
        return '%s-%02d-%02d' % (m.group(3) or anio, MESES[m.group(2).lower()], int(m.group(1)))
    return None


def fecha_junto_al_token(texto, patron_token, anio):
    """Sólo cuenta la fecha del PRIMER paréntesis que abre a <= 70 caracteres del token: una fecha en otra parte del
    párrafo suele ser la de otro hecho."""
    m = re.search(patron_token, texto)
    if not m:
        return None
    resto = texto[m.end():]
    p = resto.find('(')
    if p < 0 or p > 70:
        return None
    q = resto.find(')', p)
    return fecha_de_texto(resto[p + 1:q if q > 0 else p + 160], anio)


def fecha_de_commit(pj, ruta, n, token, linea_txt):
    """Fecha del primer commit que introduce la DEFINICIÓN: primero el fragmento literal de la línea que empieza en el
    token (git log -S), así no cuentan menciones previas del número; si la línea se editó después, la primera
    aparición del token en ese archivo."""
    if ruta.startswith('git:'):
        _, ref, archivo = ruta.split(':', 2)
    else:
        archivo, ref = ruta, pj.rama
    intentos = []
    m = re.search(re.escape(token) if token else pj.re_token(n), linea_txt)
    if m:
        intentos.append(('-S', linea_txt[m.start():m.start() + 40]))
    if token:
        intentos.append(('-S', token))
    else:   # expresiones POSIX para git -G
        intentos.append(('-G', '%s-0*%d[^0-9]' % (pj.prefijo, n)))
        intentos.append(('-G', '%s-0*%d$' % (pj.prefijo, n)))
    for flag, patron in intentos:
        out = git(pj.base, 'log', ref, '--reverse', '--format=%ad %h', '--date=short', flag + patron, '--', archivo)
        out = [x for x in out.split('\n') if x.strip()]
        if out:
            fc, h = out[0].split()[:2]
            return fc, 'commit %s (%s)' % (h, flag)
    return 'no_determinable', 'no_determinable'


def carga_clasificacion(pj):
    ruta = pj.ruta(pj.clasificacion)
    if not os.path.exists(ruta):
        return {}
    with open(ruta, encoding='utf-8') as f:
        c = json.load(f)
    return {int(k): v for k, v in c.items() if not k.startswith('_')}


def valida(n, c, fuente):
    if c.get('tipo') not in VOC_T or c.get('quien_lo_cometio') not in VOC_Q or c.get('quien_lo_atrapo') not in VOC_A \
            or c.get('tiempo_hasta_detectarlo') not in VOC_TI or c.get('altero_conclusion') not in VOC_AC \
            or c.get('hallazgo_sin_accion') not in VOC_SA:
        sys.exit('ABORTO: vocabulario fuera de lista en ERR-%d (ver registro/ESQUEMA_errores.md): %s' % (n, c))
    if len(c.get('resumen', '').split()) > 20:
        sys.exit('ABORTO: el resumen de ERR-%d pasa de 20 palabras' % n)
    if len(c.get('justificacion_tipo', '').split()) > 15:
        sys.exit('ABORTO: la justificación de ERR-%d pasa de 15 palabras' % n)
    no_usado = bool(fuente.get('no_usado'))
    if no_usado != (c['tipo'] == 'no_encontrado'):
        sys.exit('ABORTO: ERR-%d: tipo "no_encontrado" no coincide con no_usado de [fuentes]' % n)


def valida_ids(filas, prefijo):
    vistos = {}
    patron = re.compile(r'^%s-\d{3,}$' % re.escape(prefijo))
    for r in filas:
        i = r['id_permanente']
        if r['tipo'] == 'no_encontrado' and i == '':
            continue
        if i == 'pendiente':
            continue
        if not patron.match(i):
            sys.exit('ABORTO: id_permanente de ERR-%d inválido: %r (se espera %s-NNN o "pendiente")'
                     % (r['numero'], i, prefijo))
        if i in vistos:
            sys.exit('ABORTO: id_permanente %s repetido en ERR-%d y ERR-%d (nunca se reutiliza)'
                     % (i, vistos[i], r['numero']))
        vistos[i] = r['numero']


def main():
    ap = argparse.ArgumentParser(description='Construye el registro de errores desde config.toml.')
    ap.add_argument('--config', default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                     'config.toml'))
    args = ap.parse_args()
    if not os.path.exists(args.config):
        sys.exit('ABORTO: no existe %s' % args.config)
    pj = Proyecto(args.config)
    occ = escanea(pj)
    clasif = carga_clasificacion(pj)

    defs = {}
    for n in sorted(pj.fuentes):
        f = pj.fuentes[n]
        if f.get('no_usado'):
            defs[n] = dict(numero=n, fuente=f.get('evidencia', 'no_determinable'), fecha='no_determinable',
                           origen_fecha='no_determinable', texto='', apariciones=len(occ.get(n, [])))
            continue
        ruta, linea, token = f['ruta'], int(f['linea']), f.get('token')
        lineas = lee_lineas(pj, ruta)
        if linea < 1 or linea > len(lineas):
            sys.exit('ABORTO: %s no tiene línea %d' % (ruta, linea))
        l = lineas[linea - 1]
        ok = (token in l) if token else re.search(pj.re_token(n), l) is not None
        if not ok:
            sys.exit('ABORTO: %s:%d no contiene %s' % (ruta, linea, token or '%s-%d' % (pj.prefijo, n)))
        texto = parrafo(pj, lineas, linea)
        fecha = fecha_junto_al_token(texto, pj.re_token(n), pj.anio) if not token else None
        origen = 'texto' if fecha else None
        if not fecha:
            fecha, origen = fecha_de_commit(pj, ruta, n, token, l)
        defs[n] = dict(numero=n, fuente='%s:%d' % (ruta, linea), fecha=fecha, origen_fecha=origen, texto=texto,
                       apariciones=len(occ.get(n, [])))
    for n, c in clasif.items():
        if c.get('fecha_manual') and n in defs:
            defs[n]['fecha'] = c['fecha_manual']
            defs[n]['origen_fecha'] = 'manual: ' + c.get('motivo_fecha', '')

    faltan = [n for n in pj.fuentes if n not in clasif]
    if faltan:
        sys.exit('ABORTO: faltan clasificaciones en %s para %s' % (pj.clasificacion, faltan))
    sobran = [n for n in clasif if n not in pj.fuentes]
    if sobran:
        sys.exit('ABORTO: hay clasificaciones sin fuente en [fuentes] de config.toml: %s' % sobran)

    filas = []
    for n in sorted(pj.fuentes):
        c, d = clasif[n], defs[n]
        valida(n, c, pj.fuentes[n])
        filas.append({'numero': n, 'id_permanente': c.get('id_permanente', 'pendiente'), 'fecha': d['fecha'],
                      'tipo': c['tipo'], 'quien_lo_cometio': c['quien_lo_cometio'],
                      'quien_lo_atrapo': c['quien_lo_atrapo'], 'tiempo_hasta_detectarlo': c['tiempo_hasta_detectarlo'],
                      'altero_conclusion': c['altero_conclusion'], 'hallazgo_sin_accion': c['hallazgo_sin_accion'],
                      'resumen': c['resumen'], 'fuente': d['fuente'], 'justificacion_tipo': c['justificacion_tipo']})
    valida_ids(filas, pj.prefijo)

    os.makedirs(pj.ruta(pj.carpeta), exist_ok=True)
    os.makedirs(pj.ruta(pj.generado), exist_ok=True)
    with open(pj.ruta(os.path.join(pj.carpeta, 'errores.csv')), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, lineterminator='\n')
        w.writeheader()
        w.writerows(filas)
    with open(pj.ruta(os.path.join(pj.generado, 'definiciones_errores.json')), 'w', encoding='utf-8',
              newline='\n') as f:
        json.dump({str(k): v for k, v in defs.items()}, f, ensure_ascii=False, indent=1)
        f.write('\n')

    existentes = [r['numero'] for r in filas if r['tipo'] != 'no_encontrado']
    k = min(pj.tam_muestra, len(existentes))
    muestra = random.Random(pj.semilla_muestra).sample(existentes, k) if k else []
    with open(pj.ruta(os.path.join(pj.generado, 'muestra.csv')), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS + ['clasificacion_revisor'], lineterminator='\n')
        w.writeheader()
        por_n = {r['numero']: r for r in filas}
        for n in muestra:
            w.writerow(dict(por_n[n], clasificacion_revisor=''))

    sin_fuente = sorted(n for n in occ if n not in pj.fuentes)
    escribe_resumen(pj, filas, muestra, occ, clasif, sin_fuente)
    print('%s con definición: %d; no usados: %d; muestra: %s' % (
        pj.prefijo, len(existentes), len(filas) - len(existentes), sorted(muestra)))
    if sin_fuente:
        print('AVISO: %s mencionados en el texto sin fuente en [fuentes]: %s (ver %s)' % (
            pj.prefijo, ', '.join('%s-%d' % (pj.prefijo, n) for n in sin_fuente),
            '; '.join(occ[sin_fuente[0]][:3])))
    print('Escrito: %s' % os.path.join(pj.carpeta, 'errores.csv').replace(os.sep, '/'))


def tabla_cruzada(L, filas, f1, f2):
    if not filas:
        L.append('(sin filas)')
        L.append('')
        return
    v1 = sorted(set(r[f1] for r in filas))
    v2 = sorted(set(r[f2] for r in filas))
    L.append('| %s / %s | %s |' % (f1, f2, ' | '.join(v2)))
    L.append('|---|' + '---|' * len(v2))
    for a in v1:
        L.append('| %s | %s |' % (a, ' | '.join(str(sum(1 for r in filas if r[f1] == a and r[f2] == b)) for b in v2)))
    L.append('')


def escribe_resumen(pj, filas, muestra, occ, clasif, sin_fuente):
    P = pj.prefijo
    ex = [r for r in filas if r['tipo'] != 'no_encontrado']
    no_err = {n for n, c in clasif.items() if c.get('no_es_error')}
    ex_e = [r for r in ex if r['numero'] not in no_err]
    L = ['# Resumen de errores (generado por `herramientas/construye_errores.py`; no editar a mano)', '',
         'Fuente de verdad: `%s/errores.csv`. Esquema: `registro/ESQUEMA_errores.md`.' % pj.carpeta, '',
         '## Inventario',
         '- Números registrados: %d; con definición: %d; no usados: %d.' % (len(filas), len(ex), len(filas) - len(ex)),
         '- Entradas que no describen un error cometido (`no_es_error`): %d.' % len(no_err),
         '- Pendientes de aprobación (`id_permanente` = pendiente): %d.' % sum(
             1 for r in filas if r['id_permanente'] == 'pendiente'),
         '- Hallazgos sin acción: %d.' % sum(1 for r in ex if r['hallazgo_sin_accion'] == 'si'),
         '- Mencionados en el texto sin fuente registrada: %s.' % (
             ', '.join('%s-%d' % (P, n) for n in sin_fuente) or 'ninguno'), '']
    for campo in ['tipo', 'quien_lo_cometio', 'quien_lo_atrapo', 'altero_conclusion', 'tiempo_hasta_detectarlo',
                  'hallazgo_sin_accion']:
        cnt = collections.Counter(r[campo] for r in ex)
        L.append('## Por %s (n = %d)' % (campo, len(ex)))
        L.append('| valor | n |')
        L.append('|---|---|')
        for k, v in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0])):
            L.append('| %s | %d |' % (k, v))
        L.append('')
    no_alt = [r for r in ex_e if r['altero_conclusion'] == 'no']
    si_alt = [r for r in ex_e if r['altero_conclusion'] == 'si']
    nd_alt = [r for r in ex_e if r['altero_conclusion'] == 'no_determinable']
    antes = [r for r in no_alt if r['tiempo_hasta_detectarlo'] == 'antes_de_la_corrida']
    L.append('## Atrapados antes de alterar una conclusión')
    L.append('X = errores (sin `no_es_error`) con `altero_conclusion` = no. Cuenta sólo lo que alguien vio: no dice '
             'cuánto se escapó. Para eso hace falta sembrar defectos y medir (agentes `metodo-sembrador` y '
             '`metodo-auditor-ciego`).')
    L.append('')
    L.append('| errores | X (no alteró) | alteró | no determinable | atrapados antes de la corrida |')
    L.append('|---|---|---|---|---|')
    L.append('| %d | %d | %d | %d | %d |' % (len(ex_e), len(no_alt), len(si_alt), len(nd_alt), len(antes)))
    L.append('')
    if ex_e:
        dud_no = [r for r in no_alt if clasif[r['numero']].get('dudoso_altero')]
        dud_si = [r for r in si_alt if clasif[r['numero']].get('dudoso_altero')]
        L.append('Sensibilidad a `dudoso_altero`: X entre %d y %d.' % (len(no_alt) - len(dud_no),
                                                                       len(no_alt) + len(dud_si)))
        L.append('')
    L.append('Alteraron una conclusión: %s.' % (', '.join('%s-%d' % (P, r['numero']) for r in si_alt) or 'ninguno'))
    L.append('')
    L.append('### Cruces (sólo errores, n = %d)' % len(ex_e))
    tabla_cruzada(L, ex_e, 'tiempo_hasta_detectarlo', 'altero_conclusion')
    tabla_cruzada(L, ex_e, 'tipo', 'altero_conclusion')
    tabla_cruzada(L, ex_e, 'quien_lo_atrapo', 'altero_conclusion')
    L.append('## Casos dudosos')
    dud = [r for r in ex if clasif[r['numero']].get('dudoso')]
    for r in dud:
        L.append('- %s-%d (%s, alteró %s): %s' % (P, r['numero'], r['tipo'], r['altero_conclusion'],
                                                 clasif[r['numero']]['dudoso']))
    if not dud:
        L.append('Ninguno.')
    L.append('')
    L.append('## Muestra para revisión ciega')
    L.append('`%s/muestra.csv`: random.Random(%d).sample(existentes, %d): %s.' % (
        pj.generado, pj.semilla_muestra, len(muestra), ', '.join(str(n) for n in muestra) or 'vacía'))
    L.append('')
    with open(pj.ruta(os.path.join(pj.generado, 'resumen_errores.md')), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    main()
