diff -ruN '--exclude=__pycache__' '--exclude=.pytest_cache' '--exclude=.coverage' /mnt/data/a07fix/pristine/tesis_completa/tesis_codigo/src/adapters/__init__.py /mnt/data/a07fix/tesis/tesis_completa/tesis_codigo/src/adapters/__init__.py
--- /mnt/data/a07fix/pristine/tesis_completa/tesis_codigo/src/adapters/__init__.py	2026-07-27 20:13:44.000000000 +0000
+++ /mnt/data/a07fix/tesis/tesis_completa/tesis_codigo/src/adapters/__init__.py	2026-07-28 14:15:55.236512430 +0000
@@ -34,3 +34,8 @@
     validate_agent07c_prepared_input_contract,
     validate_original_agent07c_input_artifacts,
 )
+
+from .claim_verification_context import (
+    build_claim_verification_context_from_agent06_handoff,
+    classify_claim_from_versioned_policy,
+)
diff -ruN '--exclude=__pycache__' '--exclude=.pytest_cache' '--exclude=.coverage' /mnt/data/a07fix/pristine/tesis_completa/tesis_codigo/src/adapters/agent06_verification_handoff.py /mnt/data/a07fix/tesis/tesis_completa/tesis_codigo/src/adapters/agent06_verification_handoff.py
--- /mnt/data/a07fix/pristine/tesis_completa/tesis_codigo/src/adapters/agent06_verification_handoff.py	2026-07-27 20:13:44.000000000 +0000
+++ /mnt/data/a07fix/tesis/tesis_completa/tesis_codigo/src/adapters/agent06_verification_handoff.py	2026-07-28 14:15:53.940512445 +0000
@@ -230,7 +230,7 @@
             if key in inventory: raise ValueError(f"AGENT07_AGENT06_CLAIM_ID_DUPLICATE:{sid}:{cid}")
             if cid in global_claim_ids: raise ValueError(f"AGENT07_AGENT06_GLOBAL_CLAIM_ID_DUPLICATE:{cid}")
             global_claim_ids.add(cid)
-            inventory[key]={"claim_id":cid,"section_id":sid,"claim_text":text,"inventory_position":index}
+            inventory[key]={"claim_id":cid,"section_id":sid,"claim_text":text,"inventory_position":index,"section_title":str(section_record.get("section_title") or "").strip(),"source_free_organizational_section":bool(section_record.get("source_free_organizational_section") is True or (isinstance(section_record.get("section_validation"),Mapping) and section_record.get("section_validation",{}).get("source_free_organizational_section") is True)),"supporting_citations":tuple(claim.get("supporting_citations",()) or ())}
     if not inventory: raise ValueError("AGENT07_AGENT06_NO_CLAIM_INVENTORY")
     evidence_claim_keys=set(raw_by_claim)
     unknown_evidence=sorted(evidence_claim_keys-set(inventory))
