"""Guardia del método: hook PreToolUse de Claude Code (se activa con .claude/settings.json, vía guardia.sh).

Versión general de `.claude/guardia.py` de JUACO (https://github.com/manuelleal/juaco). Rutas, congelados y carpetas
protegidas salen de config.toml. Frena mecánicamente:
  - Edit/Write sobre un archivo de [congelados] o sobre config.toml (que es el registro de congelados);
  - `git commit` con un congelado cuyo sha256 ya no coincide con su sello;
  - `git push --force`, `git reset --hard`, `git clean` y el borrado recursivo (rm -r, Remove-Item -Recurse) que
    nombre una carpeta de [guardia].carpetas_protegidas;
  - runners (patron_runner) con --help/-h: no reconocen la bandera y lanzan la corrida de verdad (ERR-115 de JUACO);
  - runners sin --humo cuando en su carpeta no hay un PREREGISTRO*.md commiteado y sin cambios (regla 4).

Salida 0 = permitir; 2 = bloquear (el motivo va por stderr y lo lee el agente). Si la guardia misma falla, permite:
no bloquea por un error propio. Única llave: la variable de entorno de [guardia].variable_llave = 1 (por defecto
METODO_CONGELAR), puesta por una persona en el entorno de la sesión; desactiva los bloqueos de congelados y config.

Uso fuera del hook:
  python herramientas/guardia.py --check [--config config.toml]   compara sellos; sale 1 si alguno cambió
  python herramientas/guardia.py --sella RUTA [--config ...]      imprime la línea para [congelados]
Busca config.toml en: --config, $METODO_CONFIG, $CLAUDE_PROJECT_DIR/config.toml, la carpeta padre de herramientas/.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

PY = r'\bpy(?:thon[0-9.]*)?(?:\.exe)?\s+(?:-\S+\s+)*'   # "python", "python3", "py", "python.exe -u ..." antes del script


def salida_utf8():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')   # en Windows la salida entubada no es UTF-8
        except Exception:
            pass


def bloquear(motivo):
    salida_utf8()
    sys.stderr.write('GUARDIA (bloqueado): ' + motivo + '\n')
    sys.exit(2)


def busca_config(explicita=None):
    candidatos = [explicita, os.environ.get('METODO_CONFIG')]
    if os.environ.get('CLAUDE_PROJECT_DIR'):
        candidatos.append(os.path.join(os.environ['CLAUDE_PROJECT_DIR'], 'config.toml'))
    candidatos.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.toml'))
    for c in candidatos:
        if c and os.path.exists(c):
            return os.path.abspath(c)
    return None


def carga(ruta_config):
    import tomllib
    with open(ruta_config, 'rb') as f:
        cfg = tomllib.load(f)
    g = cfg.get('guardia', {})
    return dict(
        base=os.path.dirname(ruta_config),
        config=ruta_config,
        congelados={k.replace('\\', '/'): v for k, v in cfg.get('congelados', {}).items()},
        llave=os.environ.get(g.get('variable_llave', 'METODO_CONGELAR')) == '1',
        protegidas=list(g.get('carpetas_protegidas', ['datos', 'experimentos', 'registro'])),
        patron_runner=g.get('patron_runner', r'corre_\w*\.py'),
        bloquear_help=bool(g.get('bloquear_help_en_runners', True)),
        exigir_prereg=bool(g.get('exigir_preregistro_commiteado', True)),
    )


def sha16(ruta):
    with open(ruta, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def normal(ruta):
    return os.path.normcase(os.path.realpath(ruta))


def git(base, *args):
    return subprocess.run(['git', '-C', base] + list(args), capture_output=True, text=True, timeout=20)


# ------------------------------------------------------------------------------------------------- revisiones
def revisar_archivo(c, ruta):
    if not ruta or c['llave']:
        return
    objetivo = normal(ruta if os.path.isabs(ruta) else os.path.join(c['base'], ruta))
    protegidos = {normal(os.path.join(c['base'], r)): r for r in c['congelados']}
    protegidos[normal(c['config'])] = 'config.toml'
    if objetivo in protegidos:
        bloquear(f'{protegidos[objetivo]} está congelado o es el registro de congelados. Regla 1 de PROTOCOLO.md: la '
                 'referencia no se edita; una versión nueva se construye por anclas en un archivo nuevo y la congela '
                 'una persona.')


def revisar_commit(c):
    if c['llave']:
        return
    for ruta, esperado in c['congelados'].items():
        p = os.path.join(c['base'], ruta)
        real = sha16(p) if os.path.exists(p) else 'NO EXISTE'
        if real != esperado:
            bloquear(f'el congelado {ruta} cambió ({real} != {esperado}). Detenerse y averiguar por qué; no se commitea.')


def revisar_preregistro(c, script, cwd):
    """Regla 4: la corrida larga exige un PREREGISTRO*.md commiteado y limpio en la carpeta del runner."""
    ruta = script if os.path.isabs(script) else os.path.join(cwd, script)
    carpeta = os.path.dirname(os.path.abspath(ruta))
    r = git(carpeta, 'ls-files', '--', 'PREREGISTRO*.md')
    if r.returncode != 0:
        return   # fuera de git o git ausente: la guardia no bloquea por lo que no puede comprobar
    commiteados = [x for x in r.stdout.split('\n') if x.strip()]
    if not commiteados:
        bloquear(f'{script}: no hay PREREGISTRO*.md commiteado en {carpeta}. Regla 4: se preregistra y se commitea '
                 'antes de la corrida larga (el humo con --humo sí puede correr).')
    sucio = git(carpeta, 'status', '--porcelain', '--', *commiteados).stdout.strip()
    if sucio:
        bloquear(f'{script}: el preregistro tiene cambios sin commitear ({sucio}). Commitea la enmienda (con su ERR) '
                 'antes de correr.')


def revisar_comando(c, cmd, cwd):
    runner = re.compile(PY + r'(\S*' + c['patron_runner'] + r')')
    for seg in re.split(r'&&|\|\||[;|\n]', cmd):
        s = seg.strip()
        m = runner.search(s)
        if m:
            if c['bloquear_help'] and re.search(r'(?:^|\s)(?:--help|-h)(?:\s|$)', s):
                bloquear('los runners no reconocen --help/-h y lanzan la corrida de verdad (ERR-115 de JUACO). '
                         'Lee el docstring del runner o su preregistro.')
            if c['exigir_prereg'] and not re.search(r'(?:^|\s)--humo(?:\s|$)', s):
                revisar_preregistro(c, m.group(1).strip('"\''), cwd)
        g = re.match(r'(?:\S+=\S+\s+)*git\s+(?:-C\s+\S+\s+)?(\S+)(.*)$', s)
        if g:
            sub, resto = g.group(1), g.group(2)
            if sub == 'push' and re.search(r'(?:^|\s)(?:--force\S*|-f)(?:\s|$)', resto):
                bloquear('push forzado prohibido: reescribe historia compartida.')
            if sub == 'reset' and '--hard' in resto:
                bloquear('`git reset --hard` descarta trabajo sin vuelta atrás. Usa `git stash` o una rama.')
            if sub == 'clean':
                bloquear('`git clean` borra archivos sin rastrear (humos, datos sin registrar). Nada destructivo.')
            if sub == 'commit':
                revisar_commit(c)
        nombres = '|'.join(re.escape(p) for p in c['protegidas'])
        if nombres and re.match(r'rm\s', s) and re.search(r'(?:^|\s)-\w*[rR]\w*|--recursive', s) and \
                re.search(r'(?:^|[\s/"\'\\])(%s)\b' % nombres, s):
            bloquear('borrar recursivamente %s está prohibido (nada destructivo).' % ', '.join(c['protegidas']))
        if nombres and re.match(r'Remove-Item\b', s, re.I) and re.search(r'-Recurse', s, re.I) and \
                re.search(r'(%s)' % nombres, s):
            bloquear('borrar recursivamente %s está prohibido (nada destructivo).' % ', '.join(c['protegidas']))


# ------------------------------------------------------------------------------------------------- modos
def hook():
    try:
        datos = json.load(sys.stdin)
        ruta_config = busca_config()
        if not ruta_config:
            return 0
        c = carga(ruta_config)
        herramienta = datos.get('tool_name', '')
        entrada = datos.get('tool_input') or {}
        if herramienta in ('Edit', 'Write', 'NotebookEdit', 'MultiEdit'):
            revisar_archivo(c, entrada.get('file_path') or entrada.get('notebook_path') or '')
        elif herramienta in ('Bash', 'PowerShell'):
            revisar_comando(c, entrada.get('command') or '', datos.get('cwd') or c['base'])
    except Exception:   # la guardia nunca bloquea por un error propio (SystemExit de bloquear() sí pasa)
        return 0
    return 0


def cli(argv):
    salida_utf8()
    explicita = argv[argv.index('--config') + 1] if '--config' in argv else None
    ruta_config = busca_config(explicita)
    if not ruta_config:
        print('No encuentro config.toml (usa --config).')
        return 1
    c = carga(ruta_config)
    if '--sella' in argv:
        rel = argv[argv.index('--sella') + 1].replace('\\', '/')
        print('"%s" = "%s"' % (rel, sha16(os.path.join(c['base'], rel))))
        return 0
    mal = 0
    for ruta, esperado in sorted(c['congelados'].items()):
        p = os.path.join(c['base'], ruta)
        real = sha16(p) if os.path.exists(p) else 'NO EXISTE'
        ok = real == esperado
        mal += not ok
        print('%s  %s  %s' % ('OK   ' if ok else 'ROTO ', esperado, ruta) + ('' if ok else '  (real %s)' % real))
    print('CONGELADOS: %d/%d intactos' % (len(c['congelados']) - mal, len(c['congelados'])))
    return 1 if mal else 0


if __name__ == '__main__':
    if '--check' in sys.argv or '--sella' in sys.argv:
        sys.exit(cli(sys.argv))
    sys.exit(hook())
