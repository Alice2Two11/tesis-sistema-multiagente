"""Notebook and transactional adapter for Agent 07.

The adapter reuses the frozen PipelineState/StateStore transaction model. It
supports PREPARE, EXECUTE, COMMIT and RESUME without modifying the draft or
emitting EVALUATION_READY.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime, timezone
import json
from pathlib import Path
import os
import shutil
from typing import Any, Callable, Mapping

from src.adapters.agent06_verification_handoff import build_agent07_input_from_committed_agent06
from src.adapters.verification_runtime import (
    Agent07RuntimeInput, Agent07RuntimeResult, VerificationRuntimeDependencies,
    run_agent07_in_memory, validate_agent07_runtime_input_contract,
    validate_agent07_runtime_result_contract, validate_committed_agent06_output_contract,
)
from src.contracts.agent_input import ArtifactReference
from src.contracts.agent_result import (
    AgentResult, DecisionInfo, ExecutionStatus, QualityStatus,
    RequestedTransition, ToolUsage, TransitionAction,
)
from src.io.atomic_write import atomic_write_json, atomic_write_bytes
from src.state.fingerprints import build_stage_fingerprints, sha256_bytes, sha256_file
from src.state.state_store import ResumeResolution, StateStore

NOTEBOOK_PREPARATION_STATUSES = ("READY", "BLOCKED")
NOTEBOOK_EXECUTION_STATUSES = ("NOT_EXECUTED", "COMPLETED", "PARTIAL", "BLOCKED")
AGENT07_STAGE_NAME = "07_agente_verificador"
AGENT07_ARTIFACT_NAMES = (
    "provisional_verification_traceability_bundle.json",
    "multi_proposal_resolution_result.json",
    "agent07_runtime_report.json",
    "agent07_artifact_manifest.json",
)




def resolve_committed_agent06_output(*, store: StateStore, experiment_root: str | Path, stage_name: str = "06_agente_redactor", agent07_config: Mapping[str, Any] | None = None, policy_versions: Mapping[str, str] | None = None, schema_versions: Mapping[str, str] | None = None, experiment_paths: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Build the Agent 07 hand-off from the exact committed Agent 06 result."""
    return build_agent07_input_from_committed_agent06(
        store=store, stage_name=stage_name, agent07_config=agent07_config or {},
        policy_versions=policy_versions or {}, schema_versions=schema_versions or {},
        experiment_paths=experiment_paths or {"experiment_root": str(experiment_root)},
        outline_paper_mapping_path=Path(experiment_root) / "outputs" / "04_outline" / "outline_paper_mapping.csv",
    )


@dataclass(frozen=True, slots=True)
class Agent07NotebookRequest:
    configuration_source: Any
    committed_agent06_source: Any
    experiment_paths: Mapping[str, str]
    policy_versions: Mapping[str, str]
    schema_versions: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class Agent07NotebookPreparationResult:
    runtime_input: Agent07RuntimeInput | None
    dependencies: VerificationRuntimeDependencies | None
    configuration_errors: tuple[str, ...]
    input_contract_errors: tuple[str, ...]
    dependency_errors: tuple[str, ...]
    execution_errors: tuple[str, ...]
    runtime_result: Agent07RuntimeResult | None
    preparation_status: str
    execution_status: str
    official_artifacts_created: bool = False
    correction_applied: bool = False
    evaluation_ready_emitted: bool = False
    result_contract_valid: bool = False

    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True, slots=True)
class Agent07ManifestArtifact:
    artifact_name: str
    sha256: str
    size_bytes: int

    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True, slots=True)
class Agent07ArtifactManifest:
    stage: str
    decision_id: str
    attempt_number: int
    execution_fingerprint: str
    schema_versions: Mapping[str, str]
    source_draft_fingerprint: str
    artifacts: tuple[Agent07ManifestArtifact, ...]
    correction_applied: bool
    evaluation_ready_emitted: bool

    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True, slots=True)
class PreparedAgent07Execution:
    decision_id: str
    runtime_input: Agent07RuntimeInput
    input_fingerprints: Mapping[str, str]
    stage_fingerprints: Mapping[str, str]
    attempt_number: int = 1
    execution_fingerprint: str = ""


@dataclass(frozen=True, slots=True)
class ExecutedAgent07Execution:
    decision_id: str
    runtime_input: Agent07RuntimeInput
    runtime_result: Agent07RuntimeResult
    candidate_payloads: Mapping[str, bytes]
    staging_manifest_path: str
    agent_result: AgentResult
    persisted_result_path: str
    stage_fingerprints: Mapping[str, str]
    attempt_number: int = 1
    execution_fingerprint: str = ""


