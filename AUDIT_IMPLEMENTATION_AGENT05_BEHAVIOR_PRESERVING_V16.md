# AUDITORÍA DE IMPLEMENTACIÓN — AGENTE 05 V1.6

## A. Comportamiento científico original preservado

- Mismo contexto procedente del Agente 04.
- Mismo límite de 1.800 caracteres por valor.
- Mismo prompt científico y mismo esquema JSON.
- `temperature = 0`.
- Una llamada LLM cuando se reconstruye y cero cuando se reutiliza.
- Reparación por título mediante `get_close_matches` con `cutoff = 0.55`.
- Reparación de `paper_coverage_summary`.
- Eliminación de referencias no resolubles.
- Recorte literal `sections[:MAX_SECTIONS]`.
- Mismos tipos de sección que permiten `papers_to_use` vacío.
- Semántica no exhaustiva de `paper_coverage_summary`.
- Siete artefactos y rutas `03_thematic_analysis/` → `04_outline/`.
- No se añadió RAG, cobertura exhaustiva, métricas, crítico ni Judge.

## B. Infraestructura agéntica añadida

- `AgentInput` y `AgentResult` comunes.
- `PipelineState`, `StateStore`, PREPARE/EXECUTE/persist/COMMIT/RESUME.
- Fingerprints comunes conservando factores conceptuales del notebook antiguo.
- Escritura atómica y hashes finales.
- Credenciales mediante `load_runtime_credential`.
- `attempt_number` limitado a 1 y 2.
- `validation_ok=false` produce `COMPLETED/NEEDS_REVISION` y preserva los siete artefactos.
- Intento 1 solicita RETRY; intento 2 agotado usa HALT_STAGE.
- Notebook reducido a shell con bootstrap, PRECHECK y REAL MODE.

## C. Diferencias observables y conflictos

No se detectaron diferencias científicas autorizadas. Las únicas diferencias son contractuales, transaccionales y de escritura segura. El manifiesto y reporte del 04 son ahora dependencias obligatorias porque el Agente 04 cerrado los produce siempre, según decisión expresa.

## D. Mejoras funcionales rechazadas

No se implementaron Chroma/RAG, nuevas métricas, cobertura total, asignación obligatoria, prompt crítico, LLM Judge, embeddings, ranking, cambio de cutoff, integración directa con tablas 03B, reescritura automática, Agente 06 ni Orquestador final.

## E. Validación

- Suite real final: Ran 144 tests — OK.
- PRECHECK de notebook en kernel limpio: OK.
- Ejecución OpenAI real: pendiente de Colab.

## F. Correcciones operativas de la candidata Colab/tests fixed

### Política de preservación

`preserved_sha256.json` contiene exclusivamente archivos congelados. Se excluyeron archivos de entrega y reportes regenerables, incluidos `delivery_manifest.json`, `modified_files.txt`, `notebook_precheck_report.json`, `preserved_sha256.json`, `return_codes.json` y `test_report.txt`. La prueba `test_preserved_files_are_byte_identical` valida únicamente `payload["files"]` después de comprobar `status = ALL_PROTECTED_FILES_PRESERVED`.

### Repositorio por defecto

El notebook conserva `PROJECT_SOURCE_URL` como override y usa por defecto `https://github.com/Alice2Two11/tesis-sistema-multiagente.git`. Se verificó en un proceso aislado, con `CODE_ROOT` inexistente y sin `PROJECT_SOURCE_URL`, que el bootstrap construye el comando `git clone` con esa URL antes de importar `src`. La conectividad real a GitHub no se ejecutó en el contenedor porque su DNS externo no estaba disponible; no se presenta como validación de red.

### Ejecución final exacta

Comando: `python -m unittest discover -s tests -p "test_*.py"`

Resultado histórico previo: `Ran 140 tests in 4.247s — OK`; sustituido por la suite final de esta corrección.

No se modificaron el prompt, schema, cutoff 0.55, siete artefactos, quality gate, política de intentos, rutas, contratos ni etapas 00–04. No se llamó a OpenAI.



## Corrección de resolución del runtime LLM — candidata final

### Causa raíz

`src/adapters/outline_generation_runtime.py` intentaba importar `llm_utils` y, como fallback, `src.llm_utils`. La estructura real del repositorio migrado no contiene `src/llm_utils.py`; por ello la ejecución real fallaba con `RUNTIME_DEPENDENCY_FAILED` antes de la primera llamada al LLM. Las pruebas anteriores no reproducían esta ausencia.

### Corrección limitada

Se modificó únicamente `src/adapters/outline_generation_runtime.py`. El runtime ahora reutiliza el patrón existente de los agentes cerrados: `load_runtime_credential("OPENAI_API_KEY", project_dir=...)`, `langchain_openai.ChatOpenAI`, `langchain_core.messages.HumanMessage`, `temperature=0` y el parser local `extract_first_valid_json` de `src/tools/outline_generation/response_parsing.py`. No se creó `src/llm_utils.py` ni otra dependencia ficticia.

No se modificaron prompt, schema, cutoff 0.55, validaciones, siete artefactos, rutas, quality gate, política de intentos ni etapas 00–04.

### Pruebas nuevas

`tests/v16/test_agent05_runtime_resolution_v16.py` valida:

- construcción de `build_openai_outline_runtime` sin `llm_utils` ni `src.llm_utils`;
- credencial común y `temperature=0`;
- parseo observable del primer JSON válido;
- `build_real_outline_execution` contra una estructura equivalente al repositorio real, sin `src/llm_utils.py`;
- llamada literal `build_real_outline_execution("/content/proyecto_estado_arte", attempt_number=1)`;
- ausencia de imports o rutas artificiales hacia `llm_utils`.

Las pruebas utilizan un stub controlado y no llaman a OpenAI.

### Suite final exacta

Comando: `python -m unittest discover -s tests -p "test_*.py"`

Resultado final: `Ran 144 tests in 4.317s — OK`.

### Reejecución después del fallo técnico

No debe ejecutarse `attempt_number=2`, porque el intento fallido no produjo `NEEDS_REVISION` ni una transición `RETRY`. Para validar nuevamente el Agente 05 aislado, se debe volver a ejecutar `AGENT05_ATTEMPT_NUMBER=1`. El `StateStore` puede comprometer un nuevo resultado del intento 1 sobre la misma etapa cuando no existe una ejecución pendiente. Si quedó `pending_execution` por una interrupción, primero debe ejecutarse el mecanismo común `RESUME`; no se debe editar manualmente el estado ni crear un segundo `pipeline_state.json`. El nuevo `COMPLETED` sustituirá el estado técnico fallido de la etapa y conservará el historial transaccional.
