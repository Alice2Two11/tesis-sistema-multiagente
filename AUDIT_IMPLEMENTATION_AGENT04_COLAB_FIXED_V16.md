# AGENTE 04 V1.6 — CORRECCIÓN OPERATIVA COLAB

## Alcance

Se corrigieron exclusivamente dos defectos operativos del notebook shell:

1. bootstrap del repositorio antes de cualquier importación `src`;
2. resolución del `pipeline_state.json` real antes de crear `StateStore` o leer el intento previo.

No se modificaron la lógica científica, el quality gate, `representative_papers`, el Agente 03 ni 03B.

## Bootstrap

Orden implementado:

```text
configuración
→ clone o fetch/reset/clean del repositorio
→ eliminación de módulos src cargados y __pycache__
→ importlib.invalidate_caches()
→ inserción única de CODE_ROOT en sys.path
→ imports de src
```

Cuando `CODE_ROOT` no existe, se clona `PROJECT_SOURCE_URL`. Cuando contiene un repositorio Git, se ejecuta `fetch`, `reset --hard origin/main` y `clean -fd`.

## PipelineState

Ruta primaria:

```text
PROJECT_DIR / experiment_id / 05_outputs / 00_orchestrator_planner / pipeline_state.json
```

Si no existe, se busca `pipeline_state.json` mediante `rglob` únicamente dentro del experimento. Solo se acepta un candidato. Cero candidatos produce un fallo explícito; más de uno produce un fallo de ambigüedad.

El Agente 04 no crea un segundo `pipeline_state.json` ni usa enlaces simbólicos.

La ruta resuelta se asigna a `configuration["state_path"]` antes de:

- construir `StateStore`;
- construir `AgentInput` del intento 2;
- leer `PreviousAttemptSummary`;
- ejecutar REAL MODE intento 1;
- ejecutar REAL MODE intento 2;
- ejecutar DETERMINISTIC_REPAIR.

## Preservación

Todos los archivos bajo `src/`, junto con los notebooks 03 y 03B, conservan el mismo SHA-256 que la candidata behavior-preserving anterior.

## Validación

- Ejecución exacta `python -m unittest discover -s tests -p "test_*.py"`: 123 pruebas, OK.
- compilación de `src` y `tests`: OK.
- notebook PRECHECK en kernel limpio: OK.
- clone desde CODE_ROOT inexistente usando repositorio Git local controlado: OK.
- import de `src` después del bootstrap: OK.
- resolución de ruta canónica: OK.
- fallback único por `rglob`: OK.
- intento 2 lee transición RETRY del intento 1: OK.
- reparación determinista usa el mismo estado resuelto: OK.
- no se observó `ModuleNotFoundError`: OK.
- no se observó `El intento 2 requiere pipeline_state del intento 1` en la ruta corregida: OK.

La ejecución real externa con OpenAI no se ejecutó en este entorno.


## Corrección final de la suite de preservación

`tests/v16/test_alignment_v16.py` ahora interpreta el manifiesto de preservación mediante:

```python
payload = json.loads((ROOT / "preserved_sha256.json").read_text())
if payload.get("status") != "ALL_PROTECTED_FILES_PRESERVED":
    raise AssertionError(...)
PRESERVED = payload["files"]
```

La prueba ya no interpreta `status` y `files` como rutas. La ejecución final exacta fue:

```text
Ran 123 tests in 2.932s
OK
```

No se modificó el notebook ni la lógica científica.
