
from __future__ import annotations

import math
import re
from typing import Any


def _safe_str(value: Any) -> str:
    if value is None:
        return ""

    try:
        if isinstance(value, float) and math.isnan(value):
            return ""
    except TypeError:
        pass

    text = str(value).strip()

    if text.casefold() == "nan":
        return ""

    return text


def _normalize_percent_spacing(text: Any) -> str:
    return re.sub(
        r"(\d)\s+%",
        r"\1%",
        _safe_str(text),
    )


def _candidate_key(
    row: dict[str, Any],
) -> tuple[str, str]:
    return (
        _safe_str(row.get("source_filename")),
        _safe_str(row.get("chunk_id")),
    )


def _split_chunk_ids(value: Any) -> list[str]:
    text = _safe_str(value)

    if not text:
        return []

    parts = re.split(
        r"[;,|\n]+",
        text,
    )

    output = []
    seen = set()

    for part in parts:
        chunk_id = part.strip()

        if not chunk_id:
            continue

        if chunk_id in seen:
            continue

        seen.add(chunk_id)
        output.append(chunk_id)

    return output


def _row_numeric_literals(
    row: dict[str, Any],
) -> list[str]:
    """
    Extrae únicamente los valores explícitos de una fila
    cuantitativa confirmada.

    No toma años, índices o números de otros campos.
    """
    values = []

    for field_name in (
        "value",
        "raw_value",
        "numeric_value",
    ):
        value = _safe_str(
            row.get(field_name)
        )

        if not value:
            continue

        candidates = re.findall(
            r"(?<!\w)"
            r"[+-]?"
            r"(?:\d+\.\d+|\d+)"
            r"%?"
            r"(?!\w)",
            _normalize_percent_spacing(value),
        )

        for candidate in candidates:
            if candidate not in values:
                values.append(candidate)

    return values


