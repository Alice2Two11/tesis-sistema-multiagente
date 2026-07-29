# Drive notebook 08 change

Do not add the notebook to GitHub.

The existing cell titled `08 — VALIDAR 07C Y CARGAR EL TEXTO
EVALUATION_READY` must stop requiring 07C unconditionally. It should call
`resolve_agent08_upstream_input(...)`, then build the existing local variables
from `Agent08UpstreamInput`.

The evaluation manifest and final Markdown report must include:

```json
{
  "source_stage": "AGENT07",
  "reverification_performed": false,
  "reverification_reason": "NO_ACCEPTED_CORRECTIONS",
  "upstream_runtime_status": "PARTIAL",
  "claims_requiring_manual_review": 12
}
```

The report must list the 12 `manual_review_claim_ids` and retain their
`verdict`, `hallucination_risk`, `proposal_status`, and
`comparison_stage_availability`.

Do not call 07C for this experiment. Do not rename the Agent 06 draft as an
EVALUATION_READY artifact. The adapter's generated paths remain explicitly
provenanced as the unchanged draft.
