# PREREGISTRO: <nombre corto del bloque>

**Escrito ANTES de correr, <fecha y hora>. Autor: <rol y modelo>. Encargo: <ruta del ENCARGO o "propio">.**
<!-- Este archivo se commitea antes de la corrida larga. Después sólo se añaden enmiendas al final, cada una con su ERR. -->

## 1. Pregunta única
<!-- Una sola pregunta que se pueda contestar sí o no con las medidas de abajo. -->

## 2. Hipótesis y mecanismo
<!-- Qué se añade o cambia en el candidato, exactamente (fórmula o diff), y por qué se espera el efecto. -->

**Memoria o estado nuevo:** <!-- Cuántas variables nuevas guarda el candidato; cero si es posible. -->

**Perillas y valores:** <!-- Tabla perilla · valor · de dónde sale (nunca "probé varios y elegí el mejor"). -->

## 3. Instrumento y anclas
<!-- Ruta y sha16 de la referencia congelada, del constructor (construye_*.py) y del candidato generado. -->

## 4. Identidades (se corren primero; si fallan, el runner aborta)
<!-- Cada caso: qué se compara con qué, con qué semillas, y el control que DEBE fallar (perilla encendida ≠ referencia). -->

## 5. Brazos, entorno y semillas o réplicas
<!-- Tabla brazo · perillas · qué es. Entorno exacto. Semillas de la serie y de la réplica: NUEVAS. -->

**Exposición declarada:** <!-- Qué semillas ya vio el autor (mini-prueba, humo, identidad) y por qué no están en la serie. -->

## 6. Medidas
<!-- Cada medida con su definición operativa y el archivo donde queda (JSON de precisión completa). -->

## 7. Predicción numérica (no se recalibra)
<!-- P1, P2...: número con rango y conteo pareado (p. ej. "mediana ≥ +0.03 y pareado ≥ 15/20"). -->

## 8. Placebo y nulo de cada puerta
<!-- Tabla puerta · nulo · margen · probabilidad de que el nulo pase (≤ 0.05) · placebo que debe fallar. -->

## 9. Criterio de refutación, cláusula por cláusula
<!-- "Si P1 falla → ..." para cada predicción, y qué se registra en cada caso. Incluye el resultado "todo pasa". -->

## 10. Controles que pueden fallar
<!-- Qué controles podrían ganarle al candidato (cantidad, momento, barajado) y cómo se construyen. -->

## 11. Trampas revisadas
<!-- Tabla trampa · cómo se evita aquí (las de TRAMPAS.md del proyecto + "criterio que no puede fallar"). -->

## 12. Vocabulario permitido
<!-- Qué palabras podrá usar el informe si todo pasa, y cuáles no. -->

## 13. Costo y quién corre qué
<!-- Runner, humo (--humo, un proceso), tiempo medido de una corrida, quién lanza la corrida larga (el coordinador). -->

## Enmiendas
<!-- Vacío al commitear. Cada enmienda: fecha y hora, ERR-N, antes/después de qué serie, qué cambia y qué NO se rejuzga. -->
