from __future__ import annotations
from datetime import datetime,timezone
import json
from pathlib import Path
import pandas as pd
from src.contracts.agent_result import *
from src.contracts.agent_input import ArtifactReference
from src.state.fingerprints import sha256_file
from src.tools.draft_writing import *

class DraftWritingAgent:
    def __init__(self,runtime):self.runtime=runtime
    def _quant_context(self,section,bundle,limit):
        sources={str(p.get('source_filename','')).strip() for p in section.get('papers_to_use',[]) if isinstance(p,dict)}
        q=bundle['quantitative'];d=bundle['dataset_summary']
        q2=q[q['source_filename'].astype(str).isin(sources)].head(limit).to_dict('records') if not q.empty and 'source_filename' in q.columns else []
        d2=d[d['source_filename'].astype(str).isin(sources)].head(limit).to_dict('records') if not d.empty and 'source_filename' in d.columns else []
        return {'quantitative_results':q2,'dataset_technique_summary':d2}
    def execute(self,agent_input):
        start=datetime.now(timezone.utc).isoformat();llm_calls=0;retrieval_rounds=0;validation_calls=0
        out=Path(agent_input.agent_context.output_directory);raw_dir=out/'raw_section_outputs';raw_dir.mkdir(parents=True,exist_ok=True)
        try:
            bundle=validate_draft_dependencies(agent_input);policy=dict(agent_input.policy);manifest_path=out/'draft_generation_manifest.json';reuse=False
            required_reuse=('state_of_art_draft.json','state_of_art_draft.md','draft_sections.csv','draft_rag_evidence.csv','draft_quality_check.csv','draft_length_check.csv','draft_claim_evidence.csv','numeric_hallucination_check.csv','draft_validation_report.json','draft_generation_manifest.json')
            if manifest_path.exists() and not policy.get('force_rebuild',False):
                try:
                    old=json.loads(manifest_path.read_text());rep=json.loads((out/'draft_validation_report.json').read_text());reuse=old.get('fingerprint')==policy.get('current_fingerprint') and rep.get('validation_ok') is True and all((out/n).exists() for n in required_reuse)
                except Exception:reuse=False
            if reuse:
                validation=json.loads((out/'draft_validation_report.json').read_text());arts={n:ArtifactReference(str(out/n),sha256_file(out/n)) for n in NAMES if (out/n).exists()};arts['raw_section_outputs']=ArtifactReference(str(raw_dir),'DIRECTORY')
                return AgentResult(execution_status=ExecutionStatus.COMPLETED,quality_status=QualityStatus.APPROVED,decision=DecisionInfo(code='DRAFT_REUSED',rationale='Borrador válido reutilizado con fingerprint vigente.'),quality_metrics={'scientific':{},'technical':{'validation_ok':True,'reused':True}},warnings=(),failure_reason_codes=(),requested_transition=RequestedTransition(action=TransitionAction.ADVANCE,target_stage=None,reason_code='APPROVED',requires_human_confirmation=False),output_artifacts=arts,tool_usage=ToolUsage(retrieval_rounds=0,llm_calls=0,validation_calls=0),attempt_number=agent_input.attempt_number,started_at=start,completed_at=datetime.now(timezone.utc).isoformat())
            sections=bundle['outline'].get('sections') or []
            if not isinstance(sections,list) or not sections:raise ValueError('INVALID_OUTLINE_SCHEMA')
            policy['outline_sections']=sections
            policy['section_budgets']=assign_section_budgets(sections,policy.get('target_total_words',1000))
            generated=[];all_evidence=[];attempt_logs={}
            for section in sections:
                sid=str(section.get('section_id','')).strip();evidence=retrieve_section_evidence(section,self.runtime.collection,bundle['chunks'],int(policy.get('top_k_evidence_per_section',8)));retrieval_rounds += 1 if section.get('papers_to_use') else 0
                all_evidence.extend([{'section_id':sid,**r} for r in evidence])
                if not evidence:
                    if not section_allows_no_sources(section):raise ValueError(f'MISSING_SECTION_EVIDENCE:{sid}')
                    gen=build_source_free_organizational_section(section,policy.get('output_language','español'));attempt_logs[sid]=[{'attempt':0,'mode':'deterministic_source_free_organizational_section','validation':gen['section_validation']}];generated.append(gen);continue
                previous=[];logs=[];accepted=None
                for generation_attempt in range(1,int(policy.get('max_section_revision_attempts',2))+2):
                    prompt=build_section_prompt(section,evidence,self._quant_context(section,bundle,int(policy.get('max_quantitative_rows_per_section',12))),previous,policy)
                    raw=self.runtime.invoke(prompt);llm_calls+=1
                    write_raw_section_output(raw_dir,sid,generation_attempt,raw)
                    parsed=self.runtime.parse(raw);allowed={(r['source_filename'],r['chunk_id']) for r in evidence};norm=normalize_generated_section(parsed,allowed);norm['generation_attempt']=generation_attempt
                    val=validate_generated_section(norm,section,evidence);validation_calls+=1;norm['section_validation']=val;logs.append({'attempt':generation_attempt,'validation':val})
                    if val['validation_ok']:accepted=norm;break
                    previous=val['errors']+val['numeric_errors']
                attempt_logs[sid]=logs
                if accepted is None:raise ValueError(f'SECTION_VALIDATION_FAILED:{sid}')
                generated.append(accepted)
            evidence_map={}
            for row in all_evidence:evidence_map.setdefault(row['section_id'],[]).append({k:v for k,v in row.items() if k!='section_id'})
            _,quality_rows,section_rows,claim_rows,numeric_rows=build_draft_reports(generated,sections,evidence_map,policy)
            validation=validate_draft_global(generated,sections,evidence_map,policy)
            validation.update({'stage':'06_agente_redactor','experiment_id':agent_input.experiment_id,'validation_version':policy.get('validation_version'),'generation_attempts':attempt_logs});validation_calls+=1
            if not validation['validation_ok']:
                p=write_partial_validation(out,validation);arts={'draft_validation_report.json':ArtifactReference(str(p),sha256_file(p)),'raw_section_outputs':ArtifactReference(str(raw_dir),'DIRECTORY')};action=TransitionAction.RETRY if agent_input.attempt_number==1 else TransitionAction.HALT_STAGE
                return AgentResult(execution_status=ExecutionStatus.COMPLETED,quality_status=QualityStatus.NEEDS_REVISION,decision=DecisionInfo(code='DRAFT_VALIDATION_FAILED',rationale='El borrador no superó la validación global; no se publicaron salidas finales.'),quality_metrics={'scientific':{},'technical':{'validation_ok':False,'reused':False}},warnings=(AgentWarning(code='INVALID_DRAFT',severity=WarningSeverity.ERROR,blocking=True,message='La validación global fue negativa.'),),failure_reason_codes=('INVALID_DRAFT',),requested_transition=RequestedTransition(action=action,target_stage=None,reason_code='NEEDS_REVISION',requires_human_confirmation=False),output_artifacts=arts,tool_usage=ToolUsage(retrieval_rounds=retrieval_rounds,llm_calls=llm_calls,validation_calls=validation_calls),attempt_number=agent_input.attempt_number,started_at=start,completed_at=datetime.now(timezone.utc).isoformat())
            draft={'title':bundle['outline'].get('title','Borrador del estado del arte'),'topic':bundle['outline'].get('topic',''),'status':'draft_validated_for_verification','sections':generated,'generation_summary':{'experiment_id':agent_input.experiment_id,'section_count':len(generated),'ground_truth_used':False,'open_search_used':False,'citation_format':'[source_filename | chunk_id]'}}
            manifest={'stage':agent_input.stage_name,'experiment_id':agent_input.experiment_id,'run_id':agent_input.run_id,'attempt_number':agent_input.attempt_number,'fingerprint':policy.get('current_fingerprint'),'validation_ok':True,'safety_policy':{'uses_ground_truth':False,'uses_external_knowledge':False,'open_search_used':False},'counts':{'sections':len(generated),'llm_calls':llm_calls,'retrieval_rounds':retrieval_rounds},'versions':{'prompt':policy.get('prompt_version'),'rag':policy.get('rag_version'),'validation':policy.get('validation_version')}}
            arts=write_draft_artifacts(out,draft,all_evidence,validation,bundle['quantitative'],bundle['dataset_summary'],manifest,quality_rows,section_rows,claim_rows,numeric_rows)
            return AgentResult(execution_status=ExecutionStatus.COMPLETED,quality_status=QualityStatus.APPROVED,decision=DecisionInfo(code='DRAFT_APPROVED',rationale='Borrador generado por secciones y validado con evidencia restringida.'),quality_metrics={'scientific':{},'technical':{'validation_ok':True,'reused':False}},warnings=(),failure_reason_codes=(),requested_transition=RequestedTransition(action=TransitionAction.ADVANCE,target_stage=None,reason_code='APPROVED',requires_human_confirmation=False),output_artifacts=arts,tool_usage=ToolUsage(retrieval_rounds=retrieval_rounds,llm_calls=llm_calls,validation_calls=validation_calls),attempt_number=agent_input.attempt_number,started_at=start,completed_at=datetime.now(timezone.utc).isoformat())
        except Exception as exc:
            msg=str(exc);known=('DRAFT_INPUT_NOT_FOUND','OUTLINE_NOT_APPROVED','OUTLINE_MANIFEST_MISMATCH','GROUND_TRUTH_POLICY_VIOLATION','INVALID_DRAFT_KB_SCHEMA','INVALID_CHUNKS_SCHEMA','INVALID_QUANTITATIVE_CONTEXT','THEMATIC_NOT_APPROVED','OUTLINE_MANIFEST_NOT_APPROVED','THEMATIC_MANIFEST_NOT_APPROVED','OUTLINE_SOURCES_NOT_VALIDATED','OUTLINE_TITLES_NOT_VALIDATED','CHROMA_COLLECTION_MISMATCH','CHROMA_EMBEDDING_MODEL_MISMATCH','UNSAFE_CHROMA_INDEX','DUPLICATE_KB_SOURCE','DUPLICATE_CHUNK_ID','UNSAFE_CHUNKS','CHROMA_CHUNK_COUNT_MISMATCH','INVALID_OUTLINE_SECTION_IDS','INVALID_OUTLINE_MAPPING_SCHEMA','OUTLINE_MAPPING_INCONSISTENT','QUANTITATIVE_MANIFEST_MISMATCH','INVALID_OUTLINE_SCHEMA','MISSING_SECTION_EVIDENCE','SECTION_VALIDATION_FAILED','INVALID_LLM_OUTPUT','CREDENTIAL_NOT_FOUND','ATOMIC_WRITE_FAILED');code=next((x for x in known if x in msg),'RUNTIME_DEPENDENCY_FAILED')
            return AgentResult(execution_status=ExecutionStatus.FAILED,quality_status=QualityStatus.REJECTED,decision=DecisionInfo(code='DRAFT_WRITING_FAILED',rationale='Falló la ejecución del Agente Redactor.'),quality_metrics={'scientific':{},'technical':{}},warnings=(AgentWarning(code=code,severity=WarningSeverity.ERROR,blocking=True,message=msg),),failure_reason_codes=(code,),requested_transition=RequestedTransition(action=TransitionAction.HALT_STAGE,target_stage=None,reason_code=code,requires_human_confirmation=False),output_artifacts={},tool_usage=ToolUsage(retrieval_rounds=retrieval_rounds,llm_calls=llm_calls,validation_calls=validation_calls),attempt_number=agent_input.attempt_number,started_at=start,completed_at=datetime.now(timezone.utc).isoformat(),error={'type':type(exc).__name__,'message':msg,'stage':agent_input.stage_name})
