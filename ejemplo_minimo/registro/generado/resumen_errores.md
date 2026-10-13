# Resumen de errores (generado por `herramientas/construye_errores.py`; no editar a mano)

Fuente de verdad: `registro/errores.csv`. Esquema: `registro/ESQUEMA_errores.md`.

## Inventario
- Números registrados: 1; con definición: 1; no usados: 0.
- Entradas que no describen un error cometido (`no_es_error`): 0.
- Pendientes de aprobación (`id_permanente` = pendiente): 0.
- Hallazgos sin acción: 0.
- Mencionados en el texto sin fuente registrada: ninguno.

## Por tipo (n = 1)
| valor | n |
|---|---|
| instrumento | 1 |

## Por quien_lo_cometio (n = 1)
| valor | n |
|---|---|
| sembrador | 1 |

## Por quien_lo_atrapo (n = 1)
| valor | n |
|---|---|
| comparador | 1 |

## Por altero_conclusion (n = 1)
| valor | n |
|---|---|
| no | 1 |

## Por tiempo_hasta_detectarlo (n = 1)
| valor | n |
|---|---|
| antes_de_la_corrida | 1 |

## Por hallazgo_sin_accion (n = 1)
| valor | n |
|---|---|
| no | 1 |

## Atrapados antes de alterar una conclusión
X = errores (sin `no_es_error`) con `altero_conclusion` = no. Cuenta sólo lo que alguien vio: no dice cuánto se escapó. Para eso hace falta sembrar defectos y medir (agentes `metodo-sembrador` y `metodo-auditor-ciego`).

| errores | X (no alteró) | alteró | no determinable | atrapados antes de la corrida |
|---|---|---|---|---|
| 1 | 1 | 0 | 0 | 1 |

Sensibilidad a `dudoso_altero`: X entre 1 y 1.

Alteraron una conclusión: ninguno.

### Cruces (sólo errores, n = 1)
| tiempo_hasta_detectarlo / altero_conclusion | no |
|---|---|
| antes_de_la_corrida | 1 |

| tipo / altero_conclusion | no |
|---|---|
| instrumento | 1 |

| quien_lo_atrapo / altero_conclusion | no |
|---|---|
| comparador | 1 |

## Casos dudosos
Ninguno.

## Muestra para revisión ciega
`registro/generado/muestra.csv`: random.Random(20260929).sample(existentes, 1): 1.

