# Auditoría de restauración — Agente 06 v1.6

## Estado

CANDIDATA PARA VALIDACIÓN REAL EN COLAB. No se ejecutaron OpenAI ni Chroma reales en el contenedor.

## Funciones restauradas

### `build_section_prompt`
Se migró nuevamente desde el notebook 06 antiguo, sin reformulación editorial. Incluye `target_words`, `minimum_words`, `maximum_words`, `writing_mode`, `focus_mode`, `citation_style`, idioma, evidencia, `ALLOWED_CITATIONS`, contexto cuantitativo y errores del intento anterior. Conserva el schema JSON y las citas `[source_filename | chunk_id]`.

### `assign_section_budgets`
Se preservaron las fórmulas originales:

- `base_target = max(80, int(TARGET_TOTAL_WORDS / section_count))`
- `minimum_words = max(50, int(base_target * 0.65))`
- `maximum_words = max(90, int(base_target * 1.40))`

### `build_draft_reports` y `validate_draft_global`
Se restauraron:

- `total_words`;
- `target_total_words`;
- `configured_min_total_words`;
- `effective_min_total_words`;
- `max_total_words`;
- `global_length_valid`;
- objetivos y límites por sección;
- `within_section_range` y secciones fuera del rango;
- citas inválidas;
- secciones sin citas válidas;
- oraciones sustantivas sin cita;
- errores claim–cita;
- errores cuantitativos;
- validación individual de secciones.

La fórmula de mínimo global efectivo se conservó:

`max(1, MIN_TOTAL_WORDS - source_free_count * max(0, int(TARGET_TOTAL_WORDS / section_count) - 40))`.

### `validate_draft_dependencies`
Se restauraron las comprobaciones observables de:

- identidad de experimento;
- `validation_ok` de 04 y 05;
- confirmación de fuentes y títulos del outline;
- seguridad y ausencia de Ground Truth/conocimiento externo;
- colección Chroma;
- modelo de embeddings;
- cantidad de chunks indexados;
- flags de Ground Truth, revisión, bibliografía y chunks excluidos;
- columnas obligatorias y duplicados;
- IDs de sección;
- coherencia exacta outline–mapping;
- bloque opcional 03B y sus columnas/safety policy;
- filtrado `value_found_in_source_chunk = true`.

### `draft_length_check.csv`
Se restauraron las columnas:

- `section_id`;
- `section_title`;
- `word_count`;
- `target_words`;
- `minimum_words`;
- `maximum_words`;
- `source_free_organizational_section`;
- `within_section_range`;
- `citation_count`;
- `claim_count`.

### Raw outputs
`raw_section_outputs/<section_id>_attempt_<n>.txt` conserva nombres y contenido, pero ahora usa `atomic_write_text`.

## Comparación con el notebook antiguo

Se preservaron RAG restringido, Chroma→CSV, filtros por fuente, deduplicación, formato de cita, normalización, validación literal, reintentos internos, doce artefactos, raw outputs, rutas y política contractual. No se añadieron métricas, prompts, retrieval, crítica o verificación científica nuevas.

## Pruebas nuevas

`tests/v16/test_agent06_validation_restored_v16.py` verifica por comportamiento:

- total global fuera de rango;
- sección fuera del presupuesto;
- densidad de citas insuficiente;
- sección sin citas válidas;
- errores claim–evidencia;
- errores numéricos globales;
- prompt con modos, estilo y presupuesto;
- colección Chroma incompatible;
- embedding incompatible;
- Ground Truth, revisión, bibliografía y chunks excluidos;
- incoherencia outline–mapping;
- escritura atómica de raw outputs.

## Alcance preservado

No se modificaron 00–05, contratos, estado, RAG restringido, formato de citas, reintentos, normalización, rutas, doce artefactos ni integración con 07. `REAL_EXTERNAL_COLAB_AGENT06_RETURN_CODE = NOT_EXECUTED_IN_CONTAINER`.
