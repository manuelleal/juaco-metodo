---
name: metodo-bloque
description: Corre un bloque preregistrado de punta a punta con el protocolo `metodo` (preregistro commiteado, CPU libre, identidad, campo a campo, humo, corrida larga, réplica, registro, commit). Úsala con /metodo-bloque <ruta del PREREGISTRO o del corre_*.py> o cuando la persona responsable diga "corre el bloque" o "lanza la corrida".
---

Bloque: $ARGUMENTS

Protocolo (reglas 3, 4, 8, 9, 10, 12 y 13 de `PROTOCOLO.md`); no saltar pasos, cada uno deja rastro en el log:

1. **Problema antes de actuar.** Escribe en dos líneas qué problema resuelve el bloque y qué podría fallar (instrumento, criterio, comparador). Si el preregistro no tiene predicción numérica, control que pueda fallar, placebo y semillas NUEVAS, no se corre: se devuelve a `metodo-creador`.
2. **Sellos.** `python herramientas/guardia.py --check`. Si algún congelado cambió, detenerse.
3. **Preregistro commiteado ANTES de correr.** `git log -1 -- <preregistro>`; si no está, `git add` + `git commit` sólo del preregistro y del instrumento.
4. **Identidad.** Salida del arnés pegada en el preregistro o corrida ahora en un proceso (puede hacerlo `metodo-probador`). Perillas apagadas = referencia bit a bit; los controles que deben fallar, fallan.
5. **Entrada campo a campo** de cualquier batería copiada contra la de la referencia, con los valores por defecto resueltos.
6. **CPU libre.** Procesos python vivos con su línea de comando (ver `agentes/metodo-probador.md`). Si hay otra corrida larga, esperar; nunca matar procesos ajenos. Ajustar el número de procesos a la CPU libre.
7. **Humo** que ESCRIBA su JSON (`--humo`, semilla fuera de la serie). Si no escribe JSON, no hay corrida larga.
8. **Corrida larga** con las semillas del preregistro, en segundo plano, con log. Mientras corre, no lanzar otra.
9. **Lectura.** Veredicto por la letra del preregistro desde el JSON de precisión completa (no del log), con el placebo al lado. Si un veredicto depende de UNA semilla en el umbral, réplica en rango nuevo. Subconjuntos sólo con enmienda previa.
10. **Registro.** Encargar a `metodo-cronista` la entrada con log + JSON; revisar sus números contra el JSON antes de pegar. ERR nuevos con `metodo-err`; después, `python herramientas/construye_errores.py`.
11. **Commit** con crudos, log, JSON, preregistro y registro. Push sólo si la persona responsable lo pidió.
12. **Reporte** con el formato de `metodo-veredicto`.

Si algo cae por el instrumento y no por el sistema bajo estudio, se numera ERR y el reintento va preregistrado.
