# Implementación 03B v1.6 — reparación determinista de flattening

Estado: **CANDIDATA 03B V1.6 — REPARACIÓN DETERMINISTA DE FLATTENING**.

La corrección reutiliza `structured_quantitative_extraction.json` y `structured_quantitative_extraction_raw.jsonl`, no llama a OpenAI y no sobrescribe esos archivos. Normaliza diccionarios anidados, técnicas y datasets como strings, conserva `raw_path`/`raw_value`, registra formas no soportadas y valida consistencia entre candidatos crudos y tablas finales. No modifica el Agente 03 ni inicia el Agente 04.
