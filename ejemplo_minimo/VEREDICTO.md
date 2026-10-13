# VEREDICTO: ejemplo mínimo · exploración por sorpresa en un bandido no estacionario

**INCOMPLETO (falta réplica: serie y réplica no coinciden en P2)**

**Preregistro:** `PREREGISTRO.md` (sha16 69b045281821bfc5), commit 9f468be 2026-10-13.
**Resultados:** `datos/serie_101-120.json` (sha16 59670df68854a439), `datos/replica_121-140.json` (sha16 8559bcd6de4d4659).

## Errores registrados en este bloque
**ERR-001 (2026-10-13):** la batería copiada para el candidato (`bateria_copiada.py`) omitió un argumento que la referencia pasa explícitamente — alpha: referencia 0.1 (batería) · candidato None (defecto del módulo) — y el candidato habría corrido con el valor por defecto de su módulo · causa: instrumento (argumento perdido en la copia; defecto sembrado a propósito para el ejemplo) · lo atrapó: la comparación campo a campo del paso 4, antes de la corrida · veredictos que toca: ninguno; contrafactual en semillas 901–920 (fuera de la serie): con el defecto, P1 habría dado mediana -0.3127 y 2/20 pareado, es decir P1 CAE · corrección: argumentos del candidato = `KWARGS_REFERENCIA` + `PERILLAS` · regla: 12 de `PROTOCOLO.md`.

## Tabla

| puerta | predicción (PREREGISTRO §7-§9) | serie 101–120 | réplica 121–140 | pasa |
|---|---|---|---|---|
| G | mediana Q3 REF en [0.30, 0.78] | mediana Q3 REF 0.6991 | mediana Q3 REF 0.7127 | sí |
| P0 | el placebo CAE el criterio de P1 | mediana +0.0089, 11/20 | mediana -0.0312, 7/20 | sí |
| P1 | CAND − REF ≥ +0.02 y ≥ 15/20 | mediana +0.0792, 20/20 | mediana +0.0536, 19/20 | sí |
| P2 | CAND − CONST > 0 y ≥ 15/20 | mediana +0.0039, 15/20 | mediana +0.0022, 13/20 | no replica |
| P3 | total CAND − REF ≥ −0.01 | mediana +0.0154 | mediana +0.0126 | sí |

## Lectura honesta

Por la letra, subir epsilon con la sorpresa mejora la recompensa del cuarto que sigue a la inversión en las dos series. Contra el control con la misma exploración total (CONST) pasa en una serie y cae en la otra: que el momento añada algo sobre la cantidad no está demostrado, y tampoco descartado. Conteos a ±1 del umbral: P2. Por la regla 10, eso pide otra réplica antes de afirmar nada fuera de este ejemplo. Es un juguete con el entorno elegido a favor de la pregunta (PREREGISTRO §5): no dice nada de otros entornos.

## Qué sigue

Lo que manda el preregistro (§9): una tercera serie con la misma letra en semillas nuevas (p. ej. 141–160), declarada antes en una enmienda; el preregistro está sellado, así que la enmienda la vuelve a sellar una persona. Este ejemplo se detiene aquí a propósito: no se cambia la letra para que el veredicto salga redondo.

En tu proyecto: copia la estructura (sellos → anclas → identidad → campo a campo → humo → serie → réplica → veredicto desde el JSON) y sustituye el sistema de juguete por el tuyo. Ver `LEEME.md`.
