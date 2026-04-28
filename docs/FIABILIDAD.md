# Fiabilidad de la IA en PQRSD (estimación teórica)

## Objetivo

Este documento estima, de forma **teórica**, la fiabilidad de la IA en los flujos clave de la plataforma: **asignar**, **aceptar/rechazar/corregir**, **resumir** y **proponer respuesta** para PQRSD.

> **Importante:** los porcentajes aquí presentados **no son métricas reales de producción**. Para obtener porcentajes reales se debe instrumentar y medir cuántas sugerencias de IA son finalmente aceptadas, rechazadas o corregidas por los funcionarios.

## Qué hace la IA en esta página (a grandes rasgos)

En el flujo actual del proyecto, la IA apoya principalmente en:

1. **Asignación/ruteo** de PQRS a secretaría sugerida.
2. **Pre-clasificación** que luego pasa por validación humana (acciones: validar, rechazar, solicitar corrección).
3. **Generación de resumen** (lead, temas, resumen ejecutivo).
4. **Generación de posible respuesta** o explicación asistida (p. ej. explicación de rechazo/estado).

## Supuestos para la estimación teórica

- Operación con **modelo local gratuito en Ollama** (no SOTA).
- Dominio legal-administrativo con lenguaje ambiguo y alto costo de error.
- Datos de entrada heterogéneos (redacción ciudadana, faltantes, ruido).
- Flujo con **human-in-the-loop** (la IA propone, el funcionario decide).

## Porcentajes teóricos de fiabilidad

| Proceso                                 | Fiabilidad teórica actual (modelo gratuito Ollama) | Fiabilidad teórica con modelo más potente | Mejora teórica |
| --------------------------------------- | -------------------------------------------------: | ----------------------------------------: | -------------: |
| Asignación a secretaría                 |                                                62% |                                       80% |         +18 pp |
| Sugerencia de aceptar/rechazar/corregir |                                                58% |                                       76% |         +18 pp |
| Resumen de PQRS                         |                                                74% |                                       88% |         +14 pp |
| Posible respuesta (borrador)            |                                                66% |                                       82% |         +16 pp |
| **Índice global estimado**              |                                            **64%** |                                   **81%** |     **+17 pp** |

### Lectura recomendada de estos números

- **64%** significa: en teoría, ~6 de cada 10 sugerencias podrían salir útiles sin cambios mayores con el modelo local gratuito.
- Con modelos más potentes, se espera subir a **~81%** en condiciones equivalentes.
- La mejora proyectada es de **+17 puntos porcentuales** (rango razonable: **+12 a +20 pp** según calidad de prompts, datos y controles).

## Por qué estos porcentajes son razonables (marco conceptual)

1. La literatura legal sobre agentes IA muestra ganancias fuertes en velocidad y soporte operativo, pero mantiene la necesidad de supervisión humana en decisiones sensibles.
2. En el material de referencia de impacto laboral de IA se evidencia la brecha entre **capacidad teórica** y **uso observado**, lo que justifica no sobreestimar desempeño real desde el inicio.
3. En legal triage e investigación legal, la precisión depende mucho de contexto, trazabilidad de fuentes y validación humana; por eso la decisión final no debe automatizarse al 100% en PQRSD.

## Cómo convertir esto en porcentaje real del proyecto

Medir al menos estos indicadores en operación:

- **Tasa de aceptación de sugerencias IA** = validaciones `VALIDATE` / total casos con sugerencia.
- **Tasa de rechazo de sugerencias IA** = `REJECT` / total casos con sugerencia.
- **Tasa de corrección solicitada** = `REQUEST_CORRECTION` / total casos con sugerencia.
- **Utilidad de resumen** = resúmenes usados sin edición mayor / total resúmenes consultados.
- **Utilidad de borrador de respuesta** = respuestas usadas con edición leve / total borradores.

Con 4–8 semanas de datos, se puede reemplazar esta estimación teórica por KPI real por secretaría, tipo de PQRS y nivel de riesgo.

## Cómo mejorar los porcentajes sin cambiar de modelo

Además de usar un modelo más potente, hay mejoras de proceso y datos que normalmente elevan bastante la calidad.

| Palanca (sin cambiar modelo) | Acción concreta | Impacto teórico esperado |
|---|---|---|
| Glosarios de dominio | Mejorar `glosarios/` con sinónimos locales, expresiones ciudadanas reales y ejemplos frontera (aceptable vs rechazable). | +3 a +6 pp en clasificación/ruteo |
| Banco de ejemplos | Mantener un set curado de casos reales anotados (aceptar/rechazar/corregir) para recalibrar prompts y reglas. | +2 a +5 pp en decisión sugerida |
| Retroalimentación operativa | Capturar motivo de rechazo/corrección del funcionario y convertirlo en reglas/patrones reutilizables. | +2 a +4 pp sostenidos |
| Umbrales de confianza | Definir umbral por tipo de caso (alto riesgo = revisión obligatoria, bajo riesgo = sugerencia asistida). | Menos falsos positivos críticos |
| QA de resúmenes y respuestas | Checklist corto: fidelidad al texto original, completitud, tono institucional, no inventar hechos. | +3 a +6 pp en utilidad de resumen/respuesta |
| Monitoreo por secretaría | Tablero semanal con tasas de aceptación, rechazo y corrección por dependencia y tipo de PQRS. | Detección temprana de deriva/sesgo |

### Meta teórica solo por mejora operativa (sin cambiar modelo)
- Índice global actual estimado: **64%**.
- Con disciplina operativa (glosarios + ejemplos + feedback + control de calidad), meta razonable: **72% a 75%**.
- Es decir, una mejora teórica de **+8 a +11 pp** sin cambiar de LLM.

### Ciclo recomendado de mejora continua
1. Medir semanalmente: aceptación, rechazo, corrección y calidad de resumen/respuesta.
2. Revisar los casos rechazados/corregidos con mayor frecuencia.
3. Actualizar glosarios y ejemplos con esos casos.
4. Ajustar prompts/reglas y volver a medir.
5. Congelar versión ganadora y repetir el ciclo.

## Recomendaciones

1. Mantener la IA como **sistema de recomendación**, no de decisión final automática.
2. Registrar por caso: sugerencia de IA, acción humana final y motivo.
3. Definir umbral de confianza para escalamiento obligatorio a revisión humana.
4. Priorizar mejora de modelo + prompting + glosarios antes de automatizar más decisiones.
5. Revisar mensualmente sesgos por tipo de ciudadano, territorio y tema para evitar impactos desiguales.

## Fuentes

- The Shift AI. _AI Agents in Legal Industry: Automating Client Interaction, Compliance and Case Support_.  
  https://www.theshift.ai/blog/ai-agents-in-legal-industry-automating-client-interaction-compliance-and-case-support
- Ratomir. _The Impact of AI on Legal Services_.  
  https://www.ratomir.com/blog/the-impact-of-ai-on-legal-services/
- Massenkoff, M. & McCrory, P. (2026). _Labor market impacts of AI: A new measure and early evidence_ (PDF local: `Nowcasting_Econ-Report-v16.pdf`).
- Anthropic Research. _Labor market impacts of AI_ (versión web).  
  https://www.anthropic.com/research/labor-market-impacts
- NIST. _AI Risk Management Framework (AI RMF 1.0)_.  
  https://www.nist.gov/itl/ai-risk-management-framework