@@ -255,13 +255,13 @@
         cfp=fingerprint_text(text);sfp=fingerprint_text(section)
         evidence=tuple(sorted(raw_by_claim.get((sid,cid),{}).values(),key=lambda x:x["evidence_id"]))
         contexts.append({
-          "claim_id":cid,"section_id":sid,"original_claim_text":text,"section_text":section,
+          "claim_id":cid,"claim_id_origin":"inherited_agent06","section_id":sid,"section_title":item["section_title"],"original_claim_text":text,"section_text":section,"supporting_citations":item["supporting_citations"],"source_free_organizational_section":item["source_free_organizational_section"],
           "claim_span_in_section":{"coordinate_base":"SECTION_TEXT","coordinate_system":"PYTHON_CODEPOINT_OFFSETS","base_text_fingerprint":sfp,"start":start,"end":end,"text":text},
           "claim_fingerprint":cfp,"section_fingerprint":sfp,"eligible_evidence":evidence,
           "authorized_source_filenames":tuple(sorted(allowed_by_section.get(sid,set()))),
           "source_draft_fingerprint":source_draft_fingerprint,
           "numeric_risk":numeric.get((sid,cid)),"numeric_risk_status":"EVALUATED" if (sid,cid) in numeric else "NOT_AVAILABLE",
-          "field_provenance":{"claim_id":"state_of_art_draft.json:sections[].claims","section_id":"state_of_art_draft.json:sections[].section_id","original_claim_text":"state_of_art_draft.json:sections[].claims","section_text":"draft_sections.csv|state_of_art_draft.json","claim_span_in_section":"explicit artifact coordinates|unique exact location","eligible_evidence":"draft_claim_evidence.csv|draft_rag_evidence.csv + outline_paper_mapping.csv authorization","authorized_source_filenames":"outline_paper_mapping.csv","numeric_risk":"numeric_hallucination_check.csv" if (sid,cid) in numeric else "ABSENT","source_draft_fingerprint":"draft_generation_manifest.json|canonical draft fingerprint"},
+          "field_provenance":{"claim_id":"state_of_art_draft.json:sections[].claims","claim_id_origin":"committed Agent06 inventory","section_id":"state_of_art_draft.json:sections[].section_id","section_title":"state_of_art_draft.json:sections[].section_title","original_claim_text":"state_of_art_draft.json:sections[].claims","supporting_citations":"state_of_art_draft.json:sections[].claims[].supporting_citations","source_free_organizational_section":"state_of_art_draft.json:section_validation","section_text":"draft_sections.csv|state_of_art_draft.json","claim_span_in_section":"explicit artifact coordinates|unique exact location","eligible_evidence":"draft_claim_evidence.csv|draft_rag_evidence.csv + outline_paper_mapping.csv authorization","authorized_source_filenames":"outline_paper_mapping.csv","numeric_risk":"numeric_hallucination_check.csv" if (sid,cid) in numeric else "ABSENT","source_draft_fingerprint":"draft_generation_manifest.json|canonical draft fingerprint"},
         })
     if not contexts: raise ValueError("AGENT07_AGENT06_NO_CLAIM_CONTEXTS")
     handoff={"commit_status":"COMMITTED","run_id":state.identity.run_id,"experiment_id":state.identity.experiment_id,"artifact_identity":str(manifest.get("artifact_identity") or agent06_decision),"schema_version":state.identity.schema_version,"source_draft_fingerprint":source_draft_fingerprint,"agent06_manifest_source_draft_fingerprint":str(declared) if declared else None,"claim_verification_contexts":tuple(contexts),"expected_claim_ids":tuple(cid for _,cid in sorted(inventory)),"claim_inventory_fingerprint":_sha256_json(tuple(inventory[k] for k in sorted(inventory))),"agent06_decision_id":agent06_decision,"outline_mapping_fingerprint":sha256_file(mapping_path),"integration_metadata":{"agent07_config_fingerprint":_sha256_json(agent07_config),"policy_versions":dict(policy_versions),"schema_versions":dict(schema_versions),"experiment_paths":dict(experiment_paths)}}
