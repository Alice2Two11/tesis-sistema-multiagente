"""Deterministic integration adapter from Agent 06 handoff contexts to Agent 07 core.

This module restores the versioned claim classification semantics from Agent 07
Phase 1R and constructs the exact input contract consumed by VerificationAgent.
It does not perform scientific judgment, retrieval, correction, or persistence.
"""
from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Mapping, Sequence

from src.config.verification_policy_config import get_verification_input_policy
from src.tools.verification.corrections import fingerprint_text
from src.tools.verification.validation import validate_claim_verification_context

_SPACE_RE = re.compile(r"\s+")
_NUMBER_RE = re.compile(r"(?<!\w)[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)\s*%?")
_COMPARATIVE_RE = re.compile(r"\b(?:outperform(?:s|ed)?|better|worse|higher|lower|more accurate|less accurate|compared with|compared to|versus|vs\.?|superior|inferior|supera(?:n|ron)?|mejor(?:a|ó|aron)?|peor|mayor(?:es)?|menor(?:es)?|más precis[oa]s?|menos precis[oa]s?|comparad[oa]s? con|frente a)\b", re.I)
_METHOD_RE = re.compile(r"\b(?:method|model|algorithm|architecture|training|dataset|feature|hyperparameter|evaluation protocol|cross-validation|método|metodo|modelo|algoritmo|arquitectura|entrenamiento|conjunto de datos|dataset|característica|caracteristica|hiperparámetro|hiperparametro|protocolo de evaluación|protocolo de evaluacion|validación cruzada|validacion cruzada)\b", re.I)
_ATTRIBUTION_RE = re.compile(r"\b(?:proposed by|introduced by|developed by|according to|the authors|et al\.|propuest[oa] por|introducid[oa] por|desarrollad[oa] por|según|segun|los autores|las autoras|de acuerdo con)\b", re.I)
_INTERPRETIVE_RE = re.compile(r"\b(?:suggests?|indicates?|implies?|demonstrates?|shows that|may|could|likely|therefore|overall|sugiere(?:n)?|indica(?:n)?|implica(?:n)?|demuestra(?:n)?|muestra(?:n)? que|podría(?:n)?|podria(?:n)?|probablemente|por lo tanto|en general)\b", re.I)
_TRANSITIONAL_RE = re.compile(r"^(?:however|moreover|in addition|therefore|consequently|the next section|this section|finally|in summary|sin embargo|además|ademas|por otra parte|por lo tanto|en consecuencia|la siguiente sección|la siguiente seccion|esta sección|esta seccion|finalmente|en resumen)\b", re.I)
_ORGANIZATIONAL_RE = re.compile(r"\b(?:scope|organization of the review|structure of this section|purpose of this section|guide the reader|alcance|organización de la revisión|organizacion de la revision|estructura de esta sección|estructura de esta seccion|propósito de esta sección|proposito de esta seccion|guiar al lector)\b", re.I)


def classify_claim_from_versioned_policy(claim_text: str, *, source_free_organizational_section: bool = False) -> str:
    """Phase-1R bilingual deterministic classification, preserved verbatim in behavior."""
    text = _SPACE_RE.sub(" ", str(claim_text or "").strip())
    if not text:
        raise ValueError("AGENT07_CONTEXT_ADAPTER_EMPTY_CLAIM_TEXT")
    if source_free_organizational_section or _ORGANIZATIONAL_RE.search(text): return "ORGANIZATIONAL"
    if _TRANSITIONAL_RE.search(text) and len(text.split()) <= 25: return "TRANSITIONAL"
    if _NUMBER_RE.search(text): return "QUANTITATIVE"
    if _COMPARATIVE_RE.search(text): return "COMPARATIVE"
    if _ATTRIBUTION_RE.search(text): return "ATTRIBUTION"
    if _METHOD_RE.search(text): return "METHODOLOGICAL"
    if _INTERPRETIVE_RE.search(text): return "INTERPRETIVE"
    return "SUBSTANTIVE_FACTUAL"


def _evidence_text(row: Mapping[str, Any]) -> str:
    for key in ("canonical_text", "contractual_text", "text"):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    raise ValueError("AGENT07_CONTEXT_ADAPTER_EVIDENCE_TEXT_MISSING")


