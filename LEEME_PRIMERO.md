# Sistema multiagente para generación y evaluación de estados del arte

Este repositorio contiene el código fuente reutilizable y las pruebas
automatizadas de una tesis de maestría orientada al diseño, implementación y
evaluación de un sistema multiagente basado en modelos de lenguaje grandes para
generar estados del arte a partir de artículos científicos proporcionados por
el usuario.

## Alcance del sistema

El pipeline completo comprende las etapas operativas 00–08:

```text
00  Orquestación y planificación
01  Ingesta y preparación documental
02  Extracción de información científica
03  Extracción y normalización cuantitativa
04  Análisis temático
05  Generación del esquema
06  Redacción del borrador
07  Verificación factual y trazabilidad
08  Evaluación global
```

Los notebooks operativos permanecen en Google Drive. Este repositorio contiene
la lógica migrada y reutilizable que sustenta esas etapas.

## Correspondencia entre etapas y código migrado

### Etapa 00 — Orquestación y planificación

Responsabilidades:

- preparar el experimento;
- resolver configuración común;
- registrar decisiones del pipeline;
- controlar fingerprints;
- aplicar PREPARE, EXECUTE, COMMIT y RESUME;
- conservar el estado transaccional.

Código principal:

```text
src/bootstrap/project_bootstrap.py
src/config/common_config.py
src/config/generation_policy_config.py
src/contracts/agent_input.py
src/contracts/agent_result.py
src/state/pipeline_state.py
src/state/state_store.py
src/state/fingerprints.py
src/io/atomic_write.py
src/io/credentials.py
```

### Etapa 01 — Ingesta y preparación documental

Responsabilidades:

- preparar los documentos del experimento;
- organizar texto y metadatos;
- producir chunks limpios;
- dejar disponibles los artefactos documentales usados por RAG.

La infraestructura común de esta etapa se apoya en:

```text
src/bootstrap/
src/config/
src/contracts/
src/io/
src/state/
```

La lógica operacional específica de ingesta continúa coordinada desde el
notebook correspondiente en Google Drive y sus artefactos del experimento.

### Etapa 02 — Extracción de información científica

Responsabilidades:

- recuperar contenido relevante;
- construir fichas científicas;
- extraer problema, métodos, datasets, resultados y limitaciones;
- validar la salida estructurada.

Código principal:

```text
src/agents/extraction_agent.py
src/adapters/extraction_runtime.py
src/runtime/extraction_protocol.py
src/tools/extraction/
```

### Etapa 03 — Extracción y normalización cuantitativa

Responsabilidades:

- identificar métricas y resultados numéricos;
- normalizar valores;
- vincular resultados cuantitativos con paper y chunk;
- producir tablas comparables para etapas posteriores.

Código principal:

```text
src/capabilities/quantitative_extraction.py
src/adapters/quantitative_extraction_runtime.py
src/runtime/quantitative_extraction_protocol.py
src/config/quantitative_extraction_policy_config.py
src/tools/quantitative/
```

### Etapa 04 — Análisis temático

Responsabilidades:

- agrupar métodos, datasets, resultados y limitaciones;
- identificar temas y subtemas;
- construir comparaciones;
- sugerir la estructura temática del estado del arte.

Código principal:

```text
src/agents/thematic_analysis_agent.py
src/adapters/thematic_analysis_runtime.py
src/runtime/thematic_analysis_protocol.py
src/config/thematic_analysis_policy_config.py
src/tools/thematic/
```

### Etapa 05 — Generación del esquema

Responsabilidades:

- transformar el análisis temático en una estructura coherente;
- ordenar secciones y subsecciones;
- definir objetivos y cobertura esperada;
- validar el esquema antes de redactar.

Código principal:

```text
src/agents/outline_generation_agent.py
src/adapters/outline_generation_runtime.py
src/runtime/outline_generation_protocol.py
src/config/outline_generation_policy_config.py
src/tools/outline/
```

### Etapa 06 — Redacción del borrador

Responsabilidades:

- generar cada sección del estado del arte;
- usar evidencia recuperada mediante RAG;
- conservar citas internas fuente–chunk;
- validar longitud, cobertura y calidad estructural;
- registrar trazas y manifiestos de generación.

Código principal:

```text
src/agents/draft_writing_agent.py
src/adapters/draft_writing_notebook.py
src/adapters/draft_writing_runtime.py
src/runtime/draft_writing_protocol.py
src/config/draft_writing_policy_config.py
src/tools/draft_writing/
```

### Etapa 07 — Verificación factual y trazabilidad

Responsabilidades:

- descomponer el borrador en claims;
- recuperar evidencia independiente;
- asignar veredictos;
- detectar riesgo factual y posibles alucinaciones;
- validar citas y números;
- construir la matriz de trazabilidad;
- generar propuestas de corrección o revisión manual.

Código principal:

```text
src/agents/verification_agent.py
src/adapters/agent06_verification_handoff.py
src/adapters/claim_verification_context.py
src/adapters/verification_notebook.py
src/adapters/verification_runtime.py
src/config/verification_policy_config.py
src/tools/verification/
```

### Etapa 08 — Evaluación global

Responsabilidades:

- comparar el estado del arte generado con un Ground Truth;
- calcular ROUGE-L, BERTScore y similitud semántica;
- aplicar una rúbrica mediante LLM Judge;
- calcular métricas factuales y de trazabilidad;
- detectar brechas temáticas;
- generar el reporte final y el manifiesto de evaluación.

Código migrado de soporte:

```text
src/adapters/evaluation_upstream.py
tests/evaluation/test_agent08_upstream_routing.py
```

