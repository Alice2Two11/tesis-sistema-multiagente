# Agent 08 — dual upstream routing (07C or direct committed 07)

## Defect

The Drive notebook `08_evaluacion(7).ipynb` hard-codes the 07C-only contract:
`verified_state_of_art_EVALUATION_READY.*`, post-correction CSVs, a successful
07C manifest, and `pending_manual_review = false`.

That contract rejects the valid terminal case demonstrated by
`experimento_paper_02`:

- Agent 07 is committed with runtime/aggregation/resolution `PARTIAL`;
- 25 claims were verified;
- zero accepted corrections are eligible for 07C;
- 12 claims remain for scientific manual review;
- Agent 07 did not emit EVALUATION_READY and did not modify the draft.

Running 07C in that case would fabricate a reverification stage that had no
accepted correction to process.

## Productive change

`src/adapters/evaluation_upstream.py` introduces a strict upstream resolver.

### Path A — 07 → 07C → 08

A valid approved 07C manifest remains supported. The adapter reports:

- `source_stage = AGENT07C`
- `reverification_performed = true`
- `reverification_reason = ACCEPTED_CORRECTIONS_REVERIFIED`

### Path B — committed 07 → 08

The direct path is allowed only when all of the following are proven:

- Agent 07 manifest belongs to `07_agente_verificador`;
- runtime is `COMPLETED` or `PARTIAL`;
- provisional bundle and resolution exist;
- aggregation and resolution are evaluable;
- `eligible_for_07c = false`;
- accepted corrections and claims with accepted proposals are zero;
- claim coverage is complete;
- manual-review count equals the authoritative claim rows;
- `correction_applied = false`;
- `evaluation_ready_emitted = false`;
- the unchanged committed draft matches Agent 07's source draft fingerprint.

It reports exactly:

- `source_stage = AGENT07`
- `reverification_performed = false`
- `reverification_reason = NO_ACCEPTED_CORRECTIONS`
- `upstream_runtime_status = PARTIAL`
- `claims_requiring_manual_review = 12`

The compatibility traceability rows retain verdict, hallucination risk,
manual-review status, proposal status, and comparison-stage availability.
The 12 pending claims therefore remain visible in Agent 08 quality and
limitations reporting.

## Notebook 08 integration

The notebook remains in Drive and is intentionally excluded from the GitHub
patch. Replace its 07C-only input cell with a call to:

```python
from src.adapters.evaluation_upstream import resolve_agent08_upstream_input

upstream = resolve_agent08_upstream_input(
    agent07_directory=OUTPUTS_DIR / "06_verification_traceability",
    agent07c_directory=OUTPUTS_DIR / "06_verification_traceability",
    draft_json_path=OUTPUTS_DIR / "05_draft_v17_candidate" / "state_of_art_draft.json",
    draft_markdown_path=OUTPUTS_DIR / "05_draft_v17_candidate" / "state_of_art_draft.md",
)

source_stage = upstream.source_stage
reverification_performed = upstream.reverification_performed
reverification_reason = upstream.reverification_reason
upstream_runtime_status = upstream.upstream_runtime_status
claims_requiring_manual_review = upstream.claims_requiring_manual_review

evaluation_ready_result = load_json_file(
    Path(upstream.generated_state_of_art_json_path)
)
df_traceability = pd.DataFrame(upstream.traceability_rows)
df_recheck_report = pd.DataFrame(upstream.claim_report_rows)
df_numeric_recheck = pd.DataFrame(upstream.numeric_check_rows)
```

The productive notebook should resolve the committed Agent 06 draft path from
PipelineState/AgentResult rather than permanently hard-code the candidate
directory shown above. The snippet shows the adapter interface, not a new path
contract.

For direct Agent 07 input, generated section text is read from `draft_text`.
For Agent 07C input, it is read from `verified_text`. The notebook report and
manifest must copy the five routing fields from `upstream`.

## No fabricated 07C

The adapter does not create post-correction files, does not mark the text as
reverified, and does not convert pending reviews into accepted corrections.

## Tests

Directed tests: 6 passed.

Combined repository verification and evaluation suite: 627 passed.

The repository's bare `pytest -q` currently has a pre-existing duplicate
test-module basename at repository root and under `tests/verification`.
The scoped command used was:

```bash
PYTHONPATH="$PWD:tests/verification" pytest -q tests/verification tests/evaluation
```
