# Agent 07 → 07C/08: corrección de propagación de revisión manual

## Hallazgo reproducido con el commit real del experimento

El resultado committed del Agente 07 contiene:

- `runtime_status = PARTIAL`
- `aggregation_status = PARTIAL`
- `resolution_status = PARTIAL`
- `claims_verified = 25`
- `claims_eligible_for_07c = 0`
- `corrections_proposed = 0`
- `claim-level manual review = 12`
- `resolution-plan manual review = 0`

Los `partial_reason_codes` incluyen `PARTIAL_MANUAL_REVIEW_REQUIRED`.

La discrepancia se originaba porque el resumen del notebook y el handoff hacia 07C contaban únicamente `claim_resolution_plans[*].manual_review_required`. Esa colección representa decisiones de resolución de propuestas, no el estado científico terminal de todos los claims. Los 12 casos pendientes viven en `provisional_bundle.claim_traceability_rows[*].manual_review_required`.

## Riesgo corregido

Sin esta corrección, el sistema podía mostrar `claims_manual_review = 0` aun cuando el bundle contractual contenía 12 claims pendientes. Además, el handoff hacia 07C podía perder esos IDs y presentar un manifest incompleto.

No se modificó el Agente 08 para aceptar un artefacto parcial. El gate oficial permanece intacto: un artefacto con revisión manual pendiente no se presenta como `EVALUATION_READY`.

## Cambios

### `src/adapters/agent07c_handoff.py`

- Une la revisión manual de dos niveles:
  - claims terminales del bundle;
  - planes de resolución.
- Registra en `workflow_state`:
  - `pending_manual_review`;
  - `manual_review_claim_ids`;
  - conteos por nivel.
- Valida coherencia entre el manifest y `Agent07CPreparedInput.manual_review_claim_ids`.
- Emite `manual_review_queue.csv` como artefacto opcional únicamente cuando existen claims pendientes.

### `notebooks/07_agente_verificador_trazabilidad_LIMPIO.ipynb`

- Corrige el resumen post-COMMIT.
- Reporta por separado revisión manual científica y revisión manual de resolución.
- Muestra IDs y `partial_reason_codes`.
- Recomienda `HALT_FOR_MANUAL_REVIEW` cuando hay claims pendientes; de lo contrario, `RUN_07C`.

### Prueba nueva

`tests/verification/test_agent07_claim_manual_review_handoff.py` reproduce el caso exacto: un claim requiere revisión manual, pero su plan de resolución no contiene una bandera manual ni una corrección elegible.

## Validación

```text
621 passed
```

Suite ejecutada:

```bash
PYTHONPATH="$PWD:tests/verification" pytest -q tests/verification
```

## Consecuencia para el experimento actual

El Agente 08 no debe ejecutarse todavía. Primero deben resolverse los 12 claims listados en `manual_review_queue_agent07.csv`. Después, 07C puede ejecutar su ruta correspondiente y producir el contrato único `EVALUATION_READY` consumido por el 08.