@dataclass(frozen=True, slots=True)
class Agent07ResumeResult:
    action: str
    committed_result: AgentResult | None
    executed: ExecutedAgent07Execution | None


RESUME_ACTIONS = (
    "COMMITTED", "EXECUTED_NOT_COMMITTED", "REEXECUTE", "NO_COMMIT",
    "FINGERPRINT_MISMATCH", "ARTIFACT_MISMATCH", "MANIFEST_INCOMPLETE",
)
SCIENTIFIC_ARTIFACT_NAMES = AGENT07_ARTIFACT_NAMES[:3]
MANIFEST_NAME = AGENT07_ARTIFACT_NAMES[3]
OPERATIONAL_AUDIT_NAME = "agent07_operational_audit.json"


def _safe_error_code(prefix: str, exc: Exception) -> str: return f"{prefix}:{type(exc).__name__}"


def validate_agent07_notebook_preparation_result_contract(value: Agent07NotebookPreparationResult | Mapping[str, Any], *, allow_unvalidated: bool=False) -> dict[str, Any]:
    payload = asdict(value) if isinstance(value, Agent07NotebookPreparationResult) else deepcopy(dict(value)) if isinstance(value, Mapping) else None
    if payload is None or set(payload) != {f.name for f in fields(Agent07NotebookPreparationResult)}: raise ValueError("AGENT07_NOTEBOOK_PREPARATION_SCHEMA_INVALID")
    if payload["preparation_status"] not in NOTEBOOK_PREPARATION_STATUSES or payload["execution_status"] not in NOTEBOOK_EXECUTION_STATUSES: raise ValueError("AGENT07_NOTEBOOK_STATUS_INVALID")
    error_fields = ("configuration_errors","input_contract_errors","dependency_errors","execution_errors")
    for name in error_fields:
        if not isinstance(payload[name], (tuple,list)) or any(not isinstance(x,str) or not x for x in payload[name]): raise ValueError("AGENT07_NOTEBOOK_ERRORS_INVALID")
    all_errors = sum((len(payload[name]) for name in error_fields), 0)
    if payload["preparation_status"] == "READY":
        if payload["runtime_input"] is None or payload["dependencies"] is None or all_errors: raise ValueError("AGENT07_NOTEBOOK_READY_COHERENCE_INVALID")
    elif all_errors == 0: raise ValueError("AGENT07_NOTEBOOK_BLOCKED_WITHOUT_CAUSE")
    if payload["runtime_result"] is not None:
        validate_agent07_runtime_result_contract(payload["runtime_result"])
        expected = payload["runtime_result"]["runtime_status"] if isinstance(payload["runtime_result"], Mapping) else payload["runtime_result"].runtime_status
        if payload["execution_status"] != expected: raise ValueError("AGENT07_NOTEBOOK_EXECUTION_STATUS_MISMATCH")
    elif payload["execution_status"] != "NOT_EXECUTED" and not payload["execution_errors"]: raise ValueError("AGENT07_NOTEBOOK_EXECUTION_RESULT_MISSING")
    if any(payload[name] is not False for name in ("official_artifacts_created","correction_applied","evaluation_ready_emitted")): raise ValueError("AGENT07_NOTEBOOK_ISOLATION_INVALID")
    if type(payload["result_contract_valid"]) is not bool or (not allow_unvalidated and payload["result_contract_valid"] is not True): raise ValueError("AGENT07_NOTEBOOK_VALIDITY_NOT_DERIVED")
    return payload


def create_agent07_notebook_preparation_result(**kwargs: Any) -> Agent07NotebookPreparationResult:
    if "result_contract_valid" in kwargs: raise TypeError("result_contract_valid is derived")
    provisional=Agent07NotebookPreparationResult(**kwargs,result_contract_valid=False)
    validate_agent07_notebook_preparation_result_contract(provisional,allow_unvalidated=True)
    final=Agent07NotebookPreparationResult(**kwargs,result_contract_valid=True)
    validate_agent07_notebook_preparation_result_contract(final); return final


