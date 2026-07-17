from __future__ import annotations
from dataclasses import dataclass
import json,re
@dataclass
class DraftWritingRuntime:
    invoke_fn: object
    collection: object
    def invoke(self,prompt):return self.invoke_fn(prompt)
    def parse(self,raw):
        text=getattr(raw,"content",raw)
        if isinstance(text,dict):return text
        text=str(text)
        candidates=[text]
        candidates += re.findall(r"```(?:json)?\s*(.*?)```",text,flags=re.S|re.I)
        start=text.find('{');end=text.rfind('}')
        if start>=0 and end>start:candidates.append(text[start:end+1])
        for c in candidates:
            try:
                obj=json.loads(c)
                if isinstance(obj,dict):return obj
            except Exception:pass
        raise ValueError('INVALID_LLM_OUTPUT')
def build_openai_draft_runtime(model,temperature,collection,*,project_dir=None,llm_factory=None,human_message_factory=None):
    from src.io.credentials import load_runtime_credential
    load_runtime_credential('OPENAI_API_KEY',project_dir=project_dir)
    if llm_factory is None:
        from langchain_openai import ChatOpenAI
        llm_factory=ChatOpenAI
    if human_message_factory is None:
        from langchain_core.messages import HumanMessage
        human_message_factory=HumanMessage
    llm=llm_factory(model=model,temperature=float(temperature))
    return DraftWritingRuntime(lambda prompt: llm.invoke([human_message_factory(content=prompt)]).content,collection)

from pathlib import Path
import json
from src.contracts.agent_input import AgentInput,AgentContext,ArtifactReference,ExecutionMode,PreviousAttemptSummary
from src.state.fingerprints import sha256_file,fingerprint_mapping
from src.config.draft_writing_policy_config import get_draft_writing_policy
from src.agents.draft_writing_agent import DraftWritingAgent

def resolve_pipeline_state_path(project_dir,experiment_id):
    root=Path(project_dir).resolve();exp=root/experiment_id;canonical=exp/'05_outputs'/'00_orchestrator_planner'/'pipeline_state.json'
    if canonical.is_file():return canonical
    candidates=list(exp.rglob('pipeline_state.json'))
    if len(candidates)==1:return candidates[0]
    if not candidates:raise FileNotFoundError(f'pipeline_state.json no encontrado en {exp}')
    raise RuntimeError(f'pipeline_state.json ambiguo: {candidates}')

def _collection_name(item):
    name=getattr(item,'name',None)
    return str(name if name is not None else item)

def _open_chroma_client(path,client_factory=None):
    if client_factory is None:
        import chromadb
        client_factory=chromadb.PersistentClient
    try:
        return client_factory(path=str(path))
    except TypeError:
        return client_factory(str(path))

def resolve_chroma_dir(experiment_dir,expected_collection,explicit_path=None,*,client_factory=None):
    exp=Path(experiment_dir).resolve()
    ordered=[]
    if explicit_path:
        ordered.append(Path(explicit_path).expanduser())
    ordered.append(exp/'04_chroma_index')
    ordered.extend(sorted({p.parent for p in exp.rglob('chroma.sqlite3')},key=lambda x:str(x)))
    candidates=[];seen=set()
    for item in ordered:
        path=item if item.is_absolute() else (exp/item)
        try:key=str(path.resolve())
        except Exception:key=str(path)
        if key not in seen:
            seen.add(key);candidates.append(Path(key))
    valid=[];observed={}
    for path in candidates:
        if not path.is_dir() or not (path/'chroma.sqlite3').is_file():
            continue
        try:
            client=_open_chroma_client(path,client_factory)
            names=sorted({_collection_name(x) for x in client.list_collections()})
        except Exception as exc:
            observed[str(path)]=[f'CLIENT_ERROR:{type(exc).__name__}']
            continue
        observed[str(path)]=names
        if expected_collection in names:
            valid.append(path.resolve())
    unique=[];seen_valid=set()
    for path in valid:
        key=str(path)
        if key not in seen_valid:
            seen_valid.add(key);unique.append(path)
    if len(unique)==1:
        return unique[0]
    if len(unique)>1:
        raise RuntimeError(f'CHROMA_DIR_AMBIGUOUS:{[str(x) for x in unique]}')
    raise FileNotFoundError(f'CHROMA_COLLECTION_NOT_FOUND:{expected_collection}; observed={observed}')

