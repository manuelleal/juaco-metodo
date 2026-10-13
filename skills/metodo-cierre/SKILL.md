---
name: metodo-cierre
description: Cierre de jornada en un proyecto que sigue el protocolo `metodo`. Deja todo registrado, commiteado y el estado al día para que la siguiente sesión retome sin releer. Úsala cuando digan "cerremos", "cierre del día", "deja todo listo", o con /metodo-cierre.
---

Notas para el cierre: $ARGUMENTS

1. `git status --short`. Clasificar cada archivo: crudo/log/JSON de una corrida registrada (entra), instrumento verificado (entra), borrador sin identidad (entra marcado como borrador en el mensaje), basura (se lista, no se borra sin permiso).
2. Ninguna corrida larga viva (procesos con su línea de comando). Si hay una, esperar o dejar dicho en el estado qué corre y desde cuándo.
3. Registro: toda corrida terminada hoy tiene su entrada. Las que falten: `metodo-cronista`.
4. ERR: todos los de hoy tienen fuente en `config.toml` y clasificación; `python herramientas/construye_errores.py` termina sin ABORTO y sin AVISO de mencionados sin fuente (o el aviso queda explicado en el estado).
5. `python herramientas/guardia.py --check`: sellos intactos.
6. `registro/ESTADO.md` nuevo (`plantillas/ESTADO.md`): hecho hoy · preparado y pendiente · decisiones de la persona responsable tomadas hoy (hora y palabras) · siguiente candidato · ERR nuevos (rango) · quién retome lee X, Y, Z en ese orden.
7. Commit con mensaje claro. Push sólo si la persona responsable lo pidió. Verificar `git status` limpio.
8. Reporte final: tabla corta hecho / pendiente / decisión, y el comando exacto con el que arranca la siguiente sesión.
