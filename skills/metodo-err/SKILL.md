---
name: metodo-err
description: Registra un ERR nuevo (error de instrumento, criterio, lectura o procedimiento) con el siguiente número libre, en el formato del protocolo `metodo`, y regenera registro/errores.csv. Úsala cuando se detecte un fallo del instrumento, se cambie un umbral o criterio, o la persona responsable diga "eso es un ERR" o /metodo-err <descripción>.
---

Qué pasó: $ARGUMENTS

1. Siguiente número libre: el mayor entre los de `[fuentes]` de `config.toml` y los mencionados en el texto (la línea "AVISO" de `python herramientas/construye_errores.py` lista los mencionados sin fuente), más uno. Si hay varias ramas o sesiones, revisarlas también: un número puede chocar (por eso existe `id_permanente`).
2. Formato de la entrada (`plantillas/ERR.md`): **ERR-N (fecha hora):** qué se observó · causa · qué veredictos ya registrados toca (verificado contra los JSON, no supuesto; "ninguno" si es así) · corrección · regla nueva si la hay.
3. Reglas fijas: toda enmienda que cambie un umbral o la forma de un criterio lleva ERR al escribirla (regla 9); nunca se recalibra sobre los datos ya vistos: criterio nuevo y semillas nuevas (regla 4).
4. Dónde va: la entrada en el registro del proyecto (o en el VEREDICTO del bloque); su `archivo:línea` en `[fuentes]` de `config.toml`; su clasificación en `registro/clasificacion_errores.json` con los valores de `registro/ESQUEMA_errores.md` (`id_permanente` = "pendiente" hasta que el coordinador lo apruebe y le asigne `ERR-NNN`). Si nace una regla, va a `PROTOCOLO.md`. Si el ERR afecta a un instrumento, comentario en el código con el número.
5. `python herramientas/construye_errores.py`: debe terminar sin ABORTO.
6. Si un veredicto registrado cambia, se dice explícitamente en el registro y en el commit; si no cambia, también ("el veredicto no cambia, verificado contra X").
7. Commit sólo del ERR y su corrección, con mensaje que empiece por "ERR-N:".

Nota: `config.toml` está protegido por la guardia. Editarlo es trabajo de una persona (o de una sesión con la llave puesta por una persona).
