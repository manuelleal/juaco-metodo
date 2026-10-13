"""Prueba del cotejo preregistro <-> runner: casos que DEBEN abortar y casos que DEBEN pasar.

  python herramientas/prueba_coteja.py

Copia herramientas/ y ejemplo_minimo/ a una carpeta temporal, siembra en la copia un defecto por caso (un umbral
alterado, una perilla alterada, una fila borrada, una enmienda sin ERR...) y compara el código de salida con el
esperado. El caso del umbral se prueba dos veces: con el script sin ejecutar el runner y corriendo corre.py entero,
que debe abortar en el paso 1 sin escribir datos. Imprime N/N y sale 1 si algún caso no se comporta. No toca nada
fuera de la carpeta temporal y la borra al terminar.
"""
import os
import shutil
import subprocess
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


def lee(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def escribe(p, s):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)


def cambia(p, a, b):
    s = lee(p)
    assert s.count(a) == 1, 'ancla no única en %s: %r' % (p, a)
    escribe(p, s.replace(a, b))


def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    tmp = tempfile.mkdtemp(prefix='prueba_coteja_')
    ign = shutil.ignore_patterns('__pycache__', 'datos', 'registro')
    try:
        shutil.copytree(os.path.join(RAIZ, 'herramientas'), os.path.join(tmp, 'herramientas'), ignore=ign)
        shutil.copytree(os.path.join(RAIZ, 'ejemplo_minimo'), os.path.join(tmp, 'ejemplo_minimo'), ignore=ign)
        E = os.path.join(tmp, 'ejemplo_minimo')
        pre, run, bat = (os.path.join(E, x) for x in ('PREREGISTRO.md', 'corre.py', 'bateria_copiada.py'))
        orig = {p: lee(p) for p in (pre, run, bat)}
        umbral = 'UMBRAL_PAREADO, MARGEN_P1, COTA_P3, HUECO = 15,'
        pre_tabla = orig[pre][orig[pre].index('\n## Parámetros sellados') + 1:]

        def restaura():
            for p, s in orig.items():
                escribe(p, s)

        def cli(prereg=pre):
            return subprocess.run([PY, os.path.join(tmp, 'herramientas', 'coteja_preregistro.py'), prereg, run],
                                  capture_output=True, text=True, encoding='utf-8')

        def enmienda(con_err):
            nueva = pre_tabla.replace('| UMBRAL_PAREADO | 15 |', '| UMBRAL_PAREADO | 14 |')
            escribe(pre, orig[pre] + '\n**Enmienda 2%s.** Umbral 15 -> 14.\n\n' % (' (ERR-002)' if con_err else '')
                    + nueva)
            cambia(run, umbral, umbral.replace('15,', '14,'))

        casos = [
            ('el ejemplo tal cual: todo igual', lambda: None, cli, 0),
            ('umbral 15 -> 14 en corre.py (sin ejecutar)', lambda: cambia(run, umbral, umbral.replace('15,', '14,')),
             cli, 1),
            ('umbral 15 -> 14: corre.py entero aborta en el paso 1',
             lambda: cambia(run, umbral, umbral.replace('15,', '14,')),
             lambda: subprocess.run([PY, run], capture_output=True, text=True, encoding='utf-8'), 1),
            ('perilla k 0.3 -> 1.0 en la batería copiada', lambda: cambia(bat, 'k=0.3', 'k=1.0'), cli, 1),
            ('fila COTA_P3 borrada del preregistro', lambda: cambia(pre, '| COTA_P3 | -0.01 |', '| OTRA | 1 |'),
             cli, 1),
            ('valor que hay que ejecutar para leer', lambda: cambia(
                run, 'DESPLAZA_PLACEBO=DESPLAZA_PLACEBO,', 'DESPLAZA_PLACEBO=int(str(DESPLAZA_PLACEBO)),'), cli, 1),
            ('enmienda que baja el umbral SIN ERR', lambda: enmienda(False), cli, 1),
            ('enmienda que baja el umbral CON ERR y runner igual', lambda: enmienda(True), cli, 0),
            ('preregistro sin la sección', lambda: escribe(pre, orig[pre].split('\n## Parámetros sellados')[0]),
             cli, 2),
        ]
        bien = 0
        for nombre, siembra, corre, esperado in casos:
            restaura()
            siembra()
            r = corre()
            ok = r.returncode == esperado
            if nombre.startswith('umbral 15 -> 14: corre.py'):
                ok = ok and 'UMBRAL_PAREADO' in r.stdout and not os.path.exists(os.path.join(E, 'datos', 'humo.json'))
            bien += ok
            print('%s  esperado %d, salió %d  %s' % ('OK  ' if ok else 'MAL ', esperado, r.returncode, nombre))
            if not ok:
                print((r.stdout + r.stderr)[-1500:])
        print('COTEJO: %d/%d casos se comportan como deben' % (bien, len(casos)))
        return 0 if bien == len(casos) else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    sys.exit(main())
