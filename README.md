# juaco-metodo

· [English](README.en.md)

Un **protocolo para dirigir agentes LLM en investigación computacional, con un registro numerado de errores**.
Reglas escritas, roles fijos, plantillas, unas pocas herramientas que hacen cumplir parte de las reglas, y un
registro donde cada error del método queda con quién lo cometió, quién o qué lo atrapó, cuándo, y si cambió una
conclusión.

Sale del proyecto JUACO (https://github.com/manuelleal/juaco, DOI 10.5281/zenodo.23041088), donde un equipo de agentes de Claude Code corrió
durante septiembre y octubre de 2026 cientos de experimentos preregistrados y usó 153 números de ERR (126 con
definición escrita; los demás quedaron sin usar). JUACO es el caso de
uso de origen; este repositorio separa el método del sistema que se estudiaba allí.

## Qué es y qué no es

Es la continuación de trabajos de 2026 que ya proponen piezas parecidas: verificadores en código que hacen cumplir
reglas de investigación (Philippov y otros, *Glite ARF*, arXiv 2606.27416), investigación asistida por IA con
preregistro, métricas congeladas y compuertas (Zhou y Yu, arXiv 2608.10858) y taxonomías de fallos de agentes en
investigación automática (Fei y otros, arXiv 2608.14905). Casi todas sus piezas existen por separado: el preregistro
viene de la metaciencia, la identidad bit a bit es la prueba de regresión de la ingeniería de software, los controles
que pueden fallar son los controles negativos de la epidemiología. Lo que este repositorio añade es **el registro de
errores atribuidos** (quién, quién lo atrapó, cuándo, si alteró una conclusión) llevado en un proyecto real, su
esquema, y el procedimiento para medir cuánto atrapa cada control sembrando defectos.

No es un banco de pruebas de agentes ni una biblioteca de experimentos. No corre nada por ti.

## Para quién

Para una persona o un equipo pequeño que usa agentes LLM para diseñar, programar y correr experimentos
computacionales (simulaciones, modelos, mejoras de una herramienta) y necesita que un resultado aguante una auditoría:
que no dependa de una semilla, de un argumento perdido en una copia, de un umbral movido después de ver los datos o de
una frase que dice más de lo que se midió.

## Instalación en tres pasos

Requisitos: Python ≥ 3.11, git. Sin dependencias externas.

1. **Copia el método a tu proyecto.** Desde la raíz de tu proyecto, con este repositorio en `../metodo`:
   ```sh
   cp -r ../metodo/PROTOCOLO.md ../metodo/ROLES.md ../metodo/plantillas ../metodo/registro ../metodo/herramientas ../metodo/config.toml .
   ```
2. **Configúralo.** Edita `config.toml`: el propósito del proyecto (primera línea de cada encargo), los archivos de
   la referencia congelada (`python herramientas/guardia.py --sella ruta` da el sello) y las carpetas protegidas.
   Comprueba:
   ```sh
   python herramientas/guardia.py --check
   python herramientas/construye_errores.py
   ```
3. **Instala agentes, skills y la guardia** en Claude Code siguiendo `agentes/INSTALAR.md`.

Antes de usarlo en tu proyecto, mira el ejemplo de juguete, que recorre el protocolo entero en un segundo:

```sh
python ejemplo_minimo/corre.py
```

Termina imprimiendo `VEREDICTO.md` con un error sembrado a propósito (ERR-001, un argumento omitido al copiar una
batería) que la comparación campo a campo atrapa antes de la corrida, y lo deja en `ejemplo_minimo/registro/errores.csv`.
Su veredicto es **INCOMPLETO**: la predicción principal se cumple en la serie y en la réplica, pero el control de
igual exploración pasa en la serie (15/20) y cae en la réplica (13/20). Se dejó así: es lo que dice la letra del
preregistro, y es justo lo que el protocolo existe para no maquillar.

## Qué hace cumplir el código y qué es sólo disciplina

"Código" quiere decir que una herramienta de este repositorio lo bloquea o lo detecta sola, **si está instalada** (la
guardia como hook de Claude Code) **o si tu runner copia el patrón** de `ejemplo_minimo/corre.py`. "Disciplina" quiere
decir que depende de que alguien lo haga y otro lo revise. En JUACO, el arnés y el humo atraparon 16 de los 89
errores cuyo atrapador consta; una regla que sólo está escrita se puede incumplir sin que nadie lo note.

| regla (`PROTOCOLO.md`) | qué exige | cumplimiento | dónde |
|---|---|---|---|
| 1 | la referencia congelada no se edita; nada destructivo | **código** | `guardia.py`: bloquea editar congelados y `config.toml`, commitear con un sello roto, `push --force`, `reset --hard`, `clean`, borrado recursivo de carpetas protegidas; `--check` |
| 2 | construcción por anclas e identidad bit a bit con control que debe fallar | **código** en el arnés y el runner; escribirlos es disciplina | `construye_candidato.py`, `arnes_identidad.py`, pasos 2 y 3 de `corre.py` |
| 3 | sólo el coordinador lanza corridas largas | **código** sólo para `corre_*.py --help`; el resto, disciplina | `guardia.py` |
| 4 | preregistro commiteado antes de correr; no recalibrar | **código** parcial: la guardia bloquea `corre_*.py` sin `--humo` si no hay `PREREGISTRO*.md` commiteado y limpio; el ejemplo verifica sello y commit. El contenido, disciplina | `guardia.py`, paso 1 de `corre.py` |
| 5 | lo que se declara es lo que se midió | disciplina | auditor, punto 6 |
| 6 | entregas en su carpeta, informe corto, sin commits de agentes | disciplina | encargo y auditor |
| 7 | lo de fuera es dato y se vuelve a medir | disciplina | preregistro |
| 8 | subconjuntos por enmienda previa; anclas del JSON completo | disciplina; el ejemplo calcula el veredicto releyendo los JSON | paso 8 de `corre.py` |
| 9 | toda enmienda de criterio lleva ERR al escribirla | disciplina; aviso automático de ERR mencionados sin fuente | `construye_errores.py` |
| 10 | réplica en semillas nuevas; una semilla en el umbral pide más | disciplina; el ejemplo corre serie y réplica y marca los conteos a ±1 del umbral | pasos 6 a 8 de `corre.py` |
| 11 | cada encargo empieza con el propósito y trae contrato | disciplina | `plantillas/ENCARGO.md`, skill `metodo-encargo` |
| 12 | batería copiada: campo a campo, argumentos exactos, humo que escribe | **código** en el runner que lo copie | pasos 4 y 5 de `corre.py` |
| 13 | todo criterio corre su placebo | disciplina en la letra; **código** en el runner que lo calcule | puerta P0 de `corre.py` |
| 14 | lo que corre es lo preregistrado: tabla `## Parámetros sellados` ↔ `PREREGISTRADO` del runner, valor a valor | **código** para lo que esté en la tabla (aborta con la lista de diferencias; una tabla nueva sin ERR también aborta); disciplina el llenar la tabla y apuntar a las variables que se usan | `coteja_preregistro.py`, `prueba_coteja.py` (9 casos), paso 1 de `corre.py` |
| registro | vocabulario cerrado, longitudes, `id_permanente` único | **código** | `construye_errores.py` aborta si algo no cumple el esquema |

## Qué tan bien funciona

Medido una vez, en un proyecto, por agentes de la misma familia: en JUACO se sembraron defectos en 60 copias de
bloques cerrados (y 20 más de réplica) y un auditor de sólo lectura las revisó a ciegas, con la clave sellada. Atrapó
28 de 40 en la serie: 15/16 de instrumento, 6/6 de lectura, pero sólo 7/18 de criterio, y dio falsas alarmas en 6 de 20
copias limpias (3 de 7 en la réplica). Por eso existen la regla 14 (cotejo preregistro ↔ runner en código) y el
`dato_que_confirma` obligatorio de los auditores; ninguno de los dos cambios está medido todavía. Diseño, números de
serie y réplica, y limitaciones: [`MEDICION.md`](MEDICION.md).

## Qué hay

```
MEDICION.md             la medición del auditor con errores sembrados (serie y réplica)
PROTOCOLO.md            14 reglas, cada una con su porqué (un ERR de JUACO o la medición) y cómo se comprueba
ROLES.md                coordinador, creador, auditor, cronista, probador (y apoyo); qué puede y qué no cada uno
plantillas/             PREREGISTRO, ENCARGO, VEREDICTO, ERR, ESTADO
registro/               errores.csv (vacío), ESQUEMA_errores.md, generado/
herramientas/           construye_errores.py, guardia.py + guardia.sh + ejemplo_settings.json,
                        prueba_guardia.py (21 casos), arnes_identidad_ejemplo.py,
                        coteja_preregistro.py + prueba_coteja.py (9 casos), puntua.py (medición sembrada)
agentes/, skills/       definiciones para Claude Code e INSTALAR.md
ejemplo_minimo/         el experimento de juguete de punta a punta
config.toml             rutas, congelados, guardia y fuentes del registro de errores
```

## Qué falta

- **Cuánto atrapa el auditor se midió una sola vez** (`MEDICION.md`), en un proyecto y con agentes de la misma familia
  sembrando y auditando. Falta repetirla con un auditor de otra familia y en otro proyecto, y medir si la regla 14 y el
  `dato_que_confirma` obligatorio cambian algo. El procedimiento está en `agentes/metodo-sembrador.md`,
  `agentes/metodo-auditor-ciego.md` y `herramientas/puntua.py`.
- **Nadie audita al coordinador** salvo la persona responsable, y si todos los agentes son del mismo modelo la
  auditoría es circular. Ver `ROLES.md`.
- La guardia sólo funciona dentro de Claude Code (es un hook) y sólo con los comandos que reconoce.
- Probado en Windows 11 con Python 3.14 y Git Bash; no probado en Linux ni macOS.

## Licencia y cita

Código bajo MIT (`LICENSE`); textos, plantillas, esquema y datos de ejemplo bajo CC BY 4.0 (`LICENSE-DATA`). Para
citar: `CITATION.cff` (DOI pendiente). Autor: Christiam Manuel Puentes Leal (ORCID 0009-0002-2570-3397).
