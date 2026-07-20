from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from src.contracts.agent_input import ArtifactReference
from src.state.fingerprints import sha256_file
from src.io.atomic_write import atomic_write_text

NAMES = (
    "state_of_art_draft.json",
    "state_of_art_draft.md",
    "draft_sections.csv",
    "draft_rag_evidence.csv",
    "draft_quality_check.csv",
    "draft_length_check.csv",
    "draft_claim_evidence.csv",
    "numeric_hallucination_check.csv",
    "draft_validation_report.json",
    "quantitative_comparative_table_used.csv",
    "dataset_technique_summary_used.csv",
    "draft_generation_manifest.json",
)


def _write(path, text):
    atomic_write_text(Path(path), text)


def write_partial_validation(out, validation):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    path = out / "draft_validation_report.json"
    _write(path, json.dumps(validation, ensure_ascii=False, indent=2))
    return path


def write_raw_section_output(raw_dir, section_id, generation_attempt, text):
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{section_id}_attempt_{generation_attempt}.txt"
    _write(path, str(text))
    return path


def write_raw_section_validation(raw_dir, section_id, generation_attempt, validation):
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{section_id}_attempt_{generation_attempt}_validation.json"
    _write(path, json.dumps(validation, ensure_ascii=False, indent=2))
    return path



def write_raw_section_rag_trace(raw_dir, section_id, generation_attempt, trace):
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{section_id}_attempt_{generation_attempt}_rag_trace.json"
    _write(path, json.dumps(trace, ensure_ascii=False, indent=2))
    return path

def write_draft_artifacts(
    out,
    draft,
    evidence_rows,
    validation,
    quant_df,
    dataset_df,
    manifest,
    quality_rows,
    section_rows,
    claim_rows,
    numeric_rows,
):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    sections = draft.get("sections", [])
    length_columns = [
        "section_id",
        "section_title",
        "word_count",
        "target_words",
        "minimum_words",
        "maximum_words",
        "source_free_organizational_section",
        "within_section_range",
        "citation_count",
        "claim_count",
    ]
    payloads = {
        "state_of_art_draft.json": json.dumps(draft, ensure_ascii=False, indent=2),
        "state_of_art_draft.md": "# " + draft.get("title", "Borrador") + "\n\n" + "\n\n".join(
            "## " + s.get("section_title", "") + "\n\n" + s.get("draft_text", "")
            for s in sections
        ),
        "draft_sections.csv": pd.DataFrame(section_rows).to_csv(index=False),
        "draft_rag_evidence.csv": pd.DataFrame(evidence_rows).to_csv(index=False),
        "draft_quality_check.csv": pd.DataFrame(quality_rows).to_csv(index=False),
        "draft_length_check.csv": pd.DataFrame(section_rows, columns=length_columns).to_csv(index=False),
        "draft_claim_evidence.csv": pd.DataFrame(
            claim_rows,
            columns=[
                "section_id",
                "claim_id",
                "claim_text",
                "source_filename",
                "chunk_id",
                "rank",
                "retrieval_method",
                "evidence_text",
                "allowed_for_section",
            ],
        ).to_csv(index=False),
        "numeric_hallucination_check.csv": pd.DataFrame(
            numeric_rows,
            columns=[
                "section_id",
                "claim_id",
                "claim_text",
                "numeric_value",
                "found_in_cited_chunks",
                "matching_citations",
                "risk",
            ],
        ).to_csv(index=False),
        "draft_validation_report.json": json.dumps(validation, ensure_ascii=False, indent=2),
        "quantitative_comparative_table_used.csv": quant_df.to_csv(index=False),
        "dataset_technique_summary_used.csv": dataset_df.to_csv(index=False),
        "draft_generation_manifest.json": json.dumps(manifest, ensure_ascii=False, indent=2),
    }
    artifacts = {}
    for name, text in payloads.items():
        path = out / name
        _write(path, text)
        artifacts[name] = ArtifactReference(str(path), sha256_file(path))
    raw = out / "raw_section_outputs"
    raw.mkdir(exist_ok=True)
    artifacts["raw_section_outputs"] = ArtifactReference(str(raw), "DIRECTORY")
    return artifacts