def _confirmed_quantitative_rows(
    quantitative_context: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = (
        quantitative_context.get(
            "quantitative_results"
        )
        if isinstance(
            quantitative_context,
            dict,
        )
        else []
    )

    if not isinstance(rows, list):
        return []

    confirmed = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        verification_status = _safe_str(
            row.get("verification_status")
        ).casefold()

        found_in_source_chunk = _safe_str(
            row.get(
                "value_found_in_source_chunk"
            )
        ).casefold()

        is_confirmed = (
            verification_status
            == "confirmed_in_source_chunk"
            or found_in_source_chunk
            in {
                "true",
                "1",
                "yes",
                "sí",
                "si",
            }
        )

        if not is_confirmed:
            continue

        source_filename = _safe_str(
            row.get("source_filename")
        )

        chunk_ids = _split_chunk_ids(
            row.get(
                "source_chunk_ids_checked"
            )
        )

        numeric_literals = (
            _row_numeric_literals(row)
        )

        if (
            not source_filename
            or not chunk_ids
            or not numeric_literals
        ):
            continue

        normalized = dict(row)
        normalized["_source_filename"] = (
            source_filename
        )
        normalized["_chunk_ids"] = chunk_ids
        normalized["_numeric_literals"] = (
            numeric_literals
        )

        confirmed.append(normalized)

    return confirmed


def build_quantitative_chunk_candidates(
    chunks_df,
    quantitative_context,
    *,
    authorized_source_filenames=None,
    max_evidence_chars=18000,
    valid_source_chunk_pairs=None,
):
    """
    Construye candidatos documentales a partir de filas
    cuantitativas verificadas.

    Un chunk solo recibe crédito por un valor cuando el valor
    aparece literalmente en su texto.
    """
    authorized_sources = {
        _safe_str(source)
        for source
        in (
            authorized_source_filenames
            or []
        )
        if _safe_str(source)
    }

    confirmed_rows = (
        _confirmed_quantitative_rows(
            quantitative_context
        )
    )

    requirements_by_pair = {}

    for row in confirmed_rows:
        source_filename = row[
            "_source_filename"
        ]

        if (
            authorized_sources
            and source_filename
            not in authorized_sources
        ):
            continue

        for chunk_id in row["_chunk_ids"]:
            pair = (
                source_filename,
                chunk_id,
            )

            requirements_by_pair.setdefault(
                pair,
                {
                    "numeric_literals": set(),
                    "metrics": set(),
                    "verification_statuses": set(),
                },
            )

            item = requirements_by_pair[pair]

            item["numeric_literals"].update(
                row["_numeric_literals"]
            )

            metric = _safe_str(
                row.get("metric")
            )

            if metric:
                item["metrics"].add(metric)

            verification_status = _safe_str(
                row.get(
                    "verification_status"
                )
            )

            if verification_status:
                item[
                    "verification_statuses"
                ].add(verification_status)

    if not requirements_by_pair:
        return []

    candidates = []

    for _, source_row in chunks_df.iterrows():
        source_filename = _safe_str(
            source_row.get(
                "source_filename"
            )
        )

        chunk_id = _safe_str(
            source_row.get("chunk_id")
        )

        pair = (
            source_filename,
            chunk_id,
        )

        if pair not in requirements_by_pair:
            continue

        if (
            valid_source_chunk_pairs
            is not None
            and pair
            not in valid_source_chunk_pairs
        ):
            continue

        text = _safe_str(
            source_row.get("text")
        )

        normalized_text = (
            _normalize_percent_spacing(text)
        )

        requirements = (
            requirements_by_pair[pair]
        )

        matched_values = sorted(
            value
            for value
            in requirements[
                "numeric_literals"
            ]
            if value in normalized_text
        )

        if not matched_values:
            continue

        # Prioriza chunks que respaldan más valores.
        score = float(
            len(matched_values)
        )

        candidates.append(
            {
                "source_filename": (
                    source_filename
                ),
                "chunk_id": chunk_id,
                "text": text[
                    :max_evidence_chars
                ],
                "score": score,
                "retrieval_method": (
                    "quantitative_confirmed_chunk"
                ),
                "quantitative_values": (
                    matched_values
                ),
                "quantitative_metrics": sorted(
                    requirements["metrics"]
                ),
                "verification_statuses": sorted(
                    requirements[
                        "verification_statuses"
                    ]
                ),
            }
        )

    candidates.sort(
        key=lambda row: (
            -len(
                row.get(
                    "quantitative_values",
                    [],
                )
            ),
            -float(
                row.get("score", 0.0)
            ),
            _safe_str(
                row.get("source_filename")
            ),
            _safe_str(
                row.get("chunk_id")
            ),
        )
    )

    return candidates


def augment_evidence_with_quantitative_chunks(
    base_evidence,
    chunks_df,
    quantitative_context,
    *,
    authorized_source_filenames=None,
    final_top_k=8,
    quantitative_quota=2,
    max_evidence_chars=18000,
    valid_source_chunk_pairs=None,
):
    """
    Combina retrieval híbrido y evidencia cuantitativa citable.

    Política:
    1. Reserva hasta quantitative_quota posiciones para chunks
       cuantitativos confirmados.
    2. Completa el resto con la evidencia híbrida original.
    3. Deduplica por source_filename + chunk_id.
    4. Nunca acepta una fila cuantitativa sin chunk fuente.
    5. Nunca inventa una cita sintética.
    """
    if final_top_k <= 0:
        return []

    quantitative_quota = max(
        0,
        min(
            int(quantitative_quota),
            int(final_top_k),
        ),
    )

    quantitative_candidates = (
        build_quantitative_chunk_candidates(
            chunks_df,
            quantitative_context,
            authorized_source_filenames=(
                authorized_source_filenames
            ),
            max_evidence_chars=(
                max_evidence_chars
            ),
            valid_source_chunk_pairs=(
                valid_source_chunk_pairs
            ),
        )
    )

    selected = []
    selected_keys = set()

    def add_rows(
        rows,
        limit,
        selection_source,
    ):
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

            if (
                valid_source_chunk_pairs
                is not None
                and key
                not in valid_source_chunk_pairs
            ):
                continue

            row["selection_source"] = (
                selection_source
            )

            row[
                "hybrid_selection_method"
            ] = (
                "hybrid_plus_confirmed_quantitative"
            )

            selected.append(row)
            selected_keys.add(key)
            added += 1

    # Conserva primero la mayor parte de la evidencia híbrida.
    base_quota = (
        final_top_k
        - quantitative_quota
    )

    add_rows(
        base_evidence,
        base_quota,
        "hybrid_base_quota",
    )

    # Añade chunks cuantitativos verificables.
    add_rows(
        quantitative_candidates,
        quantitative_quota,
        "confirmed_quantitative_quota",
    )

    # Si hubo duplicados o faltaron candidatos cuantitativos,
    # completa con el resto del ranking híbrido.
    remaining = final_top_k - len(selected)

    if remaining > 0:
        add_rows(
            base_evidence,
            remaining,
            "hybrid_completion",
        )

    # Último respaldo: más chunks cuantitativos válidos.
    remaining = final_top_k - len(selected)

    if remaining > 0:
        add_rows(
            quantitative_candidates,
            remaining,
            "quantitative_completion",
        )

    return selected[:final_top_k]



def augment_evidence_with_quantitative_chunks_greedy(
    base_evidence,
    chunks_df,
    quantitative_context,
    *,
    authorized_source_filenames=None,
    final_top_k=8,
    quantitative_quota=2,
    max_evidence_chars=18000,
    valid_source_chunk_pairs=None,
):
    """
    Combina evidencia híbrida y chunks cuantitativos confirmados
    mediante cobertura marginal.

    Política:
    1. Conserva final_top_k - quantitative_quota evidencias base.
    2. Detecta qué valores cuantitativos ya están cubiertos.
    3. Selecciona cada chunk cuantitativo según la cantidad de
       valores todavía no cubiertos que añade.
    4. Favorece diversidad de fuentes cuando existe empate.
    5. No acepta chunks sin coincidencia literal del valor.
    """

    if final_top_k <= 0:
        return []

    quantitative_quota = max(
        0,
        min(
            int(quantitative_quota),
            int(final_top_k),
        ),
    )

    quantitative_candidates = (
        build_quantitative_chunk_candidates(
            chunks_df,
            quantitative_context,
            authorized_source_filenames=(
                authorized_source_filenames
            ),
            max_evidence_chars=(
                max_evidence_chars
            ),
            valid_source_chunk_pairs=(
                valid_source_chunk_pairs
            ),
        )
    )

    selected = []
    selected_keys = set()
    selected_sources = set()

    def key_of(row):
        return (
            _safe_str(
                row.get("source_filename")
            ),
            _safe_str(
                row.get("chunk_id")
            ),
        )

    def valid_row(row):
        key = key_of(row)

        if not key[0] or not key[1]:
            return False

        if key in selected_keys:
            return False

        if (
            valid_source_chunk_pairs
            is not None
            and key
            not in valid_source_chunk_pairs
        ):
            return False

        return True

    def append_row(
        original,
        selection_source,
    ):
        row = dict(original)
        key = key_of(row)

        row["selection_source"] = (
            selection_source
        )

        row[
            "hybrid_selection_method"
        ] = (
            "hybrid_plus_confirmed_"
            "quantitative_greedy"
        )

        selected.append(row)
        selected_keys.add(key)
        selected_sources.add(key[0])

    # --------------------------------------------------------
    # A. CONSERVAR CUOTA BASE
    # --------------------------------------------------------

    base_quota = (
        int(final_top_k)
        - quantitative_quota
    )

    for original in base_evidence:
        if len(selected) >= base_quota:
            break

        if not valid_row(original):
            continue

        append_row(
            original,
            "hybrid_base_quota",
        )

    # --------------------------------------------------------
    # B. UNIVERSO DE VALORES CUANTITATIVOS CONFIRMADOS
    # --------------------------------------------------------

    quantitative_universe = set()

    for row in quantitative_candidates:
        quantitative_universe.update(
            _safe_str(value)
            for value
            in row.get(
                "quantitative_values",
                [],
            )
            if _safe_str(value)
        )

    # --------------------------------------------------------
    # C. VALORES YA CUBIERTOS POR LA EVIDENCIA BASE
    # --------------------------------------------------------

    covered_values = set()

    for row in selected:
        normalized_text = (
            _normalize_percent_spacing(
                row.get("text")
            )
        )

        for value in quantitative_universe:
            if value in normalized_text:
                covered_values.add(value)

    # --------------------------------------------------------
    # D. SELECCIÓN GREEDY POR COBERTURA MARGINAL
    # --------------------------------------------------------

    quantitative_added = 0

    while (
        quantitative_added
        < quantitative_quota
    ):
        eligible = [
            row
            for row in quantitative_candidates
            if valid_row(row)
        ]

        if not eligible:
            break

        scored = []

        for row in eligible:
            row_values = {
                _safe_str(value)
                for value
                in row.get(
                    "quantitative_values",
                    [],
                )
                if _safe_str(value)
            }

            marginal_values = (
                row_values
                - covered_values
            )

            source_filename = _safe_str(
                row.get("source_filename")
            )

            source_diversity_bonus = (
                1
                if source_filename
                not in selected_sources
                else 0
            )

            scored.append(
                (
                    len(marginal_values),
                    source_diversity_bonus,
                    len(row_values),
                    float(
                        row.get(
                            "score",
                            0.0,
                        )
                        or 0.0
                    ),
                    _safe_str(
                        row.get(
                            "source_filename"
                        )
                    ),
                    _safe_str(
                        row.get("chunk_id")
                    ),
                    row,
                    marginal_values,
                )
            )

        scored.sort(
            key=lambda item: (
                -item[0],
                -item[1],
                -item[2],
                -item[3],
                item[4],
                item[5],
            )
        )

        (
            marginal_count,
            _source_bonus,
            _total_value_count,
            _score,
            _source,
            _chunk,
            best_row,
            marginal_values,
        ) = scored[0]

        # Si no añade nada nuevo, se permite completar solo
        # cuando todavía quedan espacios vacíos.
        append_row(
            best_row,
            (
                "confirmed_quantitative_"
                "greedy_quota"
            ),
        )

        covered_values.update(
            _safe_str(value)
            for value
            in best_row.get(
                "quantitative_values",
                [],
            )
            if _safe_str(value)
        )

        selected[-1][
            "marginal_quantitative_values"
        ] = sorted(marginal_values)

        selected[-1][
            "marginal_quantitative_count"
        ] = int(marginal_count)

        quantitative_added += 1

    # --------------------------------------------------------
    # E. COMPLETAR SI HUBO MENOS CANDIDATOS CUANTITATIVOS
    # --------------------------------------------------------

    for original in base_evidence:
        if len(selected) >= final_top_k:
            break

        if not valid_row(original):
            continue

        append_row(
            original,
            "hybrid_completion",
        )

    for original in quantitative_candidates:
        if len(selected) >= final_top_k:
            break

        if not valid_row(original):
            continue

        append_row(
            original,
            "quantitative_completion",
        )

    return selected[:final_top_k]
