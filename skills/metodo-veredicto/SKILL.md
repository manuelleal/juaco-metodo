---
name: metodo-veredicto
description: Formato obligatorio para reportar cualquier resultado (corrida, agente, auditoría, prueba) en un proyecto que sigue el protocolo `metodo`: primero un veredicto en una línea, después una tabla corta, después qué sigue. Úsala siempre que haya un resultado que entregar, o con /metodo-veredicto.
---

Resultado a reportar: $ARGUMENTS

Estructura fija, sin excepciones (`plantillas/VEREDICTO.md`):

1. **Primera línea, en mayúsculas, una de estas:** FUNCIONA · NO FUNCIONA · HAY ALGO PERO MODESTO · INCOMPLETO (falta X). Sin matices en esa línea.
2. **Tabla corta** (máximo 6 filas): puerta o brazo · lo que predijo el preregistro · lo medido · pasa/cae. Si hubo réplica, una columna por serie. El placebo va en la tabla.
3. **Lectura honesta en máximo 4 frases:** qué se sostiene por la letra, qué es exploratorio, qué lo refutaría, qué costó.
4. **Qué sigue:** un paso concreto con comando o encargo, y como máximo una decisión para la persona responsable, con la opción recomendada primero.

Prohibido: abrir con matices antes del veredicto; declarar con una sola serie; vocabulario no medido ("entiende", "planifica"). Si honestamente no hay nada, decirlo directo.