def prepare_agent07_notebook_execution(request: Agent07NotebookRequest, *, configuration_loader: Callable[[Any], Mapping[str, Any]], committed_output_loader: Callable[[Any], Mapping[str, Any]], dependency_resolver: Callable[[Mapping[str, Any]], VerificationRuntimeDependencies]) -> Agent07NotebookPreparationResult:
    ce=[]; ie=[]; de=[]; config=None; committed=None; dependencies=None; runtime_input=None
    try: config=deepcopy(dict(configuration_loader(deepcopy(request.configuration_source))))
    except Exception as exc: ce.append(_safe_error_code("AGENT07_NOTEBOOK_CONFIGURATION_ERROR",exc))
    try: committed=deepcopy(dict(committed_output_loader(deepcopy(request.committed_agent06_source))))
    except Exception as exc: ie.append(_safe_error_code("AGENT07_NOTEBOOK_AGENT06_LOAD_ERROR",exc))
    if committed is not None:
        candidate=Agent07RuntimeInput(committed, config or {}, deepcopy(dict(request.policy_versions)), deepcopy(dict(request.schema_versions)), deepcopy(dict(request.experiment_paths)))
        try:
            validate_agent07_runtime_input_contract(candidate)
            if config is not None: runtime_input=candidate
        except Exception as exc: ie.append(_safe_error_code("AGENT07_NOTEBOOK_INPUT_CONTRACT_ERROR",exc))
    if config is not None:
        try:
            dependencies=dependency_resolver(deepcopy(config))
            if not isinstance(dependencies,VerificationRuntimeDependencies): raise TypeError
        except Exception as exc: de.append(_safe_error_code("AGENT07_NOTEBOOK_DEPENDENCY_ERROR",exc)); dependencies=None
    status="READY" if runtime_input is not None and dependencies is not None and not (ce or ie or de) else "BLOCKED"
    return create_agent07_notebook_preparation_result(runtime_input=runtime_input,dependencies=dependencies,configuration_errors=tuple(ce),input_contract_errors=tuple(ie),dependency_errors=tuple(de),execution_errors=(),runtime_result=None,preparation_status=status,execution_status="NOT_EXECUTED",official_artifacts_created=False,correction_applied=False,evaluation_ready_emitted=False)


def execute_agent07_notebook_in_memory(preparation: Agent07NotebookPreparationResult) -> Agent07NotebookPreparationResult:
    validate_agent07_notebook_preparation_result_contract(preparation)
    if preparation.preparation_status != "READY" or preparation.runtime_input is None or preparation.dependencies is None: return preparation
    try:
        result=run_agent07_in_memory(preparation.runtime_input,dependencies=preparation.dependencies); validate_agent07_runtime_result_contract(result)
        return create_agent07_notebook_preparation_result(runtime_input=preparation.runtime_input,dependencies=preparation.dependencies,configuration_errors=preparation.configuration_errors,input_contract_errors=preparation.input_contract_errors,dependency_errors=preparation.dependency_errors,execution_errors=(),runtime_result=result,preparation_status="READY",execution_status=result.runtime_status,official_artifacts_created=False,correction_applied=False,evaluation_ready_emitted=False)
    except Exception as exc:
        return create_agent07_notebook_preparation_result(runtime_input=preparation.runtime_input,dependencies=preparation.dependencies,configuration_errors=preparation.configuration_errors,input_contract_errors=preparation.input_contract_errors,dependency_errors=preparation.dependency_errors,execution_errors=(_safe_error_code("AGENT07_NOTEBOOK_RUNTIME_ERROR",exc),),runtime_result=None,preparation_status="BLOCKED",execution_status="NOT_EXECUTED",official_artifacts_created=False,correction_applied=False,evaluation_ready_emitted=False)


def _stage_fingerprints(runtime_input: Agent07RuntimeInput):
    valid=validate_agent07_runtime_input_contract(runtime_input)
    return build_stage_fingerprints(input_data=valid["committed_agent06_output"],config_data={"agent07_config":valid["agent07_config"],"policy_versions":valid["policy_versions"],"schema_versions":valid["schema_versions"]},dependencies_data={"source_draft_fingerprint":valid["committed_agent06_output"]["source_draft_fingerprint"],"artifact_identity":valid["committed_agent06_output"]["artifact_identity"]})


def _validate_sha(value: Any, code: str) -> str:
    if not isinstance(value, str) or len(value)!=64 or any(c not in "0123456789abcdef" for c in value): raise ValueError(code)
    return value


