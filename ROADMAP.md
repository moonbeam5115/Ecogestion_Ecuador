# EcoGestión EC — hoja de ruta técnica

## Objetivo

Crear una plataforma web para consultores ambientales y operadores empresariales de Ecuador que vincule cada **empresa** con sus **establecimientos o proyectos**, autorizaciones, obligaciones, períodos, evidencias, residuos, alertas y normativa de referencia. Debe facilitar el control documental, no sustituir a SUIA ni emitir determinaciones legales.

## MVP 0.1 — incluido en este paquete

- Registro de empresa, RUC y proyectos por establecimiento.
- Diagnóstico preliminar sin asignación automática de tipo de permiso.
- Documentos PDF de texto seleccionable y extracción por reglas con número de página; fragmentos aceptados/descartados por humano.
- Obligaciones manuales y provenientes de documentos, fechas explícitas y evidencia revisada.
- Semáforo de alertas al abrir la aplicación.
- Bitácora piloto de generación/movimientos de residuos con campos de trazabilidad y CSV.
- Datos ficticios explícitos para explorar la interfaz.

## MVP 0.2 — antes de una prueba piloto con clientes

1. **Ciclos de obligación**. Separar la obligación legal de sus instancias por período (e.g. monitoreo anual de 2027 vs 2028). No basta con marcar una sola obligación como cumplida eternamente.
2. **Permisos y RGDP**. Crear objetos de autorización ambiental diferenciados del Registro de Generador de Residuos y Desechos Peligrosos y Especiales. Mantener fechas, estado, organismo, documentos y modificaciones.
3. **Residuos**. Modelar inventario: generación, entradas, almacenamiento, salidas y actas; asociar archivos a manifiestos; evitar sumar un mismo residuo dos veces; validar unidades y códigos con el catálogo oficial vigente.
4. **Normas versionadas**. Registrar fuente, organismo, artículo, URL oficial, vigencia, versión, fechas de consulta y ámbito territorial. Las reglas no deben surgir solo de un LLM.
5. **Prueba documental**. Obtener 3–5 PDFs ficticios o anonimizados revisados por especialista ambiental y medir precisión/recobrado de obligaciones sugeridas frente a un estándar de referencia.

## Fase 1 — plataforma multiusuario

- Backend API (FastAPI) y PostgreSQL; migraciones con Alembic.
- Usuarios, empresas clientes, roles (administrador, consultor, operador, revisor, solo lectura) y aislamiento por cliente.
- Control de acceso por empresa/proyecto; cifrado de documentos, respaldos, retención; bitácora de auditoría resistente a cambios.
- Alertas programadas (email) con permisos y consentimiento, reintentos y prevención de mensajes duplicados.
- Seguimiento de compromisos y no conformidades; historial completo de decisiones.

## Fase 2 — IA documental asistida

- OCR para PDFs escaneados; extracción estructurada con texto/página precisos, clasificación de documento y normalización de frecuencias.
- Aprobación obligatoria; mostrar evidencia y confianza calibrada por categoría, identificar incertidumbre, contradicciones y documentos vencidos.
- Evaluaciones automáticas reproducibles con un conjunto de PDFs etiquetados por expertos.
- No usar resultados generativos como determinación legal ni calcular fechas a partir de una frase ambigua.

## Fase 3 — expansión

- Módulo de monitoreos (agua/aire/emisiones/ruido/suelo) con puntos de muestra, parámetros, métodos, laboratorios, límites y documentos.
- Auditorías e informes; hallazgos, acciones correctivas, responsables, plazos y trazabilidad.
- Reportes editables; exportaciones con formatos oficiales verificados y actualizados.
- Integración SUIA únicamente con métodos oficiales y permitidos; en ausencia de integración, vinculación manual a expedientes.

## Criterios de aceptación del piloto

- Se puede crear una empresa y al menos dos establecimientos sin mezclarlos.
- Un PDF se archiva y cada fragmento candidato muestra documento y página fuente.
- Nada se convierte en obligación sin aprobación humana y las fechas faltantes permanecen sin inventar.
- Una obligación no puede marcarse completada sin documento de evidencia revisado.
- Las alertas distinguen vencido, 7 días, 30 días y sin fecha.
- El registro de residuos lleva empresa/proyecto, fecha, tipo, cantidad, almacenamiento, gestor, referencia de manifiesto y destino.
- La plataforma no afirma que un diagnóstico constituye autorización o dictamen oficial.

## Riesgos

Un usuario no debe cargar datos reales confidenciales en este prototipo local sin controles de seguridad adecuados. Aún no incluye autenticación, cifrado en reposo, backups automatizados, versiones regulatorias, ni integración oficial.
