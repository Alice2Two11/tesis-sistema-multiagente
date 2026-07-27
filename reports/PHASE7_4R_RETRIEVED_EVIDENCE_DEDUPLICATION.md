# Unicidad y deduplicación

Dentro de cada recuperación se exige unicidad simultánea de:

- `evidence_id`;
- `(source_filename, chunk_id)`.

Política:

- duplicado canónicamente idéntico: se conserva una sola instancia;
- duplicado conflictivo: se bloquea con `AGENT07_RUNTIME_INDEPENDENT_RAG_CANDIDATE_CONFLICT`.

La comparación canónica incluye identidad, `query_ids` y `text_fingerprint`.