def validate_prepared_agent07_execution_contract(value: PreparedAgent07Execution) -> PreparedAgent07Execution:
    if not isinstance(value, PreparedAgent07Execution): raise ValueError("AGENT07_PREPARED_SCHEMA_INVALID")
    if not value.decision_id or value.attempt_number < 1: raise ValueError("AGENT07_PREPARED_IDENTITY_INVALID")
    validate_agent07_runtime_input_contract(value.runtime_input)
    required={"input","config","dependencies","composite"}
    if set(value.stage_fingerprints)!=required: raise ValueError("AGENT07_PREPARED_FINGERPRINTS_INVALID")
    for fp in value.stage_fingerprints.values(): _validate_sha(fp,"AGENT07_PREPARED_FINGERPRINT_INVALID")
    if value.execution_fingerprint != value.stage_fingerprints["composite"]: raise ValueError("AGENT07_PREPARED_EXECUTION_FINGERPRINT_MISMATCH")
    return value


def prepare_agent07_execution(*, store: StateStore, runtime_input: Agent07RuntimeInput) -> PreparedAgent07Execution:
    valid=validate_agent07_runtime_input_contract(runtime_input); fp=_stage_fingerprints(runtime_input)
    state=store.load(); attempt=state.stages.get(AGENT07_STAGE_NAME).attempts_used+1 if AGENT07_STAGE_NAME in state.stages else 1
    prepared=store.prepare_execution(target_stage=AGENT07_STAGE_NAME,intended_action="EXECUTE_AGENT07_VERIFICATION",attempt_number=attempt)
    result=PreparedAgent07Execution(prepared.decision_id,runtime_input,{"source_draft_fingerprint":valid["committed_agent06_output"]["source_draft_fingerprint"]},fp.to_dict(),attempt,fp.composite)
    return validate_prepared_agent07_execution_contract(result)


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n").encode("utf-8")


def _runtime_agent_result(runtime_result: Agent07RuntimeResult, refs: Mapping[str, ArtifactReference], *, attempt_number:int) -> AgentResult:
    now=datetime.now(timezone.utc).isoformat(); completed=runtime_result.runtime_status in {"COMPLETED","PARTIAL"}
    return AgentResult(execution_status=ExecutionStatus.COMPLETED if completed else ExecutionStatus.FAILED,quality_status=QualityStatus.APPROVED if runtime_result.runtime_status=="COMPLETED" else (QualityStatus.APPROVED_WITH_WARNINGS if runtime_result.runtime_status=="PARTIAL" else QualityStatus.NEEDS_REVISION),decision=DecisionInfo(code=f"AGENT07_{runtime_result.runtime_status}",rationale="Resultado terminal validado del runtime del Agente 07."),quality_metrics=dict(runtime_result.execution_metrics),warnings=(),failure_reason_codes=tuple(runtime_result.runtime_issue_codes),requested_transition=RequestedTransition(action=TransitionAction.ADVANCE if completed else TransitionAction.HALT_STAGE,target_stage=None,reason_code=f"AGENT07_{runtime_result.runtime_status}",requires_human_confirmation=runtime_result.runtime_status!="COMPLETED"),output_artifacts=refs,tool_usage=ToolUsage(retrieval_rounds=0,llm_calls=0,validation_calls=1),attempt_number=attempt_number,started_at=now,completed_at=now,error=None if completed else {"code":"AGENT07_RUNTIME_BLOCKED"})


def _manifest_for(prepared: PreparedAgent07Execution, payloads: Mapping[str, bytes]) -> Agent07ArtifactManifest:
    artifacts=tuple(Agent07ManifestArtifact(name,sha256_bytes(payloads[name]),len(payloads[name])) for name in SCIENTIFIC_ARTIFACT_NAMES)
    return Agent07ArtifactManifest(AGENT07_STAGE_NAME,prepared.decision_id,prepared.attempt_number,prepared.execution_fingerprint,dict(prepared.runtime_input.schema_versions),prepared.runtime_input.committed_agent06_output["source_draft_fingerprint"],artifacts,False,False)


