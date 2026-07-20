# Auditoría comparativa y trazabilidad RAG por generation_attempt — Agente 06 v1.6

## Alcance

Se compararon literalmente las funciones del notebook `06_agente_redactor(10).ipynb` con la candidata anterior. No se modificaron la validación numérica, el prompt científico, el número de reintentos, el formato de citas, las rutas, los contratos ni las etapas 00–05.

## Diferencias observables detectadas en retrieval

### query_chroma_restricted

Notebook antiguo:
- calcula `per_source_k = max(1, top_k // len(source_filenames) + 1)`;
- limita `n_results` al mínimo entre `per_source_k` y el número real de chunks de la fuente;
- comprueba que `metadata.source_filename` coincida con la fuente solicitada;
- trunca el texto a `MAX_EVIDENCE_CHARS`;
- deduplica y ordena antes de aplicar `top_k`.

Candidata auditada:
- solicita `top_k` por cada fuente;
- no limita por el conteo real de chunks;
- no rechaza explícitamente un `returned_source` inconsistente;
- no aplica `MAX_EVIDENCE_CHARS` en la recuperación;
- aplica un orden distinto en empates.

### query_csv_restricted

Notebook antiguo:
- calcula `score = overlap / max(len(query_tokens), 1)`;
- conserva también filas con score cero antes del ordenamiento;
- trunca a `MAX_EVIDENCE_CHARS`.

Candidata auditada:
- usa `score = overlap`;
- descarta score cero;
- no aplica el mismo truncamiento.

### dedupe_evidence

Notebook antiguo:
- descarta pares fuera de `valid_source_chunk_pairs`;
- ordena por `(-score, source_filename, chunk_id)`.

Candidata auditada:
- no recibe el conjunto cerrado `valid_source_chunk_pairs`;
- ordena solo por score descendente.

### retrieve_section_evidence

La secuencia general sí coincide: Chroma restringido, fallback CSV si faltan evidencias, deduplicación y límite `top_k`. Sin embargo, las diferencias anteriores pueden cambiar qué chunks llegan a `ALLOWED_CITATIONS`.

### build_section_prompt

El texto científico, el presupuesto, `writing_mode`, `focus_mode`, `citation_style`, idioma, evidencia, contexto cuantitativo, errores anteriores, schema y formato de cita coinciden con el notebook antiguo. No se detectó pérdida en la instrucción: cada número solo puede escribirse si aparece en un chunk citado por esa misma oración.

## Corrección de esta candidata

Solo se añadió trazabilidad técnica, sin alterar la selección de evidencia:

`raw_section_outputs/<section_id>_attempt_<n>_rag_trace.json`

Cada traza contiene:
- `section_id`;
- `generation_attempt`;
- consulta usada;
- todos los chunks entregados a la sección;
- `source_filename`;
- `chunk_id`;
- score;
- origen `chroma_restricted` o `csv_lexical_restricted`;
- texto entregado al prompt;
- `allowed_citations`;
- citas emitidas originalmente por el LLM;
- citas después de la normalización determinista.

El reporte parcial referencia cada archivo mediante `rag_trace_path`.

## Interpretación futura

- Caso A: el chunk correcto aparece en `allowed_citations`, pero no en `llm_citations` o el LLM cita otro chunk. No corresponde cambiar retrieval ni validación.
- Caso B: el chunk correcto no aparece en `allowed_citations`. Debe contrastarse la selección real con las diferencias de retrieval documentadas antes de autorizar cualquier corrección.

## Estado contractual

El intento contractual 2 real permanece `COMPLETED / NEEDS_REVISION / HALT_STAGE`. Esta candidata no crea un intento 3 ni publica el borrador.
