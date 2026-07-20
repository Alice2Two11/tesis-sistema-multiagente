#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

TARGET_VALUES = ["0.96", "1.34", "10%", "58.7%", "6.11%", "99%"]
CITATION_RE = re.compile(r"\[\s*([^\]|]+?)\s*\|\s*([^\]]+?)\s*\]")
NUMBER_RE = re.compile(r"(?<!\w)[+-]?\d+(?:[.,]\d+)?%?")


def normalized_number(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).replace(",", ".").replace("%", "")


def extract_json_object(raw: str) -> dict[str, Any]:
    candidates = [raw]
    candidates.extend(re.findall(r"```(?:json)?\s*(.*?)```", raw, flags=re.S | re.I))
    start, end = raw.find("{"), raw.rfind("}")
    if start >= 0 and end > start:
        candidates.append(raw[start : end + 1])
    for candidate in candidates:
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
    return {}


def citation_strings(text: str) -> list[str]:
    seen: set[tuple[str, str]] = set()
    out: list[str] = []
    for source, chunk in CITATION_RE.findall(text or ""):
        pair = (source.strip(), chunk.strip())
        if pair not in seen:
            seen.add(pair)
            out.append(f"[{pair[0]} | {pair[1]}]")
    return out


def sentence_citations_for_value(text: str, value: str) -> list[str]:
    value_norm = normalized_number(value)
    matches: list[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", text or ""):
        nums = [normalized_number(x) for x in NUMBER_RE.findall(sentence)]
        if value_norm in nums:
            matches.extend(citation_strings(sentence))
    return list(dict.fromkeys(matches))


def main() -> int:
    parser = argparse.ArgumentParser(description="Corrida diagnóstica RAG aislada del Agente 06; no modifica PipelineState.")
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--code-root", default="/content/tesis_codigo")
    parser.add_argument("--section-id", default="S2")
    parser.add_argument("--output-dir")
    parser.add_argument("--values", nargs="*", default=TARGET_VALUES)
    args = parser.parse_args()

    code_root = Path(args.code_root).resolve()
    project_dir = Path(args.project_dir).resolve()
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))

    from src.adapters.draft_writing_runtime import (
        build_chroma_collection,
        build_draft_agent_input,
        load_draft_configuration,
    )
    from src.tools.draft_writing import (
        build_section_query,
        retrieve_section_evidence,
        validate_draft_dependencies,
    )
    from src.io.atomic_write import atomic_write_json

    # Loader-only. No DraftWritingAgent.execute, no transaction, no StateStore.
    cfg = load_draft_configuration(project_dir, attempt_number=1)
    agent_input = build_draft_agent_input(cfg)
    bundle = validate_draft_dependencies(agent_input)
    collection = build_chroma_collection(cfg)

    section = next((s for s in bundle["outline"].get("sections", []) if str(s.get("section_id", "")).strip() == args.section_id), None)
    if section is None:
        raise SystemExit(f"SECTION_NOT_FOUND:{args.section_id}")

    top_k = int(cfg["policy"].get("top_k_evidence_per_section", 8))
    query = build_section_query(section)
    evidence = retrieve_section_evidence(section, collection, bundle["chunks"], top_k)
    allowed = {f"[{r['source_filename']} | {r['chunk_id']}]" for r in evidence}

    draft_dir = Path(cfg["output_dir"])
    raw_dir = draft_dir / "raw_section_outputs"
    output_dir = Path(args.output_dir).resolve() if args.output_dir else draft_dir / "diagnostic_rag_trace_run"
    output_dir.mkdir(parents=True, exist_ok=True)

    attempts = []
    raw_files = sorted(raw_dir.glob(f"{args.section_id}_attempt_*.txt"))
    for raw_path in raw_files:
        m = re.search(r"_attempt_(\d+)\.txt$", raw_path.name)
        if not m:
            continue
        attempt = int(m.group(1))
        raw_text = raw_path.read_text(encoding="utf-8")
        parsed = extract_json_object(raw_text)
        draft_text = str(parsed.get("draft_text", ""))
        llm_citations = citation_strings(draft_text or raw_text)

        validation_path = raw_dir / f"{args.section_id}_attempt_{attempt}_validation.json"
        validation = json.loads(validation_path.read_text(encoding="utf-8")) if validation_path.is_file() else {}

        trace = {
            "diagnostic_only": True,
            "contractual_attempt_created": False,
            "pipeline_state_modified": False,
            "section_id": args.section_id,
            "generation_attempt": attempt,
            "query": query,
            "top_k_evidence_per_section": top_k,
            "retrieved_chunks": [
                {
                    "source_filename": str(row.get("source_filename", "")),
                    "chunk_id": str(row.get("chunk_id", "")),
                    "score": float(row.get("score", 0.0) or 0.0),
                    "retrieval_method": str(row.get("retrieval_method", "")),
                    "text": str(row.get("text", "")),
                }
                for row in evidence
            ],
            "allowed_citations": sorted(allowed),
            "llm_citations": llm_citations,
            "validation": validation,
            "source_raw_output": str(raw_path),
        }
        atomic_write_json(output_dir / f"{args.section_id}_attempt_{attempt}_rag_trace.json", trace)
        attempts.append(trace)

    chunks = bundle["chunks"].copy()
    chunks["source_filename"] = chunks["source_filename"].astype(str)
    chunks["chunk_id"] = chunks["chunk_id"].astype(str)
    chunks["text"] = chunks["text"].astype(str)

    value_rows = []
    for value in args.values:
        value_norm = normalized_number(value)
        for trace in attempts:
            raw_obj = extract_json_object(Path(trace["source_raw_output"]).read_text(encoding="utf-8"))
            draft_text = str(raw_obj.get("draft_text", ""))
            used_for_value = sentence_citations_for_value(draft_text, value)
            cited_sources = {CITATION_RE.fullmatch(c).group(1).strip() for c in used_for_value if CITATION_RE.fullmatch(c)}
            candidate_rows = chunks[chunks["source_filename"].isin(cited_sources)] if cited_sources else chunks.iloc[0:0]
            matching = []
            for _, row in candidate_rows.iterrows():
                if value_norm in [normalized_number(x) for x in NUMBER_RE.findall(row["text"])]:
                    citation = f"[{row['source_filename']} | {row['chunk_id']}]"
                    matching.append({
                        "source_filename": row["source_filename"],
                        "chunk_id": row["chunk_id"],
                        "citation": citation,
                        "in_allowed_citations": citation in allowed,
                        "cited_by_llm_for_value": citation in used_for_value,
                        "text": row["text"],
                    })
            case = "A" if any(x["in_allowed_citations"] for x in matching) else "B"
            value_rows.append({
                "value": value,
                "generation_attempt": trace["generation_attempt"],
                "citations_used_for_value": used_for_value,
                "matching_chunks_same_cited_paper": matching,
                "classification": case,
                "classification_reason": (
                    "El chunk correcto estaba en ALLOWED_CITATIONS, pero el LLM no lo citó para ese valor."
                    if case == "A"
                    else "El chunk correcto no estaba en ALLOWED_CITATIONS de la corrida diagnóstica."
                ),
            })

    summary = {
        "diagnostic_only": True,
        "contractual_attempt_created": False,
        "pipeline_state_modified": False,
        "requested_transition": None,
        "published_draft": False,
        "experiment_id": cfg["experiment_id"],
        "section_id": args.section_id,
        "evidence_source": "real_chroma_plus_chunks_csv_and_existing_raw_outputs",
        "chroma_dir": str(cfg["chroma_dir"]),
        "chunks_csv": str(cfg["paths"]["chunks_clean"]),
        "raw_outputs_directory": str(raw_dir),
        "diagnostic_output_directory": str(output_dir),
        "query": query,
        "top_k_evidence_per_section": top_k,
        "allowed_citations": sorted(allowed),
        "values": value_rows,
    }
    atomic_write_json(output_dir / f"{args.section_id}_rag_diagnostic_summary.json", summary)
    print(json.dumps({
        "status": "DIAGNOSTIC_COMPLETED",
        "pipeline_state_modified": False,
        "contractual_attempt_created": False,
        "published_draft": False,
        "output_dir": str(output_dir),
        "trace_files": len(attempts),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
