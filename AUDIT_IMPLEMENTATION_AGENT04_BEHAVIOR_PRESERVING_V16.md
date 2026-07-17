# Auditoría de implementación — Agente 04 v1.6 preservando comportamiento

## Comparación previa y conflictos detectados

La candidata anterior introducía una ampliación funcional no presente en el notebook 04 original: `assigned_papers`, asignación automática paper–tema, scores de compatibilidad, `paper_theme_assignments.csv`, `UNASSIGNED_PAPERS` y aprobación condicionada a cobertura exhaustiva. Esa ampliación contradice la semántica original de `representative_papers`, que son ejemplos por tema y no una clasificación exhaustiva del corpus.

Conflicto resuelto: todos esos elementos fueron eliminados. No se ocultan como mejoras.

## A. Decisiones previas reutilizadas de 00–03B

- Se reutilizan sin duplicación `AgentInput`, `AgentResult`, `PipelineState`, `StateStore`, fingerprints, atomic writes, credenciales y bootstrap.
- Se preservan PREPARE / EXECUTE / persist / COMMIT / RESUME, `attempt_number`, estados y transición contractual.
- 04 consume la KB y manifiesto de 03, y el bloque 03B cuando está disponible y es compatible.
- No se modifican ni reinterpretan artefactos de 00, 01, 02, 03 o 03B.
- No se repite ingesta, RAG, extracción científica ni extracción cuantitativa.

## B. Infraestructura agéntica aplicada al Agente 04

- `ThematicAnalysisAgent` coordina runtime y herramientas científicas.
- El protocolo persiste resultados y fallos tempranos dentro de la transacción.
- Se conservan intento 1 normal e intento 2 dirigido; no existe intento 3 automático.
- Los artefactos se escriben atómicamente y se registran con SHA-256.
- La transición exitosa es `ADVANCE` con `target_stage = null`.
- El notebook es shell con PRECHECK, REAL MODE y reparación determinista.
- La reparación determinista usa el JSON temático persistido, no llama a OpenAI y conserva los originales.

## C. Comportamiento científico original preservado

Se preservan:

1. lectura de KB científica;
2. resumen del corpus;
3. generación de temas;
4. selección de `representative_papers`;
5. generación de `research_gaps`;
6. dimensiones comparativas;
7. estructura sugerida;
8. tabla comparativa;
9. validación de referencias y títulos;
10. los doce artefactos científicos originales.

`representative_papers` sigue siendo una selección ejemplar. No se usa como asignación exhaustiva. Por compatibilidad contractual, las claves históricas `paper_coverage`, `papers_assigned_to_theme_rate`, `unassigned_paper_rate` y `duplicate_assignment_rate` permanecen como `null`, acompañadas por `coverage_semantics = NOT_APPLICABLE_REPRESENTATIVE_PAPERS_ARE_NON_EXHAUSTIVE`; no afectan el quality gate.

## Reparación técnica permitida

Se conservan únicamente aliases seguros y deterministas:

- `theme → theme_name`;
- `gap → description`;
- `section → section_title`;
- `content → description`;
- `sources → supporting_sources`, `recommended_sources` o `relevant_sources` según bloque;
- IDs `Tn`, `Gn`, `Sn` cuando faltan.

Estas transformaciones recuperan información ya producida y no añaden contenido científico.

## Mejoras funcionales rechazadas por fuera de alcance

- `assigned_papers`;
- asignación automática paper–tema;
- scores de compatibilidad;
- `paper_theme_assignments.csv`;
- reglas para exigir inclusión de todos los papers en temas;
- `UNASSIGNED_PAPERS` como bloqueo;
- rechazo por cobertura exhaustiva;
- reglas específicas del corpus o dominio.

## Resultado esperado del caso real reparado

Cuando el JSON real contiene temas, gaps, estructura y dimensiones recuperables, las referencias son válidas y los artefactos se reconstruyen correctamente:

`COMPLETED → APPROVED → ADVANCE`, con `target_stage = null`.

La ejecución real externa no fue repetida en este entorno.
