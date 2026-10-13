# ESQUEMA del registro de errores (versión 1, 13-oct-2026)

`registro/errores.csv` lo **genera** `herramientas/construye_errores.py`; no se edita a mano. Sale de dos fuentes:

1. **La definición** de cada ERR en el texto del proyecto (registro, preregistros, veredictos). La tabla `[fuentes]`
   de `config.toml` dice en qué archivo y línea se define cada número; el script verifica que esa línea contiene
   `ERR-N` (o el `token` indicado) y aborta si no.
2. **La clasificación**, hecha a mano, en `registro/clasificacion_errores.json` (una entrada por número).

Codificación UTF-8, separador coma, fin de línea `\n`, una fila por número de ERR (incluidos los que no se usaron).

## Columnas

| columna | qué es | valores permitidos |
|---|---|---|
| `numero` | el número tal como aparece en el texto (`ERR-7` → 7) | entero ≥ 1 |
| `id_permanente` | identificador estable, **asignado por el coordinador al aprobar** la entrada. Nunca se reutiliza, ni si el ERR se retira o se descubre duplicado: la fila queda y se explica en `resumen` | `<PREFIJO>-NNN` (p. ej. `ERR-001`), `pendiente` mientras no se aprueba, vacío sólo si `tipo` = `no_encontrado` |
| `fecha` | fecha de la definición (`AAAA-MM-DD`) | fecha, o `no_determinable` |
| `tipo` | qué falló | ver abajo |
| `quien_lo_cometio` | rol que lo cometió, sólo si el texto lo dice | ver abajo |
| `quien_lo_atrapo` | rol o control que lo destapó, sólo si el texto lo dice | ver abajo |
| `tiempo_hasta_detectarlo` | cuándo se vio respecto de la corrida que habría tocado | `misma_sesion`, `antes_de_la_corrida`, `despues_de_la_corrida`, `dias`, `no_determinable` |
| `altero_conclusion` | si un veredicto o una lectura ya declarada tuvo que corregirse | `si`, `no`, `no_determinable` |
| `hallazgo_sin_accion` | si un auditor lo señaló y quedó registrado **sin corrección** (riesgo aceptado o pendiente) | `si`, `no` |
| `resumen` | qué pasó | texto, ≤ 20 palabras |
| `fuente` | `archivo:línea` de la definición (o la evidencia de que el número no se usó) | texto |
| `justificacion_tipo` | por qué ese `tipo` | texto, ≤ 15 palabras |

### `tipo`

- `instrumento`: el código, la copia, el runner, el arnés o el montaje del entorno producen números falsos, perdidos o
  vacíos (comparadores, claves, rutas, argumentos perdidos, casos de arnés mal hechos, entornos que no hacen la prueba).
- `criterio`: la letra escrita (umbral, banda, puerta, control, medida) no mide lo que dice, o no puede fallar o pasar;
  incluye los cambios de letra tras ver datos numerados por la regla 9.
- `generalizacion_indebida_del_criterio`: un criterio, control o calibración válido en un sistema, etapa o instrumento
  se aplica a otro donde su premisa ya no vale.
- `fabricacion_o_fuera_de_mandato`: afirmación sin la medición que la respalde, o agente que actúa fuera de su mandato
  (matar procesos, lanzar una corrida larga, cambiar la letra por su cuenta).
- `concurrencia`: choque de procesos o recursos compartidos (CPU, archivos, corridas en paralelo).
- `otro`: aritmética de una predicción, erratas, omisiones de informe, defecto del sistema bajo estudio (no del
  método), y los números usados para reservas o cláusulas de cierre (marcar `no_es_error` en la clasificación).
- `no_encontrado`: el número no se usó; la fila existe para que el inventario no tenga huecos sin explicar.

### `quien_lo_cometio` y `quien_lo_atrapo`

Roles: `coordinador`, `creador`, `auditor`, `compilador`, `cronista`, `probador`, `explorador`, `investigador`,
`sembrador`, `agente_externo` (un agente o sesión de otro proyecto), `director` (la persona responsable),
`otra_sesion` (otra sesión del mismo proyecto, p. ej. en la nube), `no_determinable`.

Sólo en `quien_lo_atrapo`, además: `arnes` (el arnés de identidad), `humo`, `guardia` (el hook), `comparador` (la
comparación campo a campo de la entrada de una batería), `placebo` (el criterio corrido sobre el placebo).

Se llenan **sólo si el texto lo dice** ("mío", "lo vio el auditor", "el humo cayó"). Cuando el registro habla en
primera persona, se asigna al coordinador. Todo lo demás, `no_determinable`. Una columna con muchos
`no_determinable` es un dato, no un fallo del script: en JUACO fueron 66 de 126 en `quien_lo_cometio`.

## La clasificación (`registro/clasificacion_errores.json`)

```json
{
  "_nota": "las claves que empiezan por _ se ignoran",
  "7": {
    "id_permanente": "ERR-007",
    "tipo": "instrumento",
    "quien_lo_cometio": "creador",
    "quien_lo_atrapo": "comparador",
    "tiempo_hasta_detectarlo": "antes_de_la_corrida",
    "altero_conclusion": "no",
    "hallazgo_sin_accion": "no",
    "resumen": "La batería copiada omitió alpha; el candidato corría con otro valor por defecto.",
    "justificacion_tipo": "Argumento perdido en la copia: números del instrumento, no del sistema.",
    "no_es_error": false,
    "dudoso": "",
    "fecha_manual": "",
    "motivo_fecha": ""
  }
}
```

Opcionales: `no_es_error` (reserva o cláusula, no un error cometido), `dudoso` (texto: por qué la clasificación es
dudosa), `dudoso_altero` (true si `altero_conclusion` es discutible; entra en el análisis de sensibilidad),
`fecha_manual` + `motivo_fecha` (sobrescriben la fecha extraída, con motivo).

## Fecha

Si el párrafo de la definición trae una fecha en el **primer paréntesis** a ≤ 70 caracteres del token
(`ERR-12 (18 sep, 00:35)`, `ERR-12 (2026-09-18)`), se usa esa. Si no, la del primer commit que introduce la línea en
ese archivo (`git log -S`, luego `-G`). Si no hay git, `no_determinable`. El origen queda en
`registro/generado/definiciones_errores.json`.

## Diferencias con el registro de JUACO (`informe/errores.csv` de ese repositorio)

- Columnas nuevas: `id_permanente` y `hallazgo_sin_accion`.
- `no encontrado` → `no_encontrado`; `antes_de_la_serie` / `despues_de_la_serie` → `antes_de_la_corrida` /
  `despues_de_la_corrida`; `nube` → `otra_sesion`; `quien_lo_atrapo` admite `guardia`, `comparador` y `placebo`.
- Motivo de `id_permanente`: en JUACO el número "ERR-150" se usó en dos ramas para dos errores distintos y hubo que
  renumerar uno a ERR-151. Con un identificador asignado al aprobar, el número del texto puede chocar sin que el
  registro pierda la identidad de cada error.
