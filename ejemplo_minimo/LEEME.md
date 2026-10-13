# Ejemplo mínimo

Un experimento de juguete que recorre el protocolo entero en menos de un segundo, en Python puro (≥ 3.11), sin
dependencias:

```
python ejemplo_minimo/corre.py          # todo
python ejemplo_minimo/corre.py --humo   # hasta el humo
```

**El sistema bajo estudio** es un agente epsilon-greedy en un bandido de dos brazos cuyos premios se invierten a
mitad de la corrida. **El candidato** sube epsilon cuando la sorpresa media sube. La pregunta, la predicción, los
controles y el criterio de refutación están en `PREREGISTRO.md`, escrito y commiteado antes de correr la serie.

## Qué hace cada archivo

| archivo | papel en el protocolo | regla |
|---|---|---|
| `PREREGISTRO.md` | pregunta, predicción numérica, placebo, refutación; sellado | 4, 13 |
| `config.toml` | sellos de los congelados y fuente del ERR-001 para el registro | 1 |
| `referencia.py` | referencia congelada: no se edita | 1 |
| `construye_candidato.py` → `candidato.py` | construcción por anclas; el generado no se edita a mano | 2 |
| `arnes_identidad.py` | identidad bit a bit con la perilla apagada y un control que debe fallar | 2 |
| `bateria_referencia.py`, `bateria_copiada.py` | argumentos exactos de cada brazo | 12 |
| `corre.py` | el runner: sellos → anclas → identidad → campo a campo → humo → serie → réplica → veredicto | 3, 10, 12, 13 |
| `datos/*.json` | resultados de precisión completa; el veredicto se calcula releyéndolos | 8 |
| `VEREDICTO.md` | lo escribe `corre.py` con la plantilla de `plantillas/VEREDICTO.md` | — |
| `registro/errores.csv` | lo escribe `herramientas/construye_errores.py` con este `config.toml` | — |

## El defecto sembrado

`bateria_copiada.py` trae **a propósito** el error que en JUACO costó dos resultados: al copiar la batería se perdió
un argumento (`alpha=0.1`). El módulo del candidato tiene otro valor por defecto (`alpha=None`, paso 1/n), así que el
candidato habría aprendido con otra regla que la referencia. El arnés de identidad **no** lo ve: compara módulos con
los mismos argumentos, y los módulos son idénticos. Lo ve la **comparación campo a campo** del paso 4, que resuelve
los argumentos efectivos de las dos baterías, valores por defecto incluidos.

`corre.py` muestra qué habría dicho el veredicto con el defecto (en semillas 901–920, fuera de la serie), aplica la
corrección (argumentos de la referencia + perillas), y deja el error numerado como ERR-001 en `VEREDICTO.md` y en
`registro/errores.csv`. El archivo defectuoso se deja tal cual para que el ejemplo se pueda repetir.

## Qué no enseña este ejemplo

- La auditoría por un agente: aquí el defecto lo atrapa un control automático. Para medir cuánto atrapa un auditor
  hacen falta `agentes/metodo-sembrador.md` y `agentes/metodo-auditor-ciego.md`.
- Las corridas largas en varios procesos: todo corre en uno.
- Enmiendas: el preregistro no tiene ninguna.
