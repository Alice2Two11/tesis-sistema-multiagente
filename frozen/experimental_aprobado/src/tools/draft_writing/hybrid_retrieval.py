
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable


def _safe_str(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _candidate_key(
    row: dict[str, Any],
) -> tuple[str, str]:
    return (
        _safe_str(row.get("source_filename")),
        _safe_str(row.get("chunk_id")),
    )


def build_quantitative_query(
    base_query: str,
) -> str:
    quantitative_terms = (
        "experimental results performance metrics accuracy "
        "prediction error comparison models "
        "RMSE MAE MBE MAPE NRMSE correlation coefficient "
        "R R2 percentage percent forecast results"
    )

    return (
        f"{_safe_str(base_query)} {quantitative_terms}"
    ).strip()


def query_csv_ranked_restricted(
    chunks_df,
    query,
    source_filenames,
    top_k,
    max_evidence_chars=18000,
    valid_source_chunk_pairs=None,
):
    from src.tools.draft_writing.retrieval import (
        dedupe_evidence,
        safe_str,
        tokenize_for_overlap,
    )

    if not source_filenames or top_k <= 0:
        return []

    query_tokens = tokenize_for_overlap(query)

    subset = chunks_df[
        chunks_df["source_filename"]
        .astype(str)
        .isin(source_filenames)
    ]

    rows = []

    for _, source_row in subset.iterrows():
        text = safe_str(source_row["text"])
        text_tokens = tokenize_for_overlap(text)

        overlap = len(query_tokens & text_tokens)
        score = overlap / max(len(query_tokens), 1)

        rows.append(
            {
                "source_filename": safe_str(
                    source_row["source_filename"]
                ),
                "chunk_id": safe_str(
                    source_row["chunk_id"]
                ),
                "text": text[:max_evidence_chars],
                "score": float(score),
                "retrieval_method": (
                    "csv_lexical_ranked_experimental"
                ),
            }
        )

    rows.sort(
        key=lambda row: (
            -float(row.get("score", 0.0)),
            _safe_str(row.get("source_filename")),
            _safe_str(row.get("chunk_id")),
        )
    )

    return dedupe_evidence(
        rows,
        valid_source_chunk_pairs,
    )[:top_k]


def reciprocal_rank_fusion_many(
    rankings: Iterable[
        tuple[str, list[dict[str, Any]]]
    ],
    *,
    rrf_k: int = 60,
) -> list[dict[str, Any]]:
    if rrf_k <= 0:
        raise ValueError("rrf_k debe ser mayor que cero")

    fused = {}
    fused_scores = defaultdict(float)

    for method_name, rows in rankings:
        for rank, original in enumerate(rows, start=1):
            row = dict(original)
            key = _candidate_key(row)

            if not key[0] or not key[1]:
                continue

            fused_scores[key] += 1.0 / (rrf_k + rank)

            if key not in fused:
                fused[key] = row
                fused[key]["retrieval_methods"] = []
                fused[key]["component_ranks"] = {}
                fused[key]["component_scores"] = {}

            item = fused[key]

            if method_name not in item["retrieval_methods"]:
                item["retrieval_methods"].append(method_name)

            item["component_ranks"][method_name] = rank

            item["component_scores"][method_name] = float(
                row.get("score", 0.0) or 0.0
            )

    output = []

    for key, item in fused.items():
        row = dict(item)
        row["score"] = fused_scores[key]
        row["hybrid_score"] = fused_scores[key]
        row["retrieval_method"] = "multi_query_rrf"
        output.append(row)

    output.sort(
        key=lambda row: (
            -float(row.get("hybrid_score", 0.0)),
            _safe_str(row.get("source_filename")),
            _safe_str(row.get("chunk_id")),
        )
    )

    return output


def reciprocal_rank_fusion(
    chroma_rows,
    csv_rows,
    *,
    rrf_k=60,
):
    return reciprocal_rank_fusion_many(
        [
            ("chroma_restricted", chroma_rows),
            ("csv_lexical_restricted", csv_rows),
        ],
        rrf_k=rrf_k,
    )


def balanced_hybrid_selection(
    chroma_rows,
    csv_rows,
    fused_rows,
    *,
    final_top_k=8,
    chroma_quota=3,
    csv_quota=3,
    valid_source_chunk_pairs=None,
):
    from src.tools.draft_writing.retrieval import (
        dedupe_evidence,
    )

    if final_top_k <= 0:
        return []

    selected = []
    selected_keys = set()

    def add_rows(rows, limit, selection_source):
        added = 0

        for original in rows:
            if added >= limit:
                break

            row = dict(original)
            key = _candidate_key(row)

            if not key[0] or not key[1]:
                continue

            if key in selected_keys:
                continue

            row["hybrid_selection_method"] = (
                "balanced_quota_rrf"
            )
            row["selection_source"] = selection_source

            selected.append(row)
            selected_keys.add(key)
            added += 1

    add_rows(
        chroma_rows,
        chroma_quota,
        "chroma_quota",
    )

    add_rows(
        csv_rows,
        csv_quota,
        "csv_quota",
    )

    remaining_slots = final_top_k - len(selected)

    if remaining_slots > 0:
        add_rows(
            fused_rows,
            remaining_slots,
            "rrf_completion",
        )

    final_rows = dedupe_evidence(
        selected,
        valid_source_chunk_pairs,
    )

    return final_rows[:final_top_k]