diff -ruN '--exclude=__pycache__' '--exclude=.pytest_cache' '--exclude=.coverage' /mnt/data/a07fix/pristine/tesis_completa/tesis_codigo/src/adapters/claim_verification_context.py /mnt/data/a07fix/tesis/tesis_completa/tesis_codigo/src/adapters/claim_verification_context.py
--- /mnt/data/a07fix/pristine/tesis_completa/tesis_codigo/src/adapters/claim_verification_context.py	1970-01-01 00:00:00.000000000 +0000
+++ /mnt/data/a07fix/tesis/tesis_completa/tesis_codigo/src/adapters/claim_verification_context.py	2026-07-28 14:15:19.992512827 +0000
@@ -0,0 +1,149 @@
+"""Deterministic integration adapter from Agent 06 handoff contexts to Agent 07 core.
+
+This module restores the versioned claim classification semantics from Agent 07
+Phase 1R and constructs the exact input contract consumed by VerificationAgent.
+It does not perform scientific judgment, retrieval, correction, or persistence.
+"""
+from __future__ import annotations
+
+from copy import deepcopy
+import re
+from typing import Any, Mapping, Sequence
+
+from src.config.verification_policy_config import get_verification_input_policy
+from src.tools.verification.corrections import fingerprint_text
+from src.tools.verification.validation import validate_claim_verification_context
+
+_SPACE_RE = re.compile(r"\s+")
+_NUMBER_RE = re.compile(r"(?<!\w)[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)\s*%?")
+_COMPARATIVE_RE = re.compile(r"\b(?:outperform(?:s|ed)?|better|worse|higher|lower|more accurate|less accurate|compared with|compared to|versus|vs\.?|superior|inferior|supera(?:n|ron)?|mejor(?:a|ó|aron)?|peor|mayor(?:es)?|menor(?:es)?|más precis[oa]s?|menos precis[oa]s?|comparad[oa]s? con|frente a)\b", re.I)
+_METHOD_RE = re.compile(r"\b(?:method|model|algorithm|architecture|training|dataset|feature|hyperparameter|evaluation protocol|cross-validation|método|metodo|modelo|algoritmo|arquitectura|entrenamiento|conjunto de datos|dataset|característica|caracteristica|hiperparámetro|hiperparametro|protocolo de evaluación|protocolo de evaluacion|validación cruzada|validacion cruzada)\b", re.I)
+_ATTRIBUTION_RE = re.compile(r"\b(?:proposed by|introduced by|developed by|according to|the authors|et al\.|propuest[oa] por|introducid[oa] por|desarrollad[oa] por|según|segun|los autores|las autoras|de acuerdo con)\b", re.I)
+_INTERPRETIVE_RE = re.compile(r"\b(?:suggests?|indicates?|implies?|demonstrates?|shows that|may|could|likely|therefore|overall|sugiere(?:n)?|indica(?:n)?|implica(?:n)?|demuestra(?:n)?|muestra(?:n)? que|podría(?:n)?|podria(?:n)?|probablemente|por lo tanto|en general)\b", re.I)
+_TRANSITIONAL_RE = re.compile(r"^(?:however|moreover|in addition|therefore|consequently|the next section|this section|finally|in summary|sin embargo|además|ademas|por otra parte|por lo tanto|en consecuencia|la siguiente sección|la siguiente seccion|esta sección|esta seccion|finalmente|en resumen)\b", re.I)
+_ORGANIZATIONAL_RE = re.compile(r"\b(?:scope|organization of the review|structure of this section|purpose of this section|guide the reader|alcance|organización de la revisión|organizacion de la revision|estructura de esta sección|estructura de esta seccion|propósito de esta sección|proposito de esta seccion|guiar al lector)\b", re.I)
+
+
+def classify_claim_from_versioned_policy(claim_text: str, *, source_free_organizational_section: bool = False) -> str:
+    """Phase-1R bilingual deterministic classification, preserved verbatim in behavior."""
+    text = _SPACE_RE.sub(" ", str(claim_text or "").strip())
+    if not text:
+        raise ValueError("AGENT07_CONTEXT_ADAPTER_EMPTY_CLAIM_TEXT")
+    if source_free_organizational_section or _ORGANIZATIONAL_RE.search(text): return "ORGANIZATIONAL"
+    if _TRANSITIONAL_RE.search(text) and len(text.split()) <= 25: return "TRANSITIONAL"
+    if _NUMBER_RE.search(text): return "QUANTITATIVE"
+    if _COMPARATIVE_RE.search(text): return "COMPARATIVE"
+    if _ATTRIBUTION_RE.search(text): return "ATTRIBUTION"
+    if _METHOD_RE.search(text): return "METHODOLOGICAL"
+    if _INTERPRETIVE_RE.search(text): return "INTERPRETIVE"
+    return "SUBSTANTIVE_FACTUAL"
+
+
+def _evidence_text(row: Mapping[str, Any]) -> str:
+    for key in ("canonical_text", "contractual_text", "text"):
+        value = row.get(key)
+        if isinstance(value, str) and value.strip():
+            return value.strip()
+    raise ValueError("AGENT07_CONTEXT_ADAPTER_EVIDENCE_TEXT_MISSING")
+
+
+def _normalize_evidence(rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
+    normalized=[]; seen_ids={}; seen_pairs={}
+    for raw in rows:
+        if not isinstance(raw, Mapping): raise ValueError("AGENT07_CONTEXT_ADAPTER_EVIDENCE_ROW_INVALID")
+        row=deepcopy(dict(raw))
+        eid=str(row.get("evidence_id") or "").strip(); source=str(row.get("source_filename") or "").strip(); chunk=str(row.get("chunk_id") or "").strip()
+        if not eid or not source or not chunk: raise ValueError("AGENT07_CONTEXT_ADAPTER_EVIDENCE_IDENTITY_MISSING")
+        text=_evidence_text(row)
+        row.update({"evidence_id":eid,"source_filename":source,"chunk_id":chunk,"text":text,"canonical_text":text,"authorized_for_section":bool(row.get("authorized_for_section") is True)})
+        canonical=(source,chunk,row["authorized_for_section"],fingerprint_text(text))
+        if eid in seen_ids and seen_ids[eid] != canonical: raise ValueError("AGENT07_CONTEXT_ADAPTER_EVIDENCE_CONFLICT")
+        pair=(source,chunk)
+        if pair in seen_pairs and seen_pairs[pair] != (eid,canonical): raise ValueError("AGENT07_CONTEXT_ADAPTER_EVIDENCE_CONFLICT")
+        seen_ids[eid]=canonical; seen_pairs[pair]=(eid,canonical); normalized.append(row)
+    unique={str(r["evidence_id"]):r for r in normalized}
+    return tuple(unique[k] for k in sorted(unique))
+
+
+def _supporting_citations(handoff: Mapping[str, Any], evidence: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
+    raw=handoff.get("supporting_citations", ())
+    if raw and not isinstance(raw,(tuple,list)): raise ValueError("AGENT07_CONTEXT_ADAPTER_SUPPORTING_CITATIONS_INVALID")
+    by_pair={(str(e["source_filename"]),str(e["chunk_id"])):e for e in evidence}
+    result=[]
+    for item in raw or ():
+        if isinstance(item,Mapping):
+            source=str(item.get("source_filename") or "").strip(); chunk=str(item.get("chunk_id") or "").strip()
+        else:
+            match=re.fullmatch(r"\[?\s*([^|\]]+)\s*\|\s*([^\]]+)\s*\]?",str(item).strip())
+            if not match: raise ValueError("AGENT07_CONTEXT_ADAPTER_SUPPORTING_CITATION_UNRESOLVED")
+            source,chunk=match.group(1).strip(),match.group(2).strip()
+        if not source or not chunk: raise ValueError("AGENT07_CONTEXT_ADAPTER_SUPPORTING_CITATION_UNRESOLVED")
+        row={"source_filename":source,"chunk_id":chunk}
+        if (source,chunk) in by_pair: row["evidence_id"]=str(by_pair[(source,chunk)]["evidence_id"])
+        result.append(row)
+    return tuple(result)
+
+
+def build_claim_verification_context_from_agent06_handoff(
+    handoff_context: Mapping[str, Any], *, verification_policy: Mapping[str, Any], attempt_number: int = 1,
+) -> dict[str, Any]:
+    """Build and validate the exact core context without mutating the handoff."""
+    if not isinstance(handoff_context,Mapping): raise ValueError("AGENT07_CONTEXT_ADAPTER_HANDOFF_NOT_MAPPING")
+    source=deepcopy(dict(handoff_context))
+    claim_id=str(source.get("claim_id") or "").strip(); section_id=str(source.get("section_id") or "").strip()
+    claim_text=str(source.get("original_claim_text") or "").strip()
+    section_title=str(source.get("section_title") or "").strip()
+    if not claim_id or not section_id or not claim_text: raise ValueError("AGENT07_CONTEXT_ADAPTER_IDENTITY_MISSING")
+    if not section_title: raise ValueError("AGENT07_CONTEXT_ADAPTER_SECTION_TITLE_MISSING")
+    if type(attempt_number) is not int or attempt_number < 1: raise ValueError("AGENT07_CONTEXT_ADAPTER_ATTEMPT_INVALID")
+    policy=get_verification_input_policy(verification_policy)
+    claim_type=source.get("claim_type")
+    classified=classify_claim_from_versioned_policy(claim_text,source_free_organizational_section=bool(source.get("source_free_organizational_section") is True))
+    if claim_type is None: claim_type=classified
+    elif claim_type != classified: raise ValueError("AGENT07_CONTEXT_ADAPTER_CLAIM_TYPE_CONFLICT")
+    intensity=policy["claim_verification_intensity"][claim_type]
+    evidence=_normalize_evidence(tuple(source.get("eligible_evidence",()) or ()))
+    inherited=tuple(e for e in evidence if str(e.get("retrieval_origin") or "") != "AGENT07_INDEPENDENT_RAG")
+    retrieved=tuple(e for e in evidence if str(e.get("retrieval_origin") or "") == "AGENT07_INDEPENDENT_RAG")
+    authorized_sources=tuple(source.get("authorized_source_filenames",()) or ())
+    if not authorized_sources or len(set(authorized_sources))!=len(authorized_sources): raise ValueError("AGENT07_CONTEXT_ADAPTER_AUTHORIZED_SOURCES_INVALID")
+    if any(e["authorized_for_section"] and e["source_filename"] not in set(authorized_sources) for e in evidence): raise ValueError("AGENT07_CONTEXT_ADAPTER_OUTLINE_AUTHORIZATION_MISMATCH")
+    allowed_pairs=tuple(sorted({(e["source_filename"],e["chunk_id"]) for e in evidence if e["authorized_for_section"]}))
+    numeric_status=str(source.get("numeric_risk_status") or "NOT_AVAILABLE")
+    numeric_risk=source.get("numeric_risk")
+    numeric_valid=not (claim_type=="QUANTITATIVE" and numeric_status=="EVALUATED" and str(numeric_risk).upper() in {"HIGH","CRITICAL","UNSUPPORTED","FAIL"})
+    deterministic={
+        "citation_valid": all((c["source_filename"],c["chunk_id"]) in set(allowed_pairs) for c in _supporting_citations(source,evidence)),
+        "document_identity_valid": all(bool(e["source_filename"] and e["chunk_id"]) for e in evidence),
+        "authorization_valid": all(e["authorized_for_section"] for e in evidence),
+        "numeric_pairs_valid": numeric_valid,
+        "deterministic_issue_codes": (),
+        "technical_blockers": (),
+        "numeric_risk": numeric_risk,
+        "numeric_risk_status": numeric_status,
+    }
+    retrieval_result={
+        "selected_candidates": retrieved,
+        "inherited_evidence": inherited,
+        "rounds_executed": int(source.get("agent07_independent_retrieval_rounds", 1 if retrieved else 0)),
+        "total_candidates_seen": len(retrieved), "total_unique_candidates_seen": len(retrieved),
+        "queries_executed_total": int(source.get("agent07_independent_retrieval_rounds", 1 if retrieved else 0)),
+        "new_unique_pairs_seen": len(retrieved), "queries": (), "discarded_candidates": (),
+        "retrieval_trace": (), "contradiction_signals": (), "technical_issue_codes": (),
+        "technical_status": "COMPLETED" if source.get("agent07_independent_retrieval_executed") else "NOT_ATTEMPTED",
+        "stop_reason": source.get("agent07_independent_retrieval_status", "NOT_ATTEMPTED"),
+        "queries_remaining": 0, "total_unique_candidates_retained": len(retrieved),
+        "new_unique_pairs_selected": len(retrieved), "structural_coverage_improved": bool(retrieved),
+        "structural_coverage_improved_this_delta": bool(retrieved), "retrieval_mode":"SECTION_SCOPED",
+    }
+    context={
+        "claim_id":claim_id,"claim_id_origin":str(source.get("claim_id_origin") or "inherited_agent06"),
+        "section_id":section_id,"section_title":section_title,"claim_text":claim_text,
+        "claim_type":claim_type,"verification_intensity":intensity,
+        "supporting_citations":_supporting_citations(source,evidence),
+        "inherited_evidence_assessment":{"evidence_rows":inherited,"additional_evidence_rows":(),"resolution_status":"RESOLVED" if inherited else "INHERITED_EVIDENCE_EMPTY"},
+        "retrieval_result":retrieval_result,"deterministic_validation":deterministic,
+        "allowed_source_pairs":allowed_pairs,"policy":policy,
+        "attempt_context":{"attempt_number":attempt_number,"remaining_retrieval_requests":int(policy["max_additional_retrieval_requests"]),"correction_localized":False},
+    }
+    return validate_claim_verification_context(context)
diff -ruN '--exclude=__pycache__' '--exclude=.pytest_cache' '--exclude=.coverage' /mnt/data/a07fix/pristine/tesis_completa/tesis_codigo/src/adapters/verification_runtime.py /mnt/data/a07fix/tesis/tesis_completa/tesis_codigo/src/adapters/verification_runtime.py
--- /mnt/data/a07fix/pristine/tesis_completa/tesis_codigo/src/adapters/verification_runtime.py	2026-07-27 20:13:44.000000000 +0000
+++ /mnt/data/a07fix/tesis/tesis_completa/tesis_codigo/src/adapters/verification_runtime.py	2026-07-28 14:20:42.492509196 +0000
@@ -14,6 +14,7 @@
 
 from src.agents.verification_agent import VerificationAgent
 from src.adapters.agent06_verification_handoff import (Agent07RetrieverBinding, validate_agent07_experiment_compatibility, validate_productive_retriever_binding)
+from src.adapters.claim_verification_context import build_claim_verification_context_from_agent06_handoff
 from src.tools.verification.corrections import propose_correction, fingerprint_text
 from src.tools.verification.resolution import (
     resolve_multiple_correction_proposals,
@@ -573,7 +574,7 @@
             if (str(existing.get("source_filename","")),str(existing.get("chunk_id","")),fingerprint_text(existing_text)) != (e["source_filename"],e["chunk_id"],fingerprint_text(e["canonical_text"])):
                 raise ValueError("AGENT07_RUNTIME_INDEPENDENT_RAG_CANDIDATE_CONFLICT")
         merged[e["evidence_id"]]=e
-    updated=deepcopy(dict(context)); updated["eligible_evidence"]=tuple(merged[k] for k in sorted(merged))
+    updated=deepcopy(dict(context)); updated["eligible_evidence"]=tuple(merged[k] for k in sorted(merged)); updated["agent07_independent_retrieval_executed"]=True; updated["agent07_independent_retrieval_rounds"]=rounds; updated["agent07_independent_retrieval_status"]="COMPLETED_WITH_RESULTS" if recovered else "COMPLETED_NO_RESULTS"
     snapshot_evidence=[]
     for e in updated["eligible_evidence"]:
         text=str(e.get("canonical_text",e.get("text",""))).strip()
@@ -585,6 +586,16 @@
     return updated, record
 
 
+
+def _sanitized_stage_error_code(exc: Exception) -> str:
+    """Preserve a safe contractual code, not only the Python exception class."""
+    import re
+    raw=str(exc).strip()
+    match=re.match(r"^([A-Z][A-Z0-9_]*(?::[A-Z0-9_,.-]+)*)", raw)
+    candidate=match.group(1) if match else ""
+    token=candidate if "_" in candidate else type(exc).__name__
+    return f"AGENT07_RUNTIME_STAGE_FAILURE:{token}"
+
 def _blocked_runtime_result(*, stage: str, claim_id: str | None, section_id: str | None, error_code: str, classification: str, schema_versions: Mapping[str, str], metrics: Mapping[str, int] | None = None) -> Agent07RuntimeResult:
     core = {"stage":stage,"claim_id":claim_id,"section_id":section_id,"error_code":error_code,"error_classification":classification}
     audit = BlockedRuntimeAuditRecord(**core, runtime_audit_fingerprint=_audit_hash(core)).to_dict()
@@ -608,7 +619,12 @@
             # A strict snapshot is mandatory for productive independent RAG records.
             # Legacy/in-memory fixtures without retrieval retain ID-only validation.
             verification_context_snapshots[(section_id,claim_id)] = snapshot
-            verification=_plain(agent.verify_claim(deepcopy(ctx))); vr.append({"section_id":section_id,"claim_verification_result":deepcopy(verification)})
+            if isinstance(agent, VerificationAgent):
+                policy_overrides=config.get("verification_policy", config.get("policy", {}))
+                core_ctx=build_claim_verification_context_from_agent06_handoff(ctx, verification_policy=policy_overrides, attempt_number=int(config.get("attempt_number",1)))
+            else:
+                core_ctx=deepcopy(ctx)
+            verification=_plain(agent.verify_claim(deepcopy(core_ctx))); vr.append({"section_id":section_id,"claim_verification_result":deepcopy(verification)})
             stage="CORRECTION_PROPOSAL"; cctx=dependencies.correction_context_factory(deepcopy(ctx),deepcopy(verification),deepcopy(config)); proposal=_plain(dependencies.proposal_runner(deepcopy(cctx),llm=dependencies.correction_llm)); proposals.append(deepcopy(proposal))
             if proposal.get("accepted_for_reverification") is not True: continue
             stage="REVERIFICATION_INPUT"; inp=_plain(dependencies.reverification_input_factory(deepcopy(ctx),deepcopy(verification),deepcopy(proposal),deepcopy(config))); ri.append(deepcopy(inp))
@@ -646,4 +662,4 @@
                 evidence_candidate_validation_claims += 1
         return create_agent07_runtime_result(provisional_bundle=bundle,multi_proposal_resolution_result=resolution,candidate_artifact_inventory=_candidate_inventory(bundle,resolution,validated["schema_versions"]),execution_metrics=_base_metrics(claims_processed=len(vr),independent_rag_claims=independent_rag_claims,independent_rag_claims_with_results=independent_rag_claims_with_results,independent_rag_claims_without_results=independent_rag_claims_without_results,independent_rag_claim_records=tuple(independent_rag_records),evidence_candidate_validation_claims=evidence_candidate_validation_claims,correction_proposals=len(proposals),reverification_inputs=len(ri),prechecks=len(pre),reverifications=len(rev),comparisons=len(comp)),runtime_warnings=(),runtime_issue_codes=(),runtime_error_records=(),blocked_runtime_audit_record=None,runtime_status=_resolution_to_runtime_status(resolution["resolution_status"]),correction_applied=False,official_artifacts_created=False,evaluation_ready_emitted=False)
     except Exception as exc:
-        return _blocked_runtime_result(stage=stage,claim_id=claim_id,section_id=section_id,error_code=f"AGENT07_RUNTIME_STAGE_FAILURE:{type(exc).__name__}",classification="DEPENDENCY" if stage in {"AGENT_INITIALIZATION","BUNDLE_BUILD","MULTI_PROPOSAL_RESOLUTION"} else "TECHNICAL",schema_versions=validated["schema_versions"],metrics=_base_metrics(claims_processed=len(vr),correction_proposals=len(proposals),reverification_inputs=len(ri),prechecks=len(pre),reverifications=len(rev),comparisons=len(comp)))
+        return _blocked_runtime_result(stage=stage,claim_id=claim_id,section_id=section_id,error_code=_sanitized_stage_error_code(exc),classification="DEPENDENCY" if stage in {"AGENT_INITIALIZATION","BUNDLE_BUILD","MULTI_PROPOSAL_RESOLUTION"} else "TECHNICAL",schema_versions=validated["schema_versions"],metrics=_base_metrics(claims_processed=len(vr),correction_proposals=len(proposals),reverification_inputs=len(ri),prechecks=len(pre),reverifications=len(rev),comparisons=len(comp)))
--- /dev/null	2026-07-28 14:08:04.876517726 +0000
+++ /mnt/data/a07fix/tesis/tesis_completa/tesis_codigo/tests/verification/test_agent07_real_context_adapter.py	2026-07-28 14:20:42.600509195 +0000
@@ -0,0 +1,93 @@
+from copy import deepcopy
+from pathlib import Path
+from types import SimpleNamespace
+
+from src.adapters.agent06_verification_handoff import build_agent07_input_from_committed_agent06
+from src.adapters.claim_verification_context import (
+    build_claim_verification_context_from_agent06_handoff,
+    classify_claim_from_versioned_policy,
+)
+from src.adapters.verification_runtime import Agent07RuntimeInput, VerificationRuntimeDependencies, run_agent07_in_memory
+from src.agents.verification_agent import VerificationAgent
+from src.contracts.agent_input import ArtifactReference
+from src.contracts.agent_result import AgentResult, DecisionInfo, ExecutionStatus, QualityStatus, RequestedTransition, ToolUsage, TransitionAction
+from src.state.pipeline_state import PipelineIdentity, PipelineState, StageState, ArtifactState, DecisionLogEntry
+from src.state.fingerprints import sha256_file
+from src.tools.verification.resolution import resolve_multiple_correction_proposals
+from src.tools.verification.validation import validate_claim_verification_context
+from test_multi_proposal_resolution_phase66 import bundle as real_bundle
+
+
+def _real_agent06_handoff(tmp_path):
+    src=Path(__file__).parents[1]/"fixtures"/"agent06_v17_e2e_snapshot"
+    names=("state_of_art_draft.json","state_of_art_draft.md","draft_sections.csv","draft_rag_evidence.csv","draft_claim_evidence.csv","numeric_hallucination_check.csv","draft_validation_report.json","draft_generation_manifest.json")
+    refs={}
+    for name in names:
+        target=tmp_path/name; target.write_bytes((src/name).read_bytes()); refs[name]=ArtifactReference(str(target),sha256_file(target))
+    result=AgentResult(ExecutionStatus.COMPLETED,QualityStatus.APPROVED,DecisionInfo("OK","ok"),{},(),RequestedTransition(TransitionAction.ADVANCE,"07","OK",False),refs,ToolUsage(),1,"2026-01-01","",completed_at="2026-01-01")
+    log=DecisionLogEntry("d06","2026-01-01","06_agente_redactor","06_agente_redactor",1,{}, {"code":"OK"},(),None,result.to_dict())
+    state=PipelineState(PipelineIdentity("exp_synthetic","run_synthetic","2026-01-01","2026-01-01","v1"),stages={"06_agente_redactor":StageState(execution_status=ExecutionStatus.COMPLETED)},artifacts={name:ArtifactState(ref,"2026-01-01") for name,ref in refs.items()},decision_log=(log,))
+    mapping=tmp_path/"outline_paper_mapping.csv"; mapping.write_bytes((src/"outline_paper_mapping.csv").read_bytes())
+    return build_agent07_input_from_committed_agent06(store=SimpleNamespace(load=lambda:state),stage_name="06_agente_redactor",agent07_config={},policy_versions={"verification":"v1"},schema_versions={"runtime":"v5"},experiment_paths={"root":str(tmp_path)},outline_paper_mapping_path=mapping)
+
+
+def test_s2_c1_real_handoff_adapts_and_validates_without_mutation(tmp_path):
+    handoff=_real_agent06_handoff(tmp_path)
+    source=next(x for x in handoff["claim_verification_contexts"] if x["claim_id"]=="S2_C1")
+    before=deepcopy(source)
+    adapted=build_claim_verification_context_from_agent06_handoff(source,verification_policy={})
+    assert validate_claim_verification_context(adapted)["claim_id"]=="S2_C1"
+    assert adapted["claim_text"]==source["original_claim_text"]
+    assert adapted["claim_type"]=="QUANTITATIVE"
+    assert adapted["verification_intensity"]=="STRICT"
+    assert source==before
+    assert all(pair[0] in source["authorized_source_filenames"] for pair in adapted["allowed_source_pairs"])
+
+
+def test_real_verification_agent_runtime_processes_complete_agent06_handoff(tmp_path):
+    handoff=_real_agent06_handoff(tmp_path)
+    original=deepcopy(handoff)
+    deps=VerificationRuntimeDependencies(
+        verification_agent_factory=VerificationAgent,
+        verification_llm=None,
+        correction_context_factory=lambda context, result, config:{"claim_id":context["claim_id"]},
+        reverification_input_factory=lambda *args:{},
+        proposal_runner=lambda context, *, llm:{"correction_id":"none-"+context["claim_id"],"accepted_for_reverification":False},
+        bundle_builder=lambda value:real_bundle(()),
+        resolution_runner=resolve_multiple_correction_proposals,
+    )
+    runtime_input=Agent07RuntimeInput(handoff,{"verification_policy":{}},{"verification":"v1"},{"runtime":"v5","provisional_bundle":"v4","multi_proposal_resolution":"v1"},{"root":str(tmp_path)})
+    result=run_agent07_in_memory(runtime_input,dependencies=deps)
+    assert result.runtime_status=="COMPLETED"
+    assert result.execution_metrics["claims_processed"]==len(handoff["expected_claim_ids"])
+    assert result.execution_metrics["claims_processed"]>=1
+    assert "CLAIM_VERIFICATION_INPUT_FIELDS_MISSING" not in str(result.to_dict())
+    assert handoff==original
+
+
+def test_claim_without_inherited_evidence_and_with_retrieved_evidence_are_valid(tmp_path):
+    handoff=_real_agent06_handoff(tmp_path)
+    source=deepcopy(handoff["claim_verification_contexts"][0])
+    source["eligible_evidence"]=()
+    empty=build_claim_verification_context_from_agent06_handoff(source,verification_policy={})
+    assert empty["inherited_evidence_assessment"]["evidence_rows"]==()
+    retrieved=deepcopy(source)
+    retrieved["eligible_evidence"]=({"evidence_id":"rag-new","source_filename":source["authorized_source_filenames"][0],"chunk_id":"new_chunk","text":"Texto recuperado contractualmente.","authorized_for_section":True,"retrieval_origin":"AGENT07_INDEPENDENT_RAG"},)
+    retrieved["agent07_independent_retrieval_executed"]=True
+    retrieved["agent07_independent_retrieval_rounds"]=1
+    retrieved["agent07_independent_retrieval_status"]="COMPLETED_WITH_RESULTS"
+    adapted=build_claim_verification_context_from_agent06_handoff(retrieved,verification_policy={})
+    assert adapted["retrieval_result"]["selected_candidates"][0]["evidence_id"]=="rag-new"
+    assert adapted["inherited_evidence_assessment"]["evidence_rows"]==()
+
+
+def test_versioned_claim_classification_covers_required_types():
+    cases={
+      "El sistema presenta resultados verificables.":"SUBSTANTIVE_FACTUAL",
+      "El sistema obtuvo 91% de precisión.":"QUANTITATIVE",
+      "El modelo A supera al modelo B.":"COMPARATIVE",
+      "El método usa validación cruzada.":"METHODOLOGICAL",
+      "Esta sección organiza el alcance de la revisión.":"ORGANIZATIONAL",
+      "Finalmente, la siguiente sección presenta los resultados.":"TRANSITIONAL",
+    }
+    for text,expected in cases.items(): assert classify_claim_from_versioned_policy(text)==expected
