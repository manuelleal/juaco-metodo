"""Prueba de la guardia: casos que DEBEN bloquear y casos que DEBEN pasar, sobre un proyecto temporal.

  python herramientas/prueba_guardia.py

Crea en una carpeta temporal un proyecto con config.toml, un congelado sellado y dos carpetas de experimento (una con
preregistro commiteado, otra sin él); alimenta a guardia.py con la entrada JSON que mandaría Claude Code y compara el
código de salida (2 = bloquea, 0 = permite) con el esperado. Imprime N/N y sale 1 si algún caso no se comporta.
No toca nada fuera de la carpeta temporal y la borra al terminar.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

GUARDIA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'guardia.py')


def prepara(d):
    os.makedirs(os.path.join(d, 'sistema'))
    os.makedirs(os.path.join(d, 'experimentos', 'con_prereg'))
    os.makedirs(os.path.join(d, 'experimentos', 'sin_prereg'))
    ref = os.path.join(d, 'sistema', 'referencia.py')
    with open(ref, 'w', encoding='utf-8', newline='\n') as f:
        f.write('def corre(semilla):\n    return semilla\n')
    sello = hashlib.sha256(open(ref, 'rb').read()).hexdigest()[:16]
    with open(os.path.join(d, 'config.toml'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('[congelados]\n"sistema/referencia.py" = "%s"\n\n[guardia]\nvariable_llave = "PRUEBA_LLAVE"\n'
                'carpetas_protegidas = ["datos", "experimentos", "registro"]\n' % sello)
    for sub in ('con_prereg', 'sin_prereg'):
        with open(os.path.join(d, 'experimentos', sub, 'corre_bloque.py'), 'w', newline='\n') as f:
            f.write('print("corrida")\n')
    with open(os.path.join(d, 'experimentos', 'con_prereg', 'PREREGISTRO_bloque.md'), 'w', newline='\n') as f:
        f.write('# PREREGISTRO\n')
    for args in (['init', '-q'], ['add', '-A'],
                 ['-c', 'user.name=prueba', '-c', 'user.email=prueba@ejemplo', 'commit', '-q', '-m', 'inicio']):
        subprocess.run(['git', '-C', d] + args, check=True, capture_output=True)
    return sello


def llama(d, entrada, llave=False):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=d)
    env.pop('METODO_CONFIG', None)
    env.pop('PRUEBA_LLAVE', None)
    if llave:
        env['PRUEBA_LLAVE'] = '1'
    datos = dict(entrada, cwd=d)
    r = subprocess.run([sys.executable, GUARDIA], input=json.dumps(datos), capture_output=True, text=True, env=env,
                       encoding='utf-8')
    return r.returncode, r.stderr.strip()


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    d = tempfile.mkdtemp(prefix='prueba_guardia_')
    try:
        prepara(d)
        bash = lambda c: {'tool_name': 'Bash', 'tool_input': {'command': c}}
        edit = lambda p: {'tool_name': 'Edit', 'tool_input': {'file_path': p}}
        casos = [
            # (nombre, entrada, código esperado, con llave)
            ('editar congelado', edit(os.path.join(d, 'sistema', 'referencia.py')), 2, False),
            ('editar congelado con ruta relativa', edit('sistema/referencia.py'), 2, False),
            ('editar config.toml', edit(os.path.join(d, 'config.toml')), 2, False),
            ('editar congelado CON llave', edit(os.path.join(d, 'sistema', 'referencia.py')), 0, True),
            ('editar archivo libre', edit(os.path.join(d, 'experimentos', 'con_prereg', 'notas.md')), 0, False),
            ('push --force', bash('git push --force origin main'), 2, False),
            ('push -f', bash('git push -f'), 2, False),
            ('push normal', bash('git push origin main'), 0, False),
            ('reset --hard', bash('git reset --hard HEAD~1'), 2, False),
            ('clean', bash('git clean -fd'), 2, False),
            ('rm -rf carpeta protegida', bash('rm -rf experimentos/viejo'), 2, False),
            ('Remove-Item -Recurse protegida', bash('Remove-Item -Recurse registro\\x'), 2, False),
            ('rm de un archivo suelto', bash('rm notas.txt'), 0, False),
            ('runner con --help', bash('python experimentos/con_prereg/corre_bloque.py --help'), 2, False),
            ('runner sin preregistro', bash('python experimentos/sin_prereg/corre_bloque.py'), 2, False),
            ('humo sin preregistro', bash('python experimentos/sin_prereg/corre_bloque.py --humo'), 0, False),
            ('runner con preregistro', bash('python -u experimentos/con_prereg/corre_bloque.py'), 0, False),
            ('commit con congelado intacto', bash('git commit -m x'), 0, False),
        ]
        ok = 0
        for nombre, entrada, esperado, llave in casos:
            cod, err = llama(d, entrada, llave)
            bien = cod == esperado
            ok += bien
            print('%s %-36s esperado %d, salió %d%s' % ('BIEN' if bien else 'MAL ', nombre, esperado, cod,
                                                        '' if bien else '  ' + err))
        # preregistro con cambios sin commitear -> bloquea
        with open(os.path.join(d, 'experimentos', 'con_prereg', 'PREREGISTRO_bloque.md'), 'a') as f:
            f.write('cambio sin commitear\n')
        cod, _ = llama(d, bash('python experimentos/con_prereg/corre_bloque.py'))
        ok += cod == 2
        print('%s %-36s esperado 2, salió %d' % ('BIEN' if cod == 2 else 'MAL ', 'preregistro modificado', cod))
        # congelado roto -> el commit se bloquea y --check sale 1
        with open(os.path.join(d, 'sistema', 'referencia.py'), 'a') as f:
            f.write('# cambio\n')
        cod, _ = llama(d, bash('git commit -m x'))
        ok += cod == 2
        print('%s %-36s esperado 2, salió %d' % ('BIEN' if cod == 2 else 'MAL ', 'commit con congelado roto', cod))
        r = subprocess.run([sys.executable, GUARDIA, '--check', '--config', os.path.join(d, 'config.toml')],
                           capture_output=True, text=True, encoding='utf-8')
        ok += r.returncode == 1
        print('%s %-36s esperado 1, salió %d' % ('BIEN' if r.returncode == 1 else 'MAL ', '--check con congelado roto',
                                                 r.returncode))
        total = len(casos) + 3
        print('GUARDIA: %d/%d casos como se esperaba' % (ok, total))
        return 0 if ok == total else 1
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
