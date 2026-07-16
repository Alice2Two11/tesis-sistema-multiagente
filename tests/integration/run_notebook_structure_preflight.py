from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK = ROOT / "03_agente_extraccion_kb_migrado_v16.ipynb"


def main() -> int:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    source = "\n\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    )
    ast.parse(source)
    required = [
        "RUN_REAL_EXTRACTION",
        "PRECHECK MODE",
        "REAL MODE",
        "execute_extraction_runtime_transaction",
        "load_runtime_credential",
        "transaction_executed",
    ]
    forbidden = [
        "def retrieve_chunks_for_paper",
        "def is_bad_card",
        "def run_title_repair",
        "def build_knowledge_base_rows",
        "Fernet(",
        "03B",
        "quantitative_extraction",
    ]
    missing = [item for item in required if item not in source]
    duplicated = [item for item in forbidden if item in source]
    if missing or duplicated:
        print(json.dumps({"status": "FAILED", "missing": missing, "forbidden": duplicated}))
        return 1
    print(json.dumps({
        "status": "OK",
        "notebook": NOTEBOOK.name,
        "ast_valid": True,
        "thin_shell": True,
        "explicit_modes": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
