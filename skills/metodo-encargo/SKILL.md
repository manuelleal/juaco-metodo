---
name: metodo-encargo
description: Arma el encargo a un agente del protocolo `metodo` (metodo-creador, metodo-auditor, metodo-cronista, metodo-compilador, metodo-probador, metodo-explorador, metodo-investigador) con propósito, contrato, modelo por dificultad y entregable. Úsala cuando haya que delegar trabajo a un agente, o con /metodo-encargo <rol> <tarea>.
---

Rol y tarea: $ARGUMENTS

Elegir el agente por dificultad: el modelo más capaz para diseño y algoritmos difíciles (`metodo-creador`, `metodo-compilador`, `metodo-investigador`); uno intermedio para auditoría y crónica (`metodo-auditor`, `metodo-cronista`); el más barato para pruebas y preguntas cortas (`metodo-probador`, `metodo-explorador`). Pocos agentes a la vez; cada uno en su carpeta.

Antes de armar el encargo:
- **Semáforo**: verde = el agente lo hace y otro lo revisa; amarillo = el agente propone y la persona responsable decide; rojo = no se delega (afirmar algo que sólo la persona recuerda, firmar, enviar, decidir qué evidencia entra, fusionar a la rama principal). Si es rojo, no hay encargo.
- **Datos**: si la tarea toca documentos de identidad, contraseñas o datos de personas con nombre, no entran al prompt sin autorización expresa para esa vez; lo demás, anonimizado o generalizado.
- **Problema descompuesto**: una sola pieza por encargo. Si el encargo corrige un fallo, escribir la causa de fondo, no el síntoma.

Plantilla del prompt (`plantillas/ENCARGO.md`; todas las líneas, en este orden):
1. **Propósito** (primera frase, regla 11 de `PROTOCOLO.md`): `[proyecto].proposito` de `config.toml` y "el método manda sobre el cómo".
2. **Contexto mínimo**: archivos a leer primero (2 a 4), referencia congelada vigente, ERR recientes que le atañen, y lo que ya se descartó.
3. **Intención**: qué se necesita y para qué decisión sirve. Sin dar la hipótesis como cierta: un agente que recibe la conclusión tiende a devolverla confirmada.
4. **Contrato**: qué entrega exactamente (archivos, formato, informe de máximo una página), en qué carpeta, y qué NO puede hacer (corridas largas, commits, matar procesos, tocar congelados).
5. **Criterio de aceptación** verificable: identidad N/N, humo que escribe JSON, predicción numérica con rango, control que puede fallar.
6. **Presupuesto**: tiempo, corridas, pasos, semillas.
7. **Cierre**: "Declara tus propias predicciones refutadas y lo que no pudiste verificar."

Si hay que devolver el trabajo: tres partes, qué funciona, qué falla, qué se necesita. Máximo tres rondas; si a la tercera no sale, el defecto está en el encargo y se reescribe.

Después de recibir el trabajo: auditar a mano los números (o con `metodo-auditor` en sólo lectura) antes de darlo por bueno; el trabajo de agentes externos no se da por bueno nunca sin auditoría. Reportar con la skill `metodo-veredicto`.
