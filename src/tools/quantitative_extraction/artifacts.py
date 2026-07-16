from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping
import pandas as pd
from src.io.atomic_write import atomic_write_csv, atomic_write_json, atomic_write_jsonl, atomic_write_text
from src.config.quantitative_extraction_policy_config import ARTIFACT_FILENAMES

def artifact_paths(output_dir):
    root=Path(output_dir); return {name:root/name for name in ARTIFACT_FILENAMES}

def write_quantitative_artifacts(*, output_dir, results, raw_records, errors, quantitative_rows, dataset_rows, technique_rows, metrics, manifest_base):
    paths=artifact_paths(output_dir); written={}
    written[ARTIFACT_FILENAMES[0]]=atomic_write_json(paths[ARTIFACT_FILENAMES[0]],results)
    written[ARTIFACT_FILENAMES[1]]=atomic_write_jsonl(paths[ARTIFACT_FILENAMES[1]],raw_records)
    error_fields=("source_filename","error_type","error_message","created_at")
    written[ARTIFACT_FILENAMES[2]]=atomic_write_csv(paths[ARTIFACT_FILENAMES[2]],errors,fieldnames=error_fields)
    quant_fields=("source_filename","paper_title","model_or_method","metric","value","numeric_value","unit","dataset_or_case","evaluation_scope","data_resolution","condition","source_text_evidence","value_found_in_kb_text","value_found_in_source_chunk","source_chunk_scope","source_chunk_ids_checked","verification_status")
    written[ARTIFACT_FILENAMES[3]]=atomic_write_csv(paths[ARTIFACT_FILENAMES[3]],quantitative_rows,fieldnames=quant_fields)
    dataset_fields=("source_filename","paper_title","dataset_name","case_study","data_type","temporal_resolution","spatial_resolution","analysis_scope","source_text_evidence")
    written[ARTIFACT_FILENAMES[4]]=atomic_write_csv(paths[ARTIFACT_FILENAMES[4]],dataset_rows,fieldnames=dataset_fields)
    technique_fields=("source_filename","paper_title","technique_name","technique_family","role","source_text_evidence")
    written[ARTIFACT_FILENAMES[5]]=atomic_write_csv(paths[ARTIFACT_FILENAMES[5]],technique_rows,fieldnames=technique_fields)
    # deterministic summary
    summaries=[]
    sources=sorted({r["source_filename"] for r in dataset_rows+technique_rows})
    for source in sources:
        titles=[r["paper_title"] for r in dataset_rows+technique_rows if r["source_filename"]==source]
        summaries.append({"source_filename":source,"paper_title":titles[0] if titles else "","techniques":"; ".join(sorted({r["technique_name"] for r in technique_rows if r["source_filename"]==source and r["technique_name"]})),"datasets":"; ".join(sorted({r["dataset_name"] for r in dataset_rows if r["source_filename"]==source and r["dataset_name"]}))})
    written[ARTIFACT_FILENAMES[6]]=atomic_write_csv(paths[ARTIFACT_FILENAMES[6]],summaries,fieldnames=("source_filename","paper_title","techniques","datasets"))
    lines=["# Reporte de extracción cuantitativa estructurada","",f"Fecha: {datetime.now(timezone.utc).isoformat()}","",f"- Papers procesados: {metrics['counts']['papers_processed']}",f"- Filas cuantitativas: {metrics['counts']['quantitative_rows']}",f"- Confirmados en chunks: {metrics['counts']['confirmed_in_source_chunks']}",f"- Solo en KB: {metrics['counts']['found_only_in_kb_text']}",f"- No confirmados: {metrics['counts']['not_confirmed']}","","Los valores encontrados solo en la KB no se presentan como confirmados en el paper."]
    written[ARTIFACT_FILENAMES[7]]=atomic_write_text(paths[ARTIFACT_FILENAMES[7]],"\n".join(lines)+"\n")
    manifest=dict(manifest_base); manifest.update({"created_at":datetime.now(timezone.utc).isoformat(),"metrics":metrics,"safety_policy":{"uses_scientific_knowledge_base":True,"uses_ground_truth":False,"uses_external_knowledge":False,"uses_review_sections":False,"uses_bibliography":False},"outputs":{k:{"path":v.path,"sha256":v.hash} for k,v in written.items()}})
    written[ARTIFACT_FILENAMES[8]]=atomic_write_json(paths[ARTIFACT_FILENAMES[8]],manifest)
    return written,manifest
