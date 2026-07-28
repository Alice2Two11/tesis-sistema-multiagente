# Agent 07 — LangChain AIMessage response normalization

## Cause

`VerificationAgent.verify_claim()` received the direct result of `llm.invoke(...)`. With
`ChatOpenAI`, that result is normally a LangChain `AIMessage`/`BaseMessage`, not a plain
`str`. The strict parser therefore treated the non-string object as empty and produced
`LLM_RESPONSE_EMPTY`, even though `AIMessage.content` contained non-empty JSON.

## Correction

A transport-boundary normalizer now:

1. accepts a plain JSON `str` unchanged;
2. accepts a `Mapping` unchanged as a copied `dict`;
3. detects message-like objects with `.content` and extracts that value;
4. then invokes the existing strict JSON parser and the existing schema/scientific
   validators without changing the rubric, verdict logic, evidence rules, retries, or risk
   computation.

`raw_attempts[].raw_text` now stores the normalized string/mapping rather than the
non-serializable message object.

## Directed tests

- string response;
- mapping response;
- `AIMessage(content='{"claim_id": ...}')`;
- truly empty message content;
- non-JSON message content;
- incomplete AIMessage JSON reaches schema validation instead of `LLM_RESPONSE_EMPTY`;
- S2_C1 with a simulated ChatOpenAI returning AIMessage reaches a validated scientific
  `SUPPORTED` judgment.

Result: **7 passed**.

## Verification suite

Result: **590 passed**.

The repository copy used for the suite required the already-existing notebook fixture at
`notebooks/07_agente_verificador_trazabilidad_LIMPIO.ipynb`; that notebook is unchanged and
is intentionally excluded from this patch.

## Isolation

No OpenAI call, network access, Chroma access, corpus read, experiment mutation, official
artifact write, correction application, 07C execution, or 08 execution occurred.