def _normalize_evidence(rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    normalized=[]; seen_ids={}; seen_pairs={}
    for raw in rows:
        if not isinstance(raw, Mapping): raise ValueError("AGENT07_CONTEXT_ADAPTER_EVIDENCE_ROW_INVALID")
        row=deepcopy(dict(raw))
        eid=str(row.get("evidence_id") or "").strip(); source=str(row.get("source_filename") or "").strip(); chunk=str(row.get("chunk_id") or "").strip()
        if not eid or not source or not chunk: raise ValueError("AGENT07_CONTEXT_ADAPTER_EVIDENCE_IDENTITY_MISSING")
        text=_evidence_text(row)
        row.update({"evidence_id":eid,"source_filename":source,"chunk_id":chunk,"text":text,"canonical_text":text,"authorized_for_section":bool(row.get("authorized_for_section") is True)})
        canonical=(source,chunk,row["authorized_for_section"],fingerprint_text(text))
        if eid in seen_ids and seen_ids[eid] != canonical: raise ValueError("AGENT07_CONTEXT_ADAPTER_EVIDENCE_CONFLICT")
        pair=(source,chunk)
        if pair in seen_pairs and seen_pairs[pair] != (eid,canonical): raise ValueError("AGENT07_CONTEXT_ADAPTER_EVIDENCE_CONFLICT")
        seen_ids[eid]=canonical; seen_pairs[pair]=(eid,canonical); normalized.append(row)
    unique={str(r["evidence_id"]):r for r in normalized}
    return tuple(unique[k] for k in sorted(unique))


def _supporting_citations(handoff: Mapping[str, Any], evidence: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    raw=handoff.get("supporting_citations", ())
    if raw and not isinstance(raw,(tuple,list)): raise ValueError("AGENT07_CONTEXT_ADAPTER_SUPPORTING_CITATIONS_INVALID")
    by_pair={(str(e["source_filename"]),str(e["chunk_id"])):e for e in evidence}
    result=[]
    for item in raw or ():
        if isinstance(item,Mapping):
            source=str(item.get("source_filename") or "").strip(); chunk=str(item.get("chunk_id") or "").strip()
        else:
            match=re.fullmatch(r"\[?\s*([^|\]]+)\s*\|\s*([^\]]+)\s*\]?",str(item).strip())
            if not match: raise ValueError("AGENT07_CONTEXT_ADAPTER_SUPPORTING_CITATION_UNRESOLVED")
            source,chunk=match.group(1).strip(),match.group(2).strip()
        if not source or not chunk: raise ValueError("AGENT07_CONTEXT_ADAPTER_SUPPORTING_CITATION_UNRESOLVED")
        row={"source_filename":source,"chunk_id":chunk}
        if (source,chunk) in by_pair: row["evidence_id"]=str(by_pair[(source,chunk)]["evidence_id"])
        result.append(row)
    return tuple(result)


def build_claim_verification_context_from_agent06_handoff(
    handoff_context: Mapping[str, Any], *, verification_policy: Mapping[str, Any], attempt_number: int = 1,
) -> dict[str, Any]:
    """Build and validate the exact core context without mutating the handoff."""
    if not isinstance(handoff_context,Mapping): raise ValueError("AGENT07_CONTEXT_ADAPTER_HANDOFF_NOT_MAPPING")
    source=deepcopy(dict(handoff_context))
    claim_id=str(source.get("claim_id") or "").strip(); section_id=str(source.get("section_id") or "").strip()
    claim_text=str(source.get("original_claim_text") or "").strip()
    section_title=str(source.get("section_title") or "").strip()
    if not claim_id or not section_id or not claim_text: raise ValueError("AGENT07_CONTEXT_ADAPTER_IDENTITY_MISSING")
    if not section_title: raise ValueError("AGENT07_CONTEXT_ADAPTER_SECTION_TITLE_MISSING")
    if type(attempt_number) is not int or attempt_number < 1: raise ValueError("AGENT07_CONTEXT_ADAPTER_ATTEMPT_INVALID")
    policy=get_verification_input_policy(verification_policy)
    claim_type=source.get("claim_type")
    classified=classify_claim_from_versioned_policy(claim_text,source_free_organizational_section=bool(source.get("source_free_organizational_section") is True))
    if claim_type is None: claim_type=classified
    elif claim_type != classified: raise ValueError("AGENT07_CONTEXT_ADAPTER_CLAIM_TYPE_CONFLICT")
    intensity=policy["claim_verification_intensity"][claim_type]
    evidence=_normalize_evidence(tuple(source.get("eligible_evidence",()) or ()))
    inherited=tuple(e for e in evidence if str(e.get("retrieval_origin") or "") != "AGENT07_INDEPENDENT_RAG")
    retrieved=tuple(e for e in evidence if str(e.get("retrieval_origin") or "") == "AGENT07_INDEPENDENT_RAG")
    authorized_sources=tuple(source.get("authorized_source_filenames",()) or ())
    if not authorized_sources or len(set(authorized_sources))!=len(authorized_sources): raise ValueError("AGENT07_CONTEXT_ADAPTER_AUTHORIZED_SOURCES_INVALID")
    if any(e["authorized_for_section"] and e["source_filename"] not in set(authorized_sources) for e in evidence): raise ValueError("AGENT07_CONTEXT_ADAPTER_OUTLINE_AUTHORIZATION_MISMATCH")
    allowed_pairs=tuple(sorted({(e["source_filename"],e["chunk_id"]) for e in evidence if e["authorized_for_section"]}))
    numeric_status=str(source.get("numeric_risk_status") or "NOT_AVAILABLE")
    numeric_risk=source.get("numeric_risk")
    numeric_valid=not (claim_type=="QUANTITATIVE" and numeric_status=="EVALUATED" and str(numeric_risk).upper() in {"HIGH","CRITICAL","UNSUPPORTED","FAIL"})
    deterministic={
        "citation_valid": all((c["source_filename"],c["chunk_id"]) in set(allowed_pairs) for c in _supporting_citations(source,evidence)),
        "document_identity_valid": all(bool(e["source_filename"] and e["chunk_id"]) for e in evidence),
        "authorization_valid": all(e["authorized_for_section"] for e in evidence),
        "numeric_pairs_valid": numeric_valid,
        "deterministic_issue_codes": (),
        "technical_blockers": (),
        "numeric_risk": numeric_risk,
        "numeric_risk_status": numeric_status,
    }
    retrieval_result={
        "selected_candidates": retrieved,
        "inherited_evidence": inherited,
        "rounds_executed": int(source.get("agent07_independent_retrieval_rounds", 1 if retrieved else 0)),
        "total_candidates_seen": len(retrieved), "total_unique_candidates_seen": len(retrieved),
        "queries_executed_total": int(source.get("agent07_independent_retrieval_rounds", 1 if retrieved else 0)),
        "new_unique_pairs_seen": len(retrieved), "queries": (), "discarded_candidates": (),
        "retrieval_trace": (), "contradiction_signals": (), "technical_issue_codes": (),
        "technical_status": "COMPLETED" if source.get("agent07_independent_retrieval_executed") else "NOT_ATTEMPTED",
        "stop_reason": source.get("agent07_independent_retrieval_status", "NOT_ATTEMPTED"),
        "queries_remaining": 0, "total_unique_candidates_retained": len(retrieved),
        "new_unique_pairs_selected": len(retrieved), "structural_coverage_improved": bool(retrieved),
        "structural_coverage_improved_this_delta": bool(retrieved), "retrieval_mode":"SECTION_SCOPED",
    }
    context={
        "claim_id":claim_id,"claim_id_origin":str(source.get("claim_id_origin") or "inherited_agent06"),
        "section_id":section_id,"section_title":section_title,"claim_text":claim_text,
        "claim_type":claim_type,"verification_intensity":intensity,
        "supporting_citations":_supporting_citations(source,evidence),
        "inherited_evidence_assessment":{"evidence_rows":inherited,"additional_evidence_rows":(),"resolution_status":"RESOLVED" if inherited else "INHERITED_EVIDENCE_EMPTY"},
        "retrieval_result":retrieval_result,"deterministic_validation":deterministic,
        "allowed_source_pairs":allowed_pairs,"policy":policy,
        "attempt_context":{"attempt_number":attempt_number,"remaining_retrieval_requests":int(policy["max_additional_retrieval_requests"]),"correction_localized":False},
    }
    return validate_claim_verification_context(context)
