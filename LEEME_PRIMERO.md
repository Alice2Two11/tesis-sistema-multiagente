# Agente 06 V17 limpio

Este paquete contiene los archivos que deben copiarse sobre el repositorio
existente. No se debe subir el ZIP como carpeta adicional.

## Archivos para GitHub

- `src/adapters/draft_writing_runtime.py`
- `src/adapters/draft_writing_notebook.py`
- `src/agents/draft_writing_agent.py`
- `src/config/draft_writing_policy_config.py`
- `src/tools/draft_writing/validation.py`
- `notebooks/06_agente_redactor_v17_LIMPIO.ipynb`

## Qué conserva

El Agente 06 sigue siendo agéntico:

- recuperación híbrida;
- selección de evidencia;
- generación por secciones;
- validación;
- normalización;
- reintentos;
- decisión `APPROVED` o `NEEDS_REVISION`;
- transición `ADVANCE` o `RETRY`;
- trazabilidad y doce artefactos contractuales.

## Correcciones de producción incluidas

1. La validación normalizada válida puede aceptar una sección reparada.
2. La desviación individual de palabras se registra como warning y no bloquea
   cuando la longitud global y las validaciones científicas sí pasan.

## Limpieza aplicada al notebook

- elimina el modelo OpenAI hardcodeado;
- deriva experimento y modelo desde `active_experiment.json`, creado por el 00;
- elimina el experimento `experimento_paper_02` hardcodeado;
- deja una sola celda de controles;
- elimina imports repetidos;
- elimina limpieza destructiva de `__pycache__`;
- mueve PREPARE aislado, lectura de artefactos, resumen, auditoría y COMMIT a
  `src/adapters/draft_writing_notebook.py`;
- usa `REQUIRED_DRAFT_ARTIFACTS` como fuente única;
- guarda valores seguros: ejecución y COMMIT desactivados.

## Instalación

Copiar el contenido del paquete sobre la raíz del repositorio y ejecutar:

```bash
git add \
  src/adapters/draft_writing_runtime.py \
  src/adapters/draft_writing_notebook.py \
  src/agents/draft_writing_agent.py \
  src/config/draft_writing_policy_config.py \
  src/tools/draft_writing/validation.py \
  notebooks/06_agente_redactor_v17_LIMPIO.ipynb

git commit -m "Clean Agent 06 notebook and centralize Colab helpers"
git push
```

No subir carpetas `__pycache__` ni archivos `.pyc`.

Añadir al `.gitignore`:

```gitignore
__pycache__/
*.pyc
```

## Controles seguros del notebook

El notebook se entrega con:

```python
RUN_EXECUTE = False
FORCE_REEXECUTION = False
COMMIT_ENABLED = False
CONFIRM_COMMIT_TEXT = ""
```

Para una nueva ejecución controlada:

```python
RUN_EXECUTE = True
FORCE_REEXECUTION = True
COMMIT_ENABLED = False
```

Para COMMIT, sin volver a ejecutar el LLM:

```python
COMMIT_ENABLED = True
CONFIRM_COMMIT_TEXT = "CONFIRMAR_COMMIT_AGENTE_06"
```