def load_draft_configuration(project_dir,attempt_number=1,*,chroma_client_factory=None):
    root=Path(project_dir).resolve();active=json.loads((root/'active_experiment.json').read_text(encoding='utf-8'));eid=active['active_experiment_id'];exp=root/eid;outputs=exp/'05_outputs';outline=outputs/'04_outline';thematic=outputs/'03_thematic_analysis';draft=outputs/'05_draft';rag=active.get('rag_policy',{});policy=get_draft_writing_policy(active.get('draft_generation_policy',{}));generation=active.get('generation_profile',{});policy.update({'experiment_profile':active.get('experiment_profile',{}),'topic_profile':active.get('topic_profile',{}),'generation_profile':generation,'rag_policy':rag,'output_language':generation.get('output_language','español académico'),'writing_mode':generation.get('writing_mode',''),'focus_mode':generation.get('focus_mode',''),'citation_style':generation.get('citation_style',''),'target_total_words':int(generation.get('target_total_words',1000)),'min_total_words':int(generation.get('min_total_words',650)),'max_total_words':int(generation.get('max_total_words',1400))})
    collection_name=active.get('chroma_collection_name','reference_papers_chunks')
    explicit=active.get('chroma_dir')
    chroma_dir=resolve_chroma_dir(exp,collection_name,explicit,client_factory=chroma_client_factory)
    paths={'outline_json':outline/'state_of_art_outline.json','outline_mapping':outline/'outline_paper_mapping.csv','outline_validation':outline/'outline_validation_report.json','outline_manifest':outline/'outline_generation_manifest.json','kb_final':thematic/'kb_final_for_thematic_analysis.csv','thematic_manifest':thematic/'thematic_analysis_manifest.json','thematic_validation':thematic/'thematic_validation_report.json','chunks_clean':Path(active.get('chunks_clean_path',exp/'03_chunks'/'chunks_clean_for_rag.csv')),'chroma_manifest':Path(active.get('chroma_manifest_path',outputs/'01_rag'/'chroma_index_manifest.json')),'quantitative_table':outputs/'02_scientific_knowledge_base'/'quantitative_comparative_table.csv','dataset_summary':outputs/'02_scientific_knowledge_base'/'dataset_technique_summary.csv','quantitative_manifest':outputs/'02_scientific_knowledge_base'/'quantitative_extraction_manifest.json'}
    return {'project_dir':root,'experiment_id':eid,'run_id':active.get('run_id',eid),'attempt_number':int(attempt_number),'model':active.get('openai_model','gpt-4o-mini'),'embedding_model_name':active.get('embedding_model_name','sentence-transformers/all-MiniLM-L6-v2'),'chroma_collection_name':collection_name,'chroma_dir':chroma_dir,'policy':policy,'output_dir':draft,'state_path':resolve_pipeline_state_path(root,eid),'paths':paths,'experiment_dir':exp}

def _previous_draft_attempt(cfg):
    if cfg['attempt_number']!=2:return None
    payload=json.loads(Path(cfg['state_path']).read_text(encoding='utf-8'));stage=payload.get('stages',{}).get('06_agente_redactor',{})
    if stage.get('requested_transition',{}).get('action')!='RETRY':raise RuntimeError('El intento 2 requiere una transición RETRY persistida.')
    return PreviousAttemptSummary(quality_status=stage.get('quality_status','NEEDS_REVISION'),failure_reason_codes=tuple(stage.get('failure_reason_codes',[])),blocking_warnings=tuple(str(x.get('code','')) for x in stage.get('warnings',[]) if x.get('blocking') and x.get('code')),previous_artifacts={})