La ejecución operacional del Agente 08 permanece en su notebook de Google Drive.

## Flujo activo de extremo a extremo

```text
00 Orquestación
        ↓
01 Ingesta
        ↓
02 Extracción científica
        ↓
03 Extracción cuantitativa
        ↓
04 Análisis temático
        ↓
05 Esquema
        ↓
06 Redacción
        ↓
07 Verificación y trazabilidad
        ↓
08 Evaluación
```

Por tanto, las etapas anteriores al 06 no fueron descartadas. También están
migradas y forman parte necesaria del pipeline completo.

## Decisión sobre el Agente 07C

La versión final no utiliza 07C como una etapa obligatoria.

Su propósito original era reverificar correcciones automáticas aplicadas por el
Agente 07:

```text
07 detecta y corrige
        ↓
07C reverifica la corrección
        ↓
08 evalúa
```

En el flujo final, las propuestas no aprobadas no se incorporan
automáticamente. Se conservan como recomendaciones trazables o casos de
revisión manual. Por eso la ruta principal es:

```text
07 verificación
        ↓
08 evaluación
```

El repositorio todavía conserva compatibilidad histórica con 07C en:

```text
src/adapters/agent07c_handoff.py
src/adapters/evaluation_upstream.py
tests/verification/
```

Esa compatibilidad no significa que 07C sea obligatorio. Su eliminación física
debe realizarse como una migración separada para no romper contratos ni pruebas
ya validadas.

## Organización actual del repositorio

```text
tesis-sistema-multiagente/
├── src/
│   ├── adapters/
│   ├── agents/
│   ├── bootstrap/
│   ├── capabilities/
│   ├── config/
│   ├── contracts/
│   ├── io/
│   ├── runtime/
│   ├── state/
│   └── tools/
├── tests/
│   ├── evaluation/
│   ├── fixtures/
│   ├── integration/
│   ├── v16/
│   ├── v17/
│   └── verification/
└── LEEME_PRIMERO.md
```

## Función de cada carpeta

### `src/adapters`

Integra notebooks, agentes, contratos y artefactos persistidos.

### `src/agents`

Contiene la lógica científica de los agentes migrados:

- extracción;
- análisis temático;
- generación de esquema;
- redacción;
- verificación.

### `src/bootstrap`

Prepara el proyecto y el entorno del experimento.

### `src/capabilities`

Contiene capacidades reutilizables, actualmente incluida la extracción
cuantitativa.

### `src/config`

Centraliza políticas, parámetros y configuración de las etapas.

### `src/contracts`

Define las estructuras comunes de entrada y salida:

- `AgentInput`;
- `AgentResult`.

### `src/io`

Implementa escritura atómica y acceso controlado a credenciales.

### `src/runtime`

Define protocolos de ejecución para las etapas migradas.

### `src/state`

Implementa:

- estado del pipeline;
- fingerprints;
- PREPARE;
- EXECUTE;
- COMMIT;
- RESUME.

### `src/tools`

Agrupa herramientas científicas especializadas por etapa.

### `tests`

Conserva pruebas unitarias, contractuales, de regresión e integración.

## Notebooks operativos

La organización acordada es:

```text
GitHub
├── src/
├── tests/
└── documentación

Google Drive
└── notebooks operativos 00–08

/content en Colab
└── clon temporal del repositorio para ejecutar
```

Reglas:

- GitHub es la fuente del código reutilizable y de las pruebas;
- Google Drive es la fuente de los notebooks operativos;
- `/content` es efímero y no debe contener cambios permanentes.

## Principales artefactos del pipeline

El sistema puede producir:

- memoria documental;
- chunks limpios para RAG;
- fichas científicas;
- base de conocimiento;
- tablas cuantitativas;
- análisis temático;
- esquema del estado del arte;
- borrador del estado del arte;
- reporte de verificación;
- matriz de trazabilidad;
- propuestas de corrección;
- reporte de alucinación o riesgo factual;
- reporte final de evaluación;
- manifiestos y fingerprints.

## Evaluación

### Métricas automáticas

- ROUGE-L;
- BERTScore;
- similitud semántica por fragmentos;
- similitud semántica global.

### LLM Judge

La rúbrica considera:

- coherencia;
- organización;
- profundidad crítica;
- calidad de síntesis;
- claridad argumentativa.

### Métricas factuales y de trazabilidad

- precisión factual;
- tasa de alucinación o riesgo factual;
- cobertura de evidencia;
- cobertura de trazabilidad;
- error de cita;
- error numérico.

Las citas internas siguen el formato:

```text
[archivo.pdf | chunk_id]
```

## Resultado del experimento de referencia

Para `experimento_paper_02`:

```text
Agente 07
- estado: PARTIAL
- claims verificados: 25
- claims con revisión manual pendiente: 12
- correcciones aceptadas: 0

Agente 08
- auditoría final: OK
- citas detectadas: 33
- error de cita: 0.0
- valores numéricos comprobados: 16
- error numérico: 0.0
```

El estado `PARTIAL` indica limitaciones factuales pendientes, no un fallo
técnico del pipeline.

## Ejecución de pruebas

Desde la raíz:

```bash
python -m pytest
```

Pruebas por área:

```bash
python -m pytest tests/evaluation
python -m pytest tests/verification
python -m pytest tests/v16
python -m pytest tests/v17
```

## Reglas de mantenimiento

No subir:

```text
__pycache__/
*.pyc
.pytest_cache/
.ipynb_checkpoints/
.env
```

La limpieza del repositorio no debe modificar el comportamiento observable de
los notebooks originales. Toda eliminación funcional o mejora requiere una
decisión independiente y pruebas de regresión.
