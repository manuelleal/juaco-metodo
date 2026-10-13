---
name: metodo-estado
description: Estado actual de un proyecto que sigue el protocolo `metodo`, en una tabla corta (hecho / en curso / pendiente) con máximo dos decisiones para la persona responsable. Úsala al abrir sesión, cuando pregunten "cómo vamos" o "qué está pendiente", o con /metodo-estado.
---

Foco pedido: $ARGUMENTS (vacío = todo el proyecto).

Pasos (todo con comandos de lectura, sin editar nada):
1. `git status --short` y `git log --oneline -8`.
2. Leer el `registro/ESTADO.md` más reciente, el plan vigente del proyecto y las últimas 40 líneas del registro.
3. `python herramientas/guardia.py --check` (sellos de la referencia congelada).
4. Procesos python vivos con su línea de comando (ninguna corrida larga arranca si hay otra corriendo): ver `agentes/metodo-probador.md`.
5. `python herramientas/construye_errores.py` y leer `registro/generado/resumen_errores.md` (ERR pendientes de aprobar, mencionados sin fuente, hallazgos sin acción).

Salida, en este orden y en lenguaje llano (`plantillas/ESTADO.md`):
1. Una línea de veredicto: VAMOS BIEN / VAMOS MAL / HAY ALGO MODESTO.
2. Tabla: fila por frente, columnas Hecho · En curso · Pendiente · Bloqueo. Numerar con las fases del plan del proyecto, nunca con fases inventadas.
3. Cambios sin commitear (lista de archivos y qué son).
4. Máximo DOS decisiones para la persona responsable, cada una con la opción recomendada primero.
5. Siguiente paso concreto con el comando exacto.