def validate_agent07_artifact_manifest_contract(value: Agent07ArtifactManifest | Mapping[str,Any], *, artifact_bytes: Mapping[str,bytes] | None=None) -> dict[str,Any]:
    p=asdict(value) if isinstance(value,Agent07ArtifactManifest) else deepcopy(dict(value)) if isinstance(value,Mapping) else None
    expected={f.name for f in fields(Agent07ArtifactManifest)}
    if p is None or set(p)!=expected: raise ValueError("AGENT07_MANIFEST_SCHEMA_INVALID")
    if p["stage"]!=AGENT07_STAGE_NAME or not p["decision_id"] or type(p["attempt_number"]) is not int or p["attempt_number"]<1: raise ValueError("AGENT07_MANIFEST_IDENTITY_INVALID")
    _validate_sha(p["execution_fingerprint"],"AGENT07_MANIFEST_EXECUTION_FINGERPRINT_INVALID"); _validate_sha(p["source_draft_fingerprint"],"AGENT07_MANIFEST_SOURCE_FINGERPRINT_INVALID")
    if not isinstance(p["schema_versions"],Mapping) or not p["schema_versions"] or any(not str(k).strip() or not str(v).strip() for k,v in p["schema_versions"].items()): raise ValueError("AGENT07_MANIFEST_SCHEMA_VERSIONS_INVALID")
    if p["correction_applied"] is not False or p["evaluation_ready_emitted"] is not False: raise ValueError("AGENT07_MANIFEST_ISOLATION_INVALID")
    arts=p["artifacts"]
    if not isinstance(arts,(list,tuple)) or {a.get("artifact_name") for a in arts}!=set(SCIENTIFIC_ARTIFACT_NAMES): raise ValueError("AGENT07_MANIFEST_ARTIFACT_SET_INVALID")
    if len(arts)!=len(SCIENTIFIC_ARTIFACT_NAMES): raise ValueError("AGENT07_MANIFEST_ARTIFACT_DUPLICATE")
    for a in arts:
        if set(a)!={"artifact_name","sha256","size_bytes"}: raise ValueError("AGENT07_MANIFEST_ARTIFACT_SCHEMA_INVALID")
        _validate_sha(a["sha256"],"AGENT07_MANIFEST_ARTIFACT_HASH_INVALID")
        if type(a["size_bytes"]) is not int or a["size_bytes"]<0: raise ValueError("AGENT07_MANIFEST_ARTIFACT_SIZE_INVALID")
        if artifact_bytes is not None:
            data=artifact_bytes.get(a["artifact_name"])
            if data is None or sha256_bytes(data)!=a["sha256"] or len(data)!=a["size_bytes"]: raise ValueError("AGENT07_MANIFEST_ARTIFACT_CONTENT_MISMATCH")
    return p


def execute_prepared_agent07(*, store: StateStore, prepared: PreparedAgent07Execution, dependencies: VerificationRuntimeDependencies) -> ExecutedAgent07Execution:
    validate_prepared_agent07_execution_contract(prepared)
    runtime_result=run_agent07_in_memory(prepared.runtime_input,dependencies=dependencies); validate_agent07_runtime_result_contract(runtime_result)
    output_dir=Path(prepared.runtime_input.experiment_paths.get("agent07_output_dir",prepared.runtime_input.experiment_paths["root"]+"/07_verification"))
    if runtime_result.runtime_status=="BLOCKED" and runtime_result.provisional_bundle is None:
        payloads={"agent07_runtime_report.json":_json_bytes(runtime_result.to_dict()),OPERATIONAL_AUDIT_NAME:_json_bytes(runtime_result.blocked_runtime_audit_record)}
    else:
        payloads={SCIENTIFIC_ARTIFACT_NAMES[0]:_json_bytes(runtime_result.provisional_bundle),SCIENTIFIC_ARTIFACT_NAMES[1]:_json_bytes(runtime_result.multi_proposal_resolution_result),SCIENTIFIC_ARTIFACT_NAMES[2]:_json_bytes(runtime_result.to_dict())}
        manifest=_manifest_for(prepared,payloads); validate_agent07_artifact_manifest_contract(manifest,artifact_bytes=payloads)
        payloads[MANIFEST_NAME]=_json_bytes(manifest.to_dict())
    staging_dir=Path(prepared.runtime_input.experiment_paths.get("agent07_staging_dir",prepared.runtime_input.experiment_paths["root"]+"/.agent07_staging"))/prepared.decision_id
    staging_dir.mkdir(parents=True,exist_ok=True)
    for name,data in payloads.items(): atomic_write_bytes(staging_dir/name,data)
    staging_manifest=staging_dir/"staging_index.json"; atomic_write_json(staging_manifest,{"decision_id":prepared.decision_id,"attempt_number":prepared.attempt_number,"execution_fingerprint":prepared.execution_fingerprint,"payload_hashes":{k:sha256_bytes(v) for k,v in payloads.items()},"fingerprints":dict(prepared.stage_fingerprints)})
    refs={name:ArtifactReference(str(output_dir/name),sha256_bytes(data)) for name,data in payloads.items()}
    result=_runtime_agent_result(runtime_result,refs,attempt_number=prepared.attempt_number); persisted=store.persist_agent_result(prepared.decision_id,result)
    executed=ExecutedAgent07Execution(prepared.decision_id,prepared.runtime_input,runtime_result,payloads,str(staging_manifest),result,str(persisted),prepared.stage_fingerprints,prepared.attempt_number,prepared.execution_fingerprint)
    return validate_executed_agent07_execution_contract(executed)


