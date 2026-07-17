# Auditoría de corrección — trazabilidad de fallo por sección, Agente 06 v1.6

## Causa raíz

La función `generate_validated_section` agotaba los `generation_attempt` y lanzaba `ValueError("SECTION_VALIDATION_FAILED:<section_id>")` antes de construir el reporte global. Como consecuencia, los `.txt` crudos permanecían, pero se perdían la validación de cada intento y `draft_validation_report.json`.

## Alcance de la corrección

No se modificaron el prompt, las reglas de validación, el RAG, el formato de citas, la cantidad de reintentos internos, las rutas, los doce artefactos de éxito ni las etapas 00–05.

Se añadieron únicamente:

1. escritura atómica de `<section_id>_attempt_<n>_validation.json` inmediatamente después de `validate_generated_section()`;
2. construcción y persistencia de un `draft_validation_report.json` parcial cuando una sección agota sus intentos;
3. traducción contractual del fallo científico a `COMPLETED / NEEDS_REVISION`, con `RETRY` en el intento contractual 1 y `HALT_STAGE` en el intento contractual 2;
4. conservación de los raw outputs y ausencia de publicación de `state_of_art_draft.json` y `state_of_art_draft.md`.

## Contenido de la validación por intento

Cada JSON incluye exclusivamente resultados derivados de la validación existente:

- `section_id`;
- `generation_attempt`;
- `validation_ok`;
- `validation_errors`;
- `invalid_citations`;
- `unsupported_claims`;
- `substantive_sentences_without_claim`;
- `substantive_sentences_without_citation`;
- `claim_sentence_mismatches`;
- `numeric_support_errors`;
- `word_count`;
- `citation_count`;
- referencia al raw output correspondiente.

## Reporte parcial

Cuando una sección falla después de todos sus intentos, el reporte parcial registra:

- `validation_ok = false`;
- `failed_section`;
- `section_attempts`;
- errores del último intento;
- rutas de validación por intento;
- directorio de raw outputs;
- `published_draft = false`.

## Prueba dirigida

La prueba `test_agent06_section_failure_trace_v16.py` reproduce tres intentos fallidos consecutivos y confirma:

- tres `.txt` crudos;
- tres JSON de validación;
- reporte parcial persistido;
- errores detallados disponibles;
- ausencia de borrador publicado;
- `COMPLETED / NEEDS_REVISION / RETRY` para `attempt_number=1`;
- `COMPLETED / NEEDS_REVISION / HALT_STAGE` para `attempt_number=2`.

## Suite completa

`python -m unittest discover -s tests -p "test_*.py"`

Resultado: `Ran 181 tests` — `OK`.
