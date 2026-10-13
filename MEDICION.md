# Qué tan bien funciona el auditor: medición con errores sembrados

**Medido una vez, en un proyecto, por agentes de la misma familia.** Hecho en JUACO el 13-oct-2026. Datos, clave
abierta, notas de cada auditor y veredicto en la rama `medicion-protocolo-20261013` de
https://github.com/manuelleal/juaco (carpeta
[`experimentos/medicion_protocolo/20261013/`](https://github.com/manuelleal/juaco/tree/medicion-protocolo-20261013/experimentos/medicion_protocolo/20261013),
commit `2f047085`). Los números de abajo están copiados de su `VEREDICTO.md`, con sus mismos redondeos.

## Diseño (preregistrado antes de sembrar, commit `2d1eb41e`)

- **Unidad:** una copia de un bloque cerrado de JUACO, con preregistro, runner y JSON de resultados. 10 bloques
  elegidos con `random.Random(20261013)`.
- **Serie:** 60 copias = 40 con un defecto sembrado (18 de criterio, 16 de instrumento, 6 de lectura u otro, en la
  proporción del registro de errores de JUACO) + 20 limpias. Cada defecto se puede ver leyendo los archivos, sin correr.
- **Réplica:** 20 copias nuevas (13 con defecto, 7 limpias), defectos nuevos, semilla `20261014`. Se preregistró
  **sólo** para la decisión sobre falsas alarmas, que en la serie cruzó su umbral por una copia.
- **Clave sellada:** la clave quedó fuera del repositorio y su sha256 se commiteó antes de auditar; se abrió después
  del último lote y coincidió (serie `237bbfa1…`, réplica `370fb5ad…`).
- **Lotes de una copia por bloque:** seis copias del mismo bloque lado a lado delatan el defecto por comparación. Antes
  de auditar se repartieron en lotes de 10 (6 en la serie, 2 en la réplica), una copia por bloque, y cada lote lo
  auditó un agente distinto (`agentes/metodo-auditor-ciego.md`, Sonnet, sólo lectura). Cambio de montaje anterior a los
  datos, numerado allí como error 196 del registro de JUACO.
- **Puntaje:** acierto = una fila `defecto=si` en el mismo archivo que la clave; falsa alarma = copia limpia con una
  fila `defecto=si` de confianza alta o media. Wilson al 95 %. `herramientas/puntua.py` reproduce las dos tablas.

## Números

| Medida | Serie (60 copias) | Wilson 95 % | Réplica (20 copias) | Wilson 95 % |
|---|---|---|---|---|
| Sensibilidad total | 28/40 = 0,70 | 0,55–0,82 | 7/13 = 0,54 | 0,29–0,77 |
| Criterio | 7/18 = 0,39 | 0,20–0,61 | 2/6 = 0,33 | 0,10–0,70 |
| Instrumento | 15/16 = 0,94 | 0,72–0,99 | 3/5 = 0,60 | 0,23–0,88 |
| Lectura / otro | 6/6 = 1,00 | 0,61–1,00 | 2/2 | 0,34–1,00 |
| Falsas alarmas | 6/20 = 0,30 | 0,15–0,52 | 3/7 = 0,43 | 0,16–0,75 |

Predicciones de la serie: P1 sensibilidad total entre 0,40 y 0,70 → en el borde superior; P2 instrumento > criterio →
sí; P3 falsas alarmas ≤ 3/20 → **NO**. Veredicto: **HAY ALGO MODESTO**. En la réplica, las sensibilidades son
descriptivas (no se preregistraron) y más bajas que en la serie.

**Juntando serie y réplica, de forma descriptiva y NO preregistrada** (juntarlas no estaba en ningún preregistro):
total 35/53 = 0,66; instrumento 18/21 = 0,86; criterio 9/24 = 0,38; falsas alarmas 9/27 = 0,33.

## Qué decidió y qué cambió aquí

- Instrumento ≥ 0,50: el auditor de sólo lectura **cuenta** como control para errores de instrumento (la lectura
  final de JUACO lo extiende a los de lectura, con 6/6 y 2/2).
- Criterio 0,39 en la serie: **no basta** para errores de criterio. → Regla 14 de `PROTOCOLO.md`:
  `herramientas/coteja_preregistro.py` coteja en código la tabla `## Parámetros sellados` del preregistro con el runner
  antes de correr.
- Falsas alarmas > 5/20, confirmado en la réplica (3/7): **el formato de hallazgos cambia**. → `dato_que_confirma`
  obligatorio para confianza alta o media en `agentes/metodo-auditor-ciego.md` y `agentes/metodo-auditor.md`.
- Ninguno de los dos cambios está medido todavía: no se sabe si el cotejo atrapa los errores de criterio que el auditor
  no vio, ni si el dato obligatorio baja las falsas alarmas sin bajar la detección.

## Limitaciones

- **Misma familia:** sembró un agente Claude y auditó otro Claude; puede haber sesgo compartido. No se ha repetido con
  un auditor de otra familia.
- **Un solo proyecto, una sola vez**, un auditor por lote, sin tiempo medido por copia.
- **Las copias limpias arrastran errores reales** de los bloques originales (los sembradores avisaron de varios antes de
  auditar); parte de las falsas alarmas son eso y se cuentan como falsas alarmas porque así se preregistró.
- **Puntaje por archivo** (error 197 del registro de JUACO): un defecto sembrado en el preregistro y señalado en el
  runner cuenta como fallo. Se dejó como estaba preregistrado.
- Los sha de logs y JSON se resellaron en cada copia: quita una pista que en un repositorio real sí existe.
- El `puntua.py` original comparaba la réplica con el sello de la serie por una ruta fija (error 198 de JUACO); la
  clave era correcta y se verificó a mano. La versión de `herramientas/` recibe el sello por argumento.
- No mide errores que ningún sembrador imaginó.