def _expected_candidate_payload_names(runtime_result: Agent07RuntimeResult) -> set[str]:
    """Derive the staging payload contract from the terminal result shape.

    A BLOCKED result can be either an early operational block (audit-only) or
    a terminal scientific block that already produced a bundle and resolution.
    The latter remains a complete *candidate* set in staging, although it is
    not eligible for official COMMIT.
    """
    has_bundle = runtime_result.provisional_bundle is not None
    has_resolution = runtime_result.multi_proposal_resolution_result is not None
    if runtime_result.runtime_status in {"COMPLETED", "PARTIAL"}:
        return set(AGENT07_ARTIFACT_NAMES)
    if runtime_result.runtime_status == "BLOCKED" and not has_bundle and not has_resolution:
        return {"agent07_runtime_report.json", OPERATIONAL_AUDIT_NAME}
    if runtime_result.runtime_status == "BLOCKED" and has_bundle and has_resolution:
        return set(AGENT07_ARTIFACT_NAMES)
    raise ValueError("AGENT07_EXECUTED_RUNTIME_PAYLOAD_SHAPE_INVALID")


def validate_executed_agent07_execution_contract(value: ExecutedAgent07Execution) -> ExecutedAgent07Execution:
    if not isinstance(value,ExecutedAgent07Execution): raise ValueError("AGENT07_EXECUTED_SCHEMA_INVALID")
    if value.agent_result.attempt_number!=value.attempt_number or value.decision_id=="": raise ValueError("AGENT07_EXECUTED_IDENTITY_INVALID")
    validate_prepared_agent07_execution_contract(PreparedAgent07Execution(value.decision_id,value.runtime_input,{"source_draft_fingerprint":value.runtime_input.committed_agent06_output["source_draft_fingerprint"]},value.stage_fingerprints,value.attempt_number,value.execution_fingerprint))
    validate_agent07_runtime_result_contract(value.runtime_result)
    if not Path(value.staging_manifest_path).is_file() or not Path(value.persisted_result_path).is_file(): raise ValueError("AGENT07_EXECUTED_STAGING_INVALID")
    expected = _expected_candidate_payload_names(value.runtime_result)
    if set(value.candidate_payloads)!=expected: raise ValueError("AGENT07_EXECUTED_PAYLOAD_SET_INVALID")
    for name,data in value.candidate_payloads.items():
        if value.agent_result.output_artifacts[name].hash!=sha256_bytes(data): raise ValueError("AGENT07_EXECUTED_PAYLOAD_HASH_MISMATCH")
    if MANIFEST_NAME in value.candidate_payloads:
        validate_agent07_artifact_manifest_contract(json.loads(value.candidate_payloads[MANIFEST_NAME]),artifact_bytes={k:v for k,v in value.candidate_payloads.items() if k!=MANIFEST_NAME})
    return value


def _validate_execution_for_commit(executed: ExecutedAgent07Execution) -> None:
    if executed.runtime_result.runtime_status == "BLOCKED":
        validate_executed_agent07_execution_contract(executed)
        if executed.runtime_result.provisional_bundle is None:
            raise RuntimeError("AGENT07_OPERATIONAL_BLOCK_NOT_SCIENTIFIC_COMMITTABLE")
        raise RuntimeError("AGENT07_SCIENTIFIC_BLOCK_NOT_OFFICIAL_COMMITTABLE")
    if set(executed.candidate_payloads) != set(AGENT07_ARTIFACT_NAMES):
        raise RuntimeError("AGENT07_COMMIT_MANIFEST_INCOMPLETE")
    validate_executed_agent07_execution_contract(executed)


def _published_dir(executed: ExecutedAgent07Execution) -> Path:
    return Path(executed.runtime_input.experiment_paths.get("agent07_output_dir",executed.runtime_input.experiment_paths["root"]+"/07_verification"))


