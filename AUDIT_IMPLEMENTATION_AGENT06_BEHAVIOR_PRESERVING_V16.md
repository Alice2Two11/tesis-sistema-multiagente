# Auditoría de implementación — Agente 06 v1.6

## Estado de la entrega

CANDIDATA PARA VALIDACIÓN REAL EN COLAB. La ejecución OpenAI/Chroma real no se realizó en el contenedor.

## A. Comportamiento científico original preservado

Se preserva la redacción sección por sección del notebook antiguo. Cada sección usa exclusivamente `papers_to_use`, recupera primero con Chroma restringido por `source_filename` y completa con fallback léxico CSV igualmente restringido. La evidencia se deduplica por `source_filename + chunk_id` y se filtra para excluir bloques no sustantivos.

Se mantiene el prompt por sección, el schema `section_id`, `section_title`, `draft_text`, `claims`, el formato de cita `[source_filename | chunk_id]`, la trazabilidad claim–cita–chunk, la validación literal de valores numéricos, la normalización determinista de posición de citas, la eliminación de contenido sustantivo sin evidencia declarada y la plantilla determinista para secciones organizativas sin fuentes.

Los reintentos internos por sección siguen siendo independientes del `attempt_number` contractual. No se añadió LLM crítico, juez, revisión global adicional, recuperación abierta, reranking, expansión de consulta, cobertura exhaustiva ni integración con el Agente 07.

## B. Infraestructura agéntica aplicada

Se añadió `DraftWritingAgent` usando los contratos comunes `AgentInput` y `AgentResult`, `PipelineState`, `StateStore`, fingerprints comunes, escritura atómica, credenciales centralizadas, PREPARE–EXECUTE–persist–COMMIT–RESUME, trazabilidad de artefactos, `execution_status`, `quality_status`, `failure_reason_codes`, `requested_transition`, `attempt_number` y `tool_usage`.

La etapa contractual es `06_agente_redactor`. Una salida aprobada solicita `ADVANCE` con `target_stage = null`. Una validación global negativa solicita `RETRY` en intento 1 y `HALT_STAGE` en intento 2. No existe intento 3 automático.

## C. Dependencias

Obligatorias: cuatro artefactos del Agente 05, tres artefactos del Agente 04, `chunks_clean_for_rag.csv`, `chroma_index_manifest.json` y la colección Chroma oficial. El contexto 03B es opcional como bloque de tres archivos; si está presente se filtra a filas con `value_found_in_source_chunk = true`.

## D. Artefactos

Se mantienen exactamente doce artefactos principales en `OUTPUTS_DIR/05_draft/`:

1. `state_of_art_draft.json`
2. `state_of_art_draft.md`
3. `draft_sections.csv`
4. `draft_rag_evidence.csv`
5. `draft_quality_check.csv`
6. `draft_length_check.csv`
7. `draft_claim_evidence.csv`
8. `numeric_hallucination_check.csv`
9. `draft_validation_report.json`
10. `quantitative_comparative_table_used.csv`
11. `dataset_technique_summary_used.csv`
12. `draft_generation_manifest.json`

`raw_section_outputs/` se conserva como colección auxiliar.

## E. Diferencias observables frente al notebook antiguo

No se identificaron cambios científicos intencionales. Las únicas diferencias son de envoltura agéntica, separación modular, persistencia transaccional, credenciales comunes, escritura atómica y notebook shell. El runtime no depende de `src.llm_utils.py`; usa `ChatOpenAI`, `HumanMessage`, `load_runtime_credential` y parser local, preservando modelo y temperatura configurados.

## F. Salidas inválidas

Si la validación global es negativa, no se publican `state_of_art_draft.json` ni `state_of_art_draft.md`. Se persisten `draft_validation_report.json`, `raw_section_outputs/` y `AgentResult`, con hashes de lo que realmente existe.

## G. Comparación final contra el notebook antiguo

Preservado: RAG restringido, Chroma primero, fallback CSV, filtros, top-k, deduplicación, exclusiones, contexto cuantitativo, prompt, schema, formato de cita, reintentos internos, normalización, validación numérica, plantilla sin fuentes, ensamblaje, bloqueo de borrador inválido, rutas, reutilización y artefactos.

No implementado por estar fuera de alcance: recuperación abierta, LLM crítico, LLM Judge, verificador factual 07, autor-año, bibliografía automática, métricas nuevas, cobertura exhaustiva, asignación de papers, nuevos artefactos u Orquestador final.

## H. Validación en contenedor

La suite acumulada se ejecuta con `python -m unittest discover -s tests -p "test_*.py"`. Las pruebas LLM y Chroma usan doubles controlados y no se presentan como validación real. `REAL_EXTERNAL_COLAB_AGENT06_RETURN_CODE = NOT_EXECUTED_IN_CONTAINER`.
