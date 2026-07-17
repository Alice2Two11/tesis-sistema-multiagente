# Agente 06 v1.6 — corrección de resolución de CHROMA_DIR

## Causa raíz verificada

La configuración heredada podía resolver `CHROMA_DIR` a `EXPERIMENT_DIR/04_chroma` únicamente porque la ruta existía. En el experimento real esa carpeta estaba vacía, mientras que la base persistente y la colección `reference_papers_chunks` estaban en `EXPERIMENT_DIR/04_chroma_index`.

El defecto no estaba en el nombre de la colección ni en la lógica RAG. El defecto era aceptar una carpeta como índice sin verificar `chroma.sqlite3` ni las colecciones realmente persistidas.

## Archivo productivo modificado

- `src/adapters/draft_writing_runtime.py`

Se añadió `resolve_chroma_dir()` con el orden aprobado:

1. ruta explícita de configuración, solo si es válida;
2. `EXPERIMENT_DIR/04_chroma_index`;
3. búsqueda controlada de `chroma.sqlite3` dentro del experimento.

Una candidata solo es válida cuando:

- es un directorio;
- contiene `chroma.sqlite3`;
- `list_collections()` contiene la colección esperada.

Una carpeta `04_chroma` vacía no es aceptada. Si ninguna ruta contiene la colección esperada se produce `CHROMA_COLLECTION_NOT_FOUND`. Si más de una ruta contiene la misma colección se produce `CHROMA_DIR_AMBIGUOUS`.

No se crea, copia, mueve ni elimina ningún índice o colección.

## Manifiesto Chroma heredado

El experimento real no contiene el manifiesto en la ruta heredada. Por ello:

- `chroma_index_manifest.json` no se convierte en dependencia obligatoria;
- si existe, se conservan todas sus validaciones previas;
- si no existe, la validez operativa del índice se comprueba directamente contra la base persistente y la colección esperada;
- las comprobaciones de seguridad sobre `chunks_clean_for_rag.csv` permanecen activas.

Archivo ajustado para esta compatibilidad:

- `src/tools/draft_writing/input_validation.py`

## Comportamiento preservado

No se modificaron:

- RAG restringido a `papers_to_use`;
- Chroma → fallback CSV;
- prompt;
- schema;
- formato de citas;
- reintentos internos;
- normalización determinista;
- validación global;
- doce artefactos;
- rutas de salida;
- contratos;
- etapas 00–05;
- Agente 07.

## Pruebas nuevas

`tests/v16/test_agent06_chroma_dir_resolution_v16.py` comprueba:

- `04_chroma` vacía;
- `04_chroma_index` con `reference_papers_chunks`;
- selección correcta de `04_chroma_index`;
- ausencia de la colección esperada;
- múltiples rutas válidas y ambigüedad;
- colección con nombre incorrecto;
- carga de configuración sin manifiesto Chroma obligatorio.

También se actualizó la integración controlada para reproducir la estructura real y comprobar que `build_real_draft_execution(..., attempt_number=1)` usa `04_chroma_index`.

## Reejecución

El fallo ocurrió antes de generación científica. Debe reejecutarse con `attempt_number = 1`. No corresponde usar intento 2, porque no existió `NEEDS_REVISION` científico ni transición `RETRY` producida por el redactor.

## Validación en contenedor

- OpenAI no fue llamado.
- Chroma real no fue abierto; las pruebas usan clientes controlados.
- Suite completa: 179 pruebas, OK.
- `REAL_EXTERNAL_COLAB_AGENT06_RETURN_CODE = NOT_EXECUTED_IN_CONTAINER`.