def build_draft_agent_input(cfg):
    required=('outline_json','outline_mapping','outline_validation','outline_manifest','kb_final','thematic_manifest','thematic_validation','chunks_clean');deps={}
    for n in required:
        p=Path(cfg['paths'][n]);
        if not p.is_file():raise FileNotFoundError(f'{n} no existe: {p}')
        deps[n]=ArtifactReference(str(p),sha256_file(p))
    if Path(cfg['paths']['chroma_manifest']).is_file():
        deps['chroma_manifest']=ArtifactReference(str(cfg['paths']['chroma_manifest']),sha256_file(cfg['paths']['chroma_manifest']))
    optional=('quantitative_table','dataset_summary','quantitative_manifest');present=[n for n in optional if Path(cfg['paths'][n]).is_file()]
    if present and len(present)!=3:raise FileNotFoundError('INVALID_QUANTITATIVE_CONTEXT')
    for n in present:deps[n]=ArtifactReference(str(cfg['paths'][n]),sha256_file(cfg['paths'][n]))
    signature={'stage':'06_agente_redactor','stage_version':cfg['policy']['stage_version'],'experiment_id':cfg['experiment_id'],'experiment_dir':str(cfg['experiment_dir']),'openai_model':cfg['model'],'embedding_model_name':cfg['embedding_model_name'],'chroma_collection_name':cfg['chroma_collection_name'],'topic_profile':cfg['policy'].get('topic_profile',{}),'experiment_profile':cfg['policy'].get('experiment_profile',{}),'generation_profile':cfg['policy'].get('generation_profile',{}),'rag_policy':cfg['policy'].get('rag_policy',{}),'draft_generation_policy':{k:v for k,v in cfg['policy'].items() if k not in ('current_fingerprint',)},'paths':{k:v.path for k,v in deps.items()},'hashes':{k:v.hash for k,v in deps.items()},'prompt_version':cfg['policy']['prompt_version'],'rag_version':cfg['policy']['rag_version'],'validation_version':cfg['policy']['validation_version']}
    cfg['policy']['current_fingerprint']=fingerprint_mapping(signature)
    return AgentInput(experiment_id=cfg['experiment_id'],run_id=cfg['run_id'],stage_name='06_agente_redactor',attempt_number=cfg['attempt_number'],mode=ExecutionMode.FULL_RUN,agent_context=AgentContext(allowed_tools=('llm','chroma','csv_retrieval','atomic_write','draft_validation'),output_directory=str(cfg['output_dir']),runtime_resources={'model':cfg['model'],'chroma_collection_name':cfg['chroma_collection_name'],'embedding_model_name':cfg['embedding_model_name']}),dependencies=deps,policy=cfg['policy'],previous_attempt=_previous_draft_attempt(cfg))

def build_chroma_collection(cfg):
    import chromadb
    from chromadb.utils import embedding_functions
    client=chromadb.PersistentClient(path=str(cfg['chroma_dir']))
    emb=embedding_functions.SentenceTransformerEmbeddingFunction(model_name=cfg['embedding_model_name'])
    return client.get_collection(name=cfg['chroma_collection_name'],embedding_function=emb)

def build_real_draft_execution(project_dir,attempt_number=1,*,collection_factory=None,runtime_factory=None,chroma_client_factory=None):
    cfg=load_draft_configuration(project_dir,attempt_number,chroma_client_factory=chroma_client_factory);collection=(collection_factory or build_chroma_collection)(cfg);rf=runtime_factory or build_openai_draft_runtime;runtime=rf(cfg['model'],cfg['policy']['temperature'],collection,project_dir=cfg['project_dir']);return DraftWritingAgent(runtime),build_draft_agent_input(cfg),cfg
