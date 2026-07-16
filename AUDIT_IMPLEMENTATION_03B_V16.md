# CANDIDATA 03B V1.6 PARA VALIDACIÓN REAL

## Implementación

03B se implementó como `QuantitativeExtractionCapability`, no como agente autónomo. Reutiliza los contratos, estado, fingerprints, escritura atómica, credenciales, configuración común y bootstrap de la candidata del Agente 03.

## Límites

- `attempt_number=1` únicamente.
- Nueve nombres de artefactos congelados.
- Transición exitosa `ADVANCE` con `target_stage=null`.
- Sin importación ni ejecución de 04.
- Sin integración dentro de `ExtractionAgent`.
- Ground Truth, conocimiento externo, secciones de revisión y bibliografía declarados como no usados.
- Umbrales de calidad todavía provisionales y sin valores científicos aprobados.

## Validación

Las pruebas unitarias y controladas usan doubles identificados. No se afirma que OpenAI real haya sido validado en este contenedor. La ejecución real externa queda pendiente para Colab.
