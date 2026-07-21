from __future__ import annotations

DEFAULT_DRAFT_WRITING_POLICY = {
    "stage_version": "06_AGENTIC_V16_BEHAVIOR_PRESERVING",
    "prompt_version": "legacy_notebook06_section_prompt_v1",
    "rag_version": "legacy_chroma_then_csv_restricted_v1",
    "validation_version": "legacy_notebook06_validation_v1",
    "temperature": 0.0,
    "auto_rebuild": True,
    "force_rebuild": False,
    "max_section_revision_attempts": 2,
    "top_k_evidence_per_section": 8,
    "max_evidence_chars": 18000,
    "max_quantitative_rows_per_section": 12,
    "allow_open_search_outside_outline_sources": False,
    "validate_citations_against_section_evidence": True,
    "validate_numeric_values_against_source_chunks": True,
    "fail_on_invalid_draft": True,
}

def get_draft_writing_policy(overrides=None):
    policy = dict(DEFAULT_DRAFT_WRITING_POLICY)
    policy.update(dict(overrides or {}))
    return policy
