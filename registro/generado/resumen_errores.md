# Resumen de errores (generado por `herramientas/construye_errores.py`; no editar a mano)

Fuente de verdad: `registro/errores.csv`. Esquema: `registro/ESQUEMA_errores.md`.

## Inventario
- Números registrados: 0; con definición: 0; no usados: 0.
- Entradas que no describen un error cometido (`no_es_error`): 0.
- Pendientes de aprobación (`id_permanente` = pendiente): 0.
- Hallazgos sin acción: 0.
- Mencionados en el texto sin fuente registrada: ninguno.

## Por tipo (n = 0)
| valor | n |
|---|---|

## Por quien_lo_cometio (n = 0)
| valor | n |
|---|---|

## Por quien_lo_atrapo (n = 0)
| valor | n |
|---|---|

## Por altero_conclusion (n = 0)
| valor | n |
|---|---|

## Por tiempo_hasta_detectarlo (n = 0)
| valor | n |
|---|---|

## Por hallazgo_sin_accion (n = 0)
| valor | n |
|---|---|

## Atrapados antes de alterar una conclusión
X = errores (sin `no_es_error`) con `altero_conclusion` = no. Cuenta sólo lo que alguien vio: no dice cuánto se escapó. Para eso hace falta sembrar defectos y medir (agentes `metodo-sembrador` y `metodo-auditor-ciego`).

| errores | X (no alteró) | alteró | no determinable | atrapados antes de la corrida |
|---|---|---|---|---|
| 0 | 0 | 0 | 0 | 0 |

Alteraron una conclusión: ninguno.

### Cruces (sólo errores, n = 0)
(sin filas)

(sin filas)

(sin filas)

## Casos dudosos
Ninguno.

## Muestra para revisión ciega
`registro/generado/muestra.csv`: random.Random(20260929).sample(existentes, 0): vacía.

