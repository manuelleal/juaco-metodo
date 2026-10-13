# PREREGISTRO: exploración por sorpresa en un bandido no estacionario (ejemplo mínimo)

**Escrito ANTES de correr la serie y la réplica, 13-oct-2026. Autor: creador (Claude Opus 5.5). Encargo: construir
el ejemplo mínimo del repositorio `metodo`.** Este archivo está sellado en `ejemplo_minimo/config.toml`: si cambia,
`corre.py` aborta. Es un ejemplo de juguete para enseñar el protocolo; su veredicto vale sólo para este entorno.

## 1. Pregunta única
¿Subir epsilon en proporción a la sorpresa media reciente (|recompensa − valor esperado|) mejora la recompensa del
cuarto que sigue a una inversión no avisada de los brazos, y lo hace por el **momento** del aumento y no por la
**cantidad** de exploración?

## 2. Hipótesis y mecanismo
Tras la inversión, el brazo elegido deja de pagar lo esperado: la sorpresa sube, epsilon sube, el agente prueba el
otro brazo antes. Fuera de la inversión la sorpresa es baja y epsilon vuelve a su valor base.

```
sb  <- (1 - beta) * sb + beta * |r - Q[a]|        (después de la acción; el paso t usa sb de los pasos anteriores)
eps_t = min(1, eps + k * sb)                       (k = 0: epsilon constante, la referencia)
```

**Memoria o estado nuevo:** un escalar (`sb`).

**Perillas y valores:**

| perilla | valor | de dónde sale |
|---|---|---|
| `k` | 0.3 | elegido entre {0.3, 1.0} mirando la mini-prueba en semillas 1–3 (declarado en §5: es una elección con datos) |
| `beta` | 0.05 | ventana de ~20 pasos; fijado antes, sin probar otros |

## 3. Instrumento y anclas

| archivo | sha16 | qué es |
|---|---|---|
| `referencia.py` | `e6155bea36a2799b` | referencia congelada |
| `construye_candidato.py` | (se verifica en corre.py) | constructor por anclas; fija el sha del origen |
| `candidato.py` | `8dd95fa8958c3fe2` | generado; corre.py lo reconstruye y aborta si no coincide |
| `bateria_referencia.py` | | argumentos exactos de la referencia: `pasos=4000, eps=0.01, alpha=0.1, medias=(0.8, 0.2), sigma=0.05` |
| `bateria_copiada.py` | | argumentos del candidato; se comparan campo a campo con los de la referencia antes de correr |

## 4. Identidades (se corren primero; si fallan, el runner aborta)
`arnes_identidad.py`, semillas 1–5 × 4 escenarios: **J1** k=0 ≡ referencia (recompensas, acciones, epsilon y Q,
bit a bit); **J2** k=0 con beta=0.5 ≡ referencia (la lectura sólo mide); **C1** control que debe fallar: k=0.3
difiere en ≥ 18/20. Comprobado por el autor antes de escribir esto: **J1 20/20, J2 20/20, C1 20/20 distintas.**

## 5. Brazos, entorno y semillas

| brazo | qué es |
|---|---|
| REF | la referencia con su batería |
| CAND | el candidato, k=0.3, beta=0.05, con los argumentos exactos de la referencia |
| CONST | **control de cantidad**: la referencia con epsilon constante = la media del epsilon que aplicó CAND **en esa misma semilla**. Misma exploración total, sin el momento |
| PLACEBO | la referencia con otra semilla de ruido (semilla + 10000): sirve para correr el criterio P1 sobre el nulo |

**Entorno:** bandido de dos brazos, medias (0.8, 0.2), ruido gaussiano sigma = 0.05, 4000 pasos, los brazos se
invierten en el paso 2000. Q3 = recompensa media en los pasos [2000, 3000).

**Semillas:** serie **101–120**, réplica **121–140**. Humo: semilla 99. Contrafactual del defecto (sólo didáctico,
no entra en el veredicto): 901–920.