def commit_executed_agent07(*, store: StateStore, executed: ExecutedAgent07Execution, fail_after_writes: int | None=None):
    _validate_execution_for_commit(executed)
    output_dir=_published_dir(executed); parent=output_dir.parent; parent.mkdir(parents=True,exist_ok=True)
    release=parent/f".{output_dir.name}.{executed.decision_id}.publish"; shutil.rmtree(release,ignore_errors=True); release.mkdir(parents=True)
    written=0
    try:
        # Manifest is created in the release directory but validated and published as the final marker.
        for name in SCIENTIFIC_ARTIFACT_NAMES:
            atomic_write_bytes(release/name,executed.candidate_payloads[name]); written+=1
            if fail_after_writes is not None and written>=fail_after_writes: raise RuntimeError("AGENT07_COMMIT_INJECTED_WRITE_FAILURE")
        manifest_payload=json.loads(executed.candidate_payloads[MANIFEST_NAME]); validate_agent07_artifact_manifest_contract(manifest_payload,artifact_bytes={n:(release/n).read_bytes() for n in SCIENTIFIC_ARTIFACT_NAMES})
        atomic_write_bytes(release/MANIFEST_NAME,executed.candidate_payloads[MANIFEST_NAME]); written+=1
        if fail_after_writes is not None and written>=fail_after_writes: raise RuntimeError("AGENT07_COMMIT_INJECTED_WRITE_FAILURE")
        validate_agent07_artifact_manifest_contract(json.loads((release/MANIFEST_NAME).read_text()),artifact_bytes={n:(release/n).read_bytes() for n in SCIENTIFIC_ARTIFACT_NAMES})
        backup=parent/f".{output_dir.name}.{executed.decision_id}.backup"; shutil.rmtree(backup,ignore_errors=True)
        if output_dir.exists(): os.replace(output_dir,backup)
        try: os.replace(release,output_dir)
        except Exception:
            if backup.exists(): os.replace(backup,output_dir)
            raise
        shutil.rmtree(backup,ignore_errors=True)
        # references now point to definitive paths and are rechecked before the single state transition.
        for name,ref in executed.agent_result.output_artifacts.items():
            if not Path(ref.path).is_file() or sha256_file(ref.path)!=ref.hash: raise RuntimeError(f"AGENT07_COMMIT_FINGERPRINT_MISMATCH:{name}")
        validate_agent07_artifact_manifest_contract(json.loads((output_dir/MANIFEST_NAME).read_text()),artifact_bytes={n:(output_dir/n).read_bytes() for n in SCIENTIFIC_ARTIFACT_NAMES})
        return store.commit_execution(decision_id=executed.decision_id,result=executed.agent_result,stage_name=AGENT07_STAGE_NAME,fingerprints=executed.stage_fingerprints,observations={"correction_applied":False,"evaluation_ready_emitted":False})
    finally:
        shutil.rmtree(release,ignore_errors=True)


def _load_executed_from_staging(*, store: StateStore, runtime_input: Agent07RuntimeInput, decision_id: str) -> ExecutedAgent07Execution | None:
    result=store.find_persisted_agent_result(decision_id)
    staging_dir=Path(runtime_input.experiment_paths.get("agent07_staging_dir",runtime_input.experiment_paths["root"]+"/.agent07_staging"))/decision_id; index=staging_dir/"staging_index.json"
    if result is None or not index.is_file(): return None
    meta=json.loads(index.read_text()); payloads={p.name:p.read_bytes() for p in staging_dir.iterdir() if p.is_file() and p.name!="staging_index.json"}
    for name,h in meta.get("payload_hashes",{}).items():
        if name not in payloads or sha256_bytes(payloads[name])!=h: return None
    runtime_payload=json.loads(payloads["agent07_runtime_report.json"]); runtime_result=Agent07RuntimeResult(**runtime_payload); validate_agent07_runtime_result_contract(runtime_result)
    value=ExecutedAgent07Execution(decision_id,runtime_input,runtime_result,payloads,str(index),result,str(store._agent_result_path(decision_id)),meta["fingerprints"],meta["attempt_number"],meta["execution_fingerprint"])
    return validate_executed_agent07_execution_contract(value)


