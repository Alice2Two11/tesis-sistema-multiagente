
from __future__ import annotations

from typing import Any


def _safe_str(value: Any) -> str:
    return (
        ""
        if value is None
        else str(value).strip()
    )


def _is_organizational_section(
    section: dict[str, Any],
) -> bool:
    """
    Identifica secciones organizativas que normalmente
    no requieren fuentes documentales.
    """
    section_type = _safe_str(
        section.get("section_type")
    ).casefold()

    section_title = _safe_str(
        section.get("section_title")
    ).casefold()

    text = (
        section_type
        + " "
        + section_title
    )

    organizational_terms = (
        "introducción",
        "introduccion",
        "introduction",
        "conclusión",
        "conclusion",
        "conclusiones",
        "conclusions",
        "cierre",
    )

    papers = (
        section.get("papers_to_use")
        or []
    )

    return (
        not papers
        and any(
            term in text
            for term in organizational_terms
        )
    )


def assign_source_aware_section_budgets(
    outline_sections,
    target_total_words,
    *,
    organizational_target_words=40,
):
    """
    Distribuye el presupuesto total sin asignar a las
    secciones organizativas el mismo peso que a las
    secciones sustantivas.

    La suma de los objetivos permanece aproximadamente
    igual a target_total_words.
    """
    sections = list(
        outline_sections
        or []
    )

    if not sections:
        return {}

    target_total_words = max(
        int(target_total_words),
        1,
    )

    organizational_target_words = max(
        int(organizational_target_words),
        20,
    )

    organizational_sections = [
        section
        for section in sections
        if _is_organizational_section(
            section
        )
    ]

    substantive_sections = [
        section
        for section in sections
        if not _is_organizational_section(
            section
        )
    ]

    budgets = {}

    organizational_total = (
        len(organizational_sections)
        * organizational_target_words
    )

    remaining_words = max(
        target_total_words
        - organizational_total,
        len(substantive_sections) * 80,
    )

    substantive_target = (
        max(
            80,
            int(
                remaining_words
                / max(
                    len(
                        substantive_sections
                    ),
                    1,
                )
            ),
        )
    )

    for section in organizational_sections:
        section_id = _safe_str(
            section.get("section_id")
        )

        target = (
            organizational_target_words
        )

        budgets[section_id] = {
            "target_words": target,
            "minimum_words": 1,
            "maximum_words": max(
                80,
                int(target * 2),
            ),
            "budget_type": (
                "source_free_organizational"
            ),
        }

    for section in substantive_sections:
        section_id = _safe_str(
            section.get("section_id")
        )

        target = substantive_target

        budgets[section_id] = {
            "target_words": target,
            "minimum_words": max(
                50,
                int(target * 0.65),
            ),
            "maximum_words": max(
                90,
                int(target * 1.40),
            ),
            "budget_type": (
                "source_aware_substantive"
            ),
        }

    return budgets
