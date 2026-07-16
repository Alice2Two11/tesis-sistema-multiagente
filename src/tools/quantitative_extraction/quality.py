from __future__ import annotations

def calculate_diagnostic_metrics(*, papers_processed, quantitative_rows, dataset_rows, technique_rows, error_rows):
    papers_with_quant=len({r["source_filename"] for r in quantitative_rows}); papers_with_dataset=len({r["source_filename"] for r in dataset_rows}); papers_with_technique=len({r["source_filename"] for r in technique_rows})
    confirmed=sum(r.get("verification_status")=="confirmed_in_source_chunk" for r in quantitative_rows); only_kb=sum(r.get("verification_status")=="found_only_in_kb_text" for r in quantitative_rows); not_confirmed=sum(r.get("verification_status")=="not_confirmed" for r in quantitative_rows)
    div=lambda a,b: (a/b if b else None)
    return {"paper_quantitative_coverage":div(papers_with_quant,papers_processed),"source_chunk_confirmation_rate":div(confirmed,len(quantitative_rows)),"unconfirmed_value_rate":div(not_confirmed,len(quantitative_rows)),"successful_extraction_rate":div(papers_processed-len(error_rows),papers_processed),"dataset_coverage":div(papers_with_dataset,papers_processed),"technique_coverage":div(papers_with_technique,papers_processed),"values_found_only_in_kb_rate":div(only_kb,len(quantitative_rows)),"counts":{"papers_processed":papers_processed,"quantitative_rows":len(quantitative_rows),"dataset_rows":len(dataset_rows),"technique_rows":len(technique_rows),"extraction_errors":len(error_rows),"confirmed_in_source_chunks":confirmed,"found_only_in_kb_text":only_kb,"not_confirmed":not_confirmed}}

def diagnostic_quality_status(metrics, *, fallback_used: bool, error_count:int):
    counts=metrics["counts"]
    if error_count:
        return "NEEDS_REVISION", ("INVALID_LLM_OUTPUT",)
    if counts["quantitative_rows"] == 0:
        return "APPROVED_WITH_WARNINGS", ("NO_QUANTITATIVE_DATA_OBSERVED",)
    if fallback_used and counts["confirmed_in_source_chunks"] == 0:
        return "NEEDS_MORE_EVIDENCE", ("SOURCE_CHUNK_EVIDENCE_INCOMPLETE",)
    if fallback_used:
        return "APPROVED_WITH_WARNINGS", ("ALL_CLEAN_CHUNKS_FALLBACK_USED",)
    return "APPROVED", ()
