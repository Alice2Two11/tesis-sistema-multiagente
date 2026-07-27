# Cierre contractual de evidencia recuperada

## Runtime Metrics V5

Cada `independent_rag_claim_record` conserva:

- identidad `claim_id` y `section_id`;
- estado y contadores de retrieval;
- binding del retriever;
- candidatos recuperados con `text_fingerprint`;
- `verification_context_snapshot` capturado después del retrieval y antes de `VerificationAgent.verify_claim(...)`.

El snapshot contiene, por evidencia:

- `evidence_id`;
- `source_filename`;
- `chunk_id`;
- `authorized_for_section`;
- `text_fingerprint`.

La salida terminal se compara contra este snapshot por identidad completa, no solo por ID.

## Evidencia autorizada para 07C

`authorized_terminal_evidence` es la unión de:

1. evidencia heredada y validada del handoff committed de Agente 06;
2. evidencia recuperada y validada por Agente 07, registrada en `independent_rag_claim_records`.

Una evidencia fuera de ambos universos bloquea el handoff.