**Exposición declarada.** El autor vio enteras las semillas 1–3 en la mini-prueba, con dos entornos: (i) eps 0.1,
sigma 0.2, alpha 0.1, donde el candidato **empeoraba** Q3 en las 3 semillas con k ∈ {0.5, 1, 2}; (ii) eps 0.01,
sigma ∈ {0.05, 0.1}, k ∈ {0.3, 1.0}. **Se eligió el entorno (ii) porque en (i) la referencia ya se recupera sola y no
hay hueco que medir. Eso es elegir el entorno a favor de la pregunta**: el veredicto no se extiende a otros entornos.
Mini-prueba en (ii) con sigma 0.05, k 0.3 (semillas 1, 2, 3): Q3 REF 0.7235 / 0.7559 / 0.5726; CAND 0.7685 / 0.7841 /
0.6940; CONST 0.7747 / 0.7144 / 0.7671. Ninguna semilla ≥ 99 se ha visto.

## 6. Medidas
Por semilla y brazo, en el JSON de precisión completa: `Q3`, `total` (recompensa media de toda la corrida),
`eps_medio`, y `huella` (sha16 de las recompensas, para detectar dos brazos idénticos).

## 7. Predicción numérica (no se recalibra)
- **P1 [mejora]:** mediana de (Q3 CAND − Q3 REF) ≥ +0.02 **y** CAND > REF pareado en ≥ 15/20. *Predicción del autor:
  pasa, con mediana en [+0.02, +0.10].*
- **P2 [es el momento, no la cantidad]:** CAND > CONST pareado en ≥ 15/20 **y** mediana de (Q3 CAND − Q3 CONST) > 0.
  *Predicción del autor: CAE, con el conteo pareado entre 6 y 14 (la mini-prueba dio 1/3).*
- **P3 [no cuesta]:** mediana de (total CAND − total REF) ≥ −0.01. *Predicción del autor: pasa.*

## 8. Placebo y nulo de cada puerta

| puerta | nulo | margen | prob. de pasar bajo el nulo | placebo |
|---|---|---|---|---|
| P1 | CAND = REF: diferencia de mediana 0, pareado 10/20 | +0.02 y 15/20 | P(X ≥ 15 \| n=20, p=0.5) = 0.021 | **P0:** P1 calculado con PLACEBO en lugar de CAND debe CAER |
| P2 | CAND = CONST | 15/20 y > 0 | 0.021 | — |
| P3 | sin costo | −0.01 | no aplica (es una cota, no un efecto) | — |

## 9. Criterio de refutación
- **G (hay hueco)** falla — mediana de Q3 REF fuera de [0.30, 0.78] — → INCOMPLETO: el entorno no deja medir.
- **P0** falla (el placebo pasa P1) → INCOMPLETO: el criterio no distingue el ruido del efecto.
- Serie y réplica no coinciden en alguna puerta → INCOMPLETO: hace falta una tercera serie preregistrada.
- **P1** cae → NO FUNCIONA.
- **P1** pasa y **P2** cae → HAY ALGO PERO MODESTO: ayuda explorar más; el momento no añade nada medible.
- **P1** y **P2** pasan y **P3** cae → HAY ALGO PERO MODESTO: canje medido.
- Todo pasa → FUNCIONA, sólo en este entorno.

## 10. Controles que pueden fallar
CONST (cantidad), PLACEBO (nulo del criterio), C1 del arnés (perilla conectada), y la alarma de filas idénticas: si
CAND y REF tienen la misma `huella` en todas las semillas, una vía está apagada y no hay veredicto.

## 11. Trampas revisadas

| trampa | cómo se evita |
|---|---|
| "más exploración" confundida con "exploración a tiempo" | CONST con el epsilon medio de CAND en la misma semilla |
| criterio que no puede fallar | P0 (placebo) y conteos con probabilidad bajo el nulo ≤ 0.05 |
| argumentos distintos entre brazos | comparación campo a campo de las baterías antes de correr |
| leer de un log redondeado | el veredicto se calcula releyendo los JSON escritos |

## 12. Vocabulario permitido
"Sube la recompensa del cuarto que sigue a la inversión" si P1 pasa. "Por el momento y no por la cantidad" sólo si P2
pasa. Nada de "detecta el cambio", "entiende" ni "se adapta" en general.

## 13. Costo y quién corre qué
`python ejemplo_minimo/corre.py` (todo, un proceso, segundos) o `--humo` (hasta el humo). 4 brazos × 40 semillas ×
4000 pasos, más 40 corridas del contrafactual. Es un ejemplo: lo corre quien lo instale.

## Enmiendas
Ninguna.
