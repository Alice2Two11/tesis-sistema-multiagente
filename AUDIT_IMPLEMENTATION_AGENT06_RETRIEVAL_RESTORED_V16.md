# AUDITORÍA DE RESTAURACIÓN DEL RETRIEVAL — AGENTE 06 V1.6

## Alcance

La candidata restaura únicamente el comportamiento observable del retrieval del notebook `06_agente_redactor(10).ipynb`. No modifica prompt, validación numérica, normalización, formato de citas, reintentos, artefactos, rutas, PipelineState, etapas 00–05 ni Agente 07.

## Causa raíz

La candidata anterior conservaba la secuencia general Chroma restringido → fallback CSV → deduplicación → top-k, pero había simplificado reglas internas que afectan qué chunks llegan a `ALLOWED_CITATIONS`. El diagnóstico real mostró que los chunks numéricos correctos existían en `chunks_clean_for_rag.csv`, pero quedaban fuera de la evidencia seleccionada.

## Comparación función por función

### `query_chroma_restricted()`

Restaurado literalmente:

- `per_source_k = max(1, top_k // len(source_filenames) + 1)`;
- `n_results = min(per_source_k, max(1, cantidad_real_de_chunks_del_paper))`;
- filtro Chroma por `source_filename`;
- descarte cuando `metadata.source_filename != source`;
- texto limitado por `MAX_EVIDENCE_CHARS`;
- score `1.0 - distance`;
- orden posterior `-score, source_filename, chunk_id`.

### `query_csv_restricted()`

Restaurado literalmente:

- tokenización original;
- `score = overlap / max(len(query_tokens), 1)`;
- inclusión inicial de filas con score cero;
- texto limitado por `MAX_EVIDENCE_CHARS`;
- orden estable mediante la deduplicación original.

### `dedupe_evidence()`

Restaurado literalmente:

- descarte de pares fuera de `valid_source_chunk_pairs`;
- descarte de evidencia no sustantiva;
- conservación del mayor score por `source_filename + chunk_id`;
- orden exacto `-score, source_filename, chunk_id`.

### `retrieve_section_evidence()`

Restaurado literalmente:

1. Chroma restringido;
2. fallback CSV solo si Chroma devuelve menos de `top_k`;
3. combinación de resultados;
4. deduplicación común;
5. corte final `[:top_k]`.

## Adaptación de infraestructura sin cambio científico

El notebook antiguo usaba variables globales (`df_chunks`, `valid_source_chunk_pairs`, `MAX_EVIDENCE_CHARS`). La migración mantiene las mismas reglas, pero inyecta esos valores como argumentos desde `DraftWritingAgent`, usando `max_evidence_chars` de la política ya existente.

## Pruebas añadidas

`tests/v16/test_agent06_retrieval_restored_v16.py` verifica:

- fórmula de `per_source_k`;
- límite por cantidad real de chunks;
- descarte de `returned_source` incorrecto;
- score CSV normalizado;
- conservación de score cero;
- `MAX_EVIDENCE_CHARS` en Chroma y CSV;
- `valid_source_chunk_pairs`;
- mejor score por par;
- orden estable;
- secuencia Chroma → CSV → dedupe → top-k.

## Diferencias no abordadas

No se corrigió ni reinterpretó la observación secundaria de varias IDs dentro de una sola cita. Tampoco se amplió `top_k`, se añadió búsqueda numérica, reranking, retrieval multi-hop o sustitución automática de chunks.

## Estado contractual

El ciclo real anterior permanece sin cambios:

- `attempt_number = 2`;
- `execution_status = COMPLETED`;
- `quality_status = NEEDS_REVISION`;
- `requested_transition.action = HALT_STAGE`;
- `published_draft = false`.

La candidata no crea ni simula un intento contractual 3.

## Corrida diagnóstica real

Se incluye `run_agent06_diagnostic_rag_trace.py` para repetir la corrida aislada contra el corpus real después de instalar la candidata. El contenedor de construcción no contiene el experimento real de Colab, por lo que no se declara aquí una selección real de S2 posterior a la restauración. El runner no usa `StateStore`, no construye `AgentResult` y escribe en `diagnostic_rag_trace_run/`.