def validate_agent07_resume_result_contract(value: Agent07ResumeResult) -> Agent07ResumeResult:
    if not isinstance(value,Agent07ResumeResult) or value.action not in RESUME_ACTIONS: raise ValueError("AGENT07_RESUME_ACTION_INVALID")
    if value.action=="COMMITTED" and value.committed_result is None: raise ValueError("AGENT07_RESUME_COMMITTED_RESULT_MISSING")
    if value.action=="EXECUTED_NOT_COMMITTED" and value.executed is None: raise ValueError("AGENT07_RESUME_EXECUTED_RESULT_MISSING")
    return value


def _resume(action: str, committed=None, executed=None): return validate_agent07_resume_result_contract(Agent07ResumeResult(action,committed,executed))


def resume_agent07_execution(*, store: StateStore, runtime_input: Agent07RuntimeInput, dependencies: VerificationRuntimeDependencies | None=None) -> Agent07ResumeResult:
    state=store.load(); fp=_stage_fingerprints(runtime_input); output_dir=Path(runtime_input.experiment_paths.get("agent07_output_dir",runtime_input.experiment_paths["root"]+"/07_verification"))
    if state.pending_execution is not None:
        executed=_load_executed_from_staging(store=store,runtime_input=runtime_input,decision_id=state.pending_execution.decision_id)
        if executed is None: return _resume("REEXECUTE")
        # Partial definitive files without the final valid manifest are not a commit. Remove them and reuse staging.
        if output_dir.exists():
            try:
                manifest=output_dir/MANIFEST_NAME
                valid_manifest=manifest.is_file() and set(p.name for p in output_dir.iterdir() if p.is_file())==set(AGENT07_ARTIFACT_NAMES)
                if valid_manifest:
                    validate_agent07_artifact_manifest_contract(json.loads(manifest.read_text()),artifact_bytes={n:(output_dir/n).read_bytes() for n in SCIENTIFIC_ARTIFACT_NAMES})
                    # Crash recovery: publication finished but the single state transition did not.
                    committed = store.commit_execution(decision_id=executed.decision_id, result=executed.agent_result, stage_name=AGENT07_STAGE_NAME, fingerprints=executed.stage_fingerprints, observations={"correction_applied":False,"evaluation_ready_emitted":False})
                    return _resume("COMMITTED", committed=executed.agent_result)
                else: shutil.rmtree(output_dir)
            except Exception: shutil.rmtree(output_dir,ignore_errors=True)
        if executed.runtime_result.runtime_status == "BLOCKED":
            # A blocked runtime result is terminal for this attempt but is not a
            # reusable scientific execution. Record the failed attempt without
            # publishing its staging-only artifacts, clear pending_execution via
            # the existing StateStore COMMIT transition, and request a fresh
            # PREPARE with a new decision_id and incremented attempt number.
            failed_result = replace(executed.agent_result, output_artifacts={})
            store.commit_execution(
                decision_id=executed.decision_id,
                result=failed_result,
                stage_name=AGENT07_STAGE_NAME,
                fingerprints=executed.stage_fingerprints,
                observations={
                    "resume_disposition": "BLOCKED_ATTEMPT_REEXECUTE",
                    "scientific_result_reused": False,
                    "correction_applied": False,
                    "evaluation_ready_emitted": False,
                },
            )
            return _resume("REEXECUTE")
        return _resume("EXECUTED_NOT_COMMITTED",executed=executed)
    stage=state.stages.get(AGENT07_STAGE_NAME)
    if stage is None or stage.execution_status != ExecutionStatus.COMPLETED: return _resume("NO_COMMIT")
    if stage.fingerprints != fp: return _resume("FINGERPRINT_MISMATCH")
    if not output_dir.is_dir(): return _resume("ARTIFACT_MISMATCH")
    try:
        manifest=json.loads((output_dir/MANIFEST_NAME).read_text()); validate_agent07_artifact_manifest_contract(manifest,artifact_bytes={n:(output_dir/n).read_bytes() for n in SCIENTIFIC_ARTIFACT_NAMES})
    except FileNotFoundError: return _resume("MANIFEST_INCOMPLETE")
    except Exception: return _resume("ARTIFACT_MISMATCH")
    for name in AGENT07_ARTIFACT_NAMES:
        artifact=state.artifacts.get(name)
        if artifact is None or not Path(artifact.reference.path).is_file() or sha256_file(artifact.reference.path)!=artifact.reference.hash: return _resume("ARTIFACT_MISMATCH")
    for entry in reversed(state.decision_log):
        if entry.stage==AGENT07_STAGE_NAME: return _resume("COMMITTED",AgentResult.from_dict(entry.result))
    return _resume("MANIFEST_INCOMPLETE")
