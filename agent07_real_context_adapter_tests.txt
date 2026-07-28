# Corrección productiva 06 → 07 → VerificationAgent

## Defecto
`run_agent07_in_memory` enviaba el contexto de handoff del Agente 06 directamente a `VerificationAgent.verify_claim`. Ese mapping no implementaba `ClaimVerificationContext` y fallaba antes de procesar S2_C1.

## Corrección
Se añadió `build_claim_verification_context_from_agent06_handoff`, que restaura la clasificación determinista bilingüe versionada de la Fase 1R, deriva la intensidad desde `verification_policy`, separa evidencia heredada y recuperada, construye los campos deterministas y valida el resultado con `validate_claim_verification_context` antes de invocar el agente real.

El handoff de 06 conserva ahora `section_title`, `supporting_citations`, `source_free_organizational_section` y `claim_id_origin` desde artefactos committed. El contexto de handoff se copia y no se muta.

La evidencia incorporada por RAG independiente queda en `retrieval_result.selected_candidates`; la heredada queda en `inherited_evidence_assessment.evidence_rows`. `allowed_source_pairs` se deriva exclusivamente de evidencia autorizada por la sección.

Los errores contractuales sanitizados conservan el código estable, por ejemplo `AGENT07_RUNTIME_STAGE_FAILURE:CLAIM_VERIFICATION_INPUT_FIELDS_MISSING`, sin incluir prompts ni texto arbitrario.

## Prueba real sin OpenAI
La prueba `test_agent07_real_context_adapter.py` usa el snapshot end-to-end real de Agente 06, construye el handoff committed, adapta S2_C1, ejecuta `validate_claim_verification_context`, instancia `VerificationAgent` real y ejecuta `run_agent07_in_memory`. No usa un agente fake y no llama OpenAI.

Resultado dirigido: 4 passed.
Suite completa de `tests/verification`: 587 passed.

## Suite global del archivo adjunto
La colección global del repositorio adjunto no está verde por defectos preexistentes y archivos de notebooks 03–06 ausentes del ZIP: 965 passed, 26 failed, 28 errors, 128 subtests passed. Esos fallos están fuera de esta corrección y se conservaron sin modificar.
