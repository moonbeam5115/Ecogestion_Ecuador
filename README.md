# EcoGestión EC — prototipo funcional (MVP 0.1.1-demo)

Aplicación web **local**, en español, para modelar la gestión del cumplimiento ambiental de empresas en Ecuador. Creada como punto de partida de ingeniería: **no es un sistema certificado ni tiene conexión a SUIA**.

## Para una demo rápida con un colaborador (recomendado)

- **Sin Python:** abre **`DEMO_RAPIDA.html`** en un navegador. Tiene una interfaz visual e interactiva, datos ficticios, filtros, aprobación de fragmentos, gestión de compromisos, referencias de evidencias, residuos y descarga de CSV. Los documentos **no se procesan ni se guardan** en la versión HTML.
- **App funcional local (Python):** en Windows haz doble clic en **`INICIAR_EN_WINDOWS.bat`**, espera la instalación inicial y usa **`🧪 Cargar datos ficticios`** en la barra lateral. Usa `sample_docs/` para probar extracción de un PDF verdadero y adjuntar evidencia en la app.
- **Presentación:** consulta **`GUIA_DEMO.md`** para un guion de 5 minutos y preguntas de validación.

Los datos iniciales son **2 empresas ficticias, 3 establecimientos, 8 obligaciones y 2 registros de residuos**, además de fragmentos de un PDF de muestra para revisión.

## Qué hace

1. **Empresas**: RUC, razón social, representante, correo.
2. **Proyectos e instalaciones**: múltiples establecimientos por empresa; ubicación, actividad, CIIU, información referencial de permisos.
3. **Diagnóstico**: cuestionario de condiciones ambientales (residuos, emisiones, descargas, sustancias, ruido, etc.); **no** hace clasificación legal automática.
4. **PDF**: almacena PDFs, extrae texto seleccionable y propone fragmentos relacionados con posibles obligaciones, mostrando página y nombre del documento.
5. **Revisión humana**: un usuario acepta o descarta cada fragmento; puede definir frecuencia, fecha y responsable, sin fechas inventadas.
6. **Obligaciones**: entradas manuales, responsable, evidencia requerida, evidencia PDF/JPG/PNG, revisión y confirmación manual.
7. **Alertas en el panel**: vencida (rojo), 0–7 días (naranja), 8–30 días (amarillo), cumplida (verde), en plazo / sin fecha. **No hay notificaciones push ni correo todavía.**
8. **Residuos**: bitácora con residuos/código, cantidad, clasificación provisional, almacenaje, gestor, transportista, manifiesto, disposición final y costos; CSV descargable.
9. **Demo**: carga explícita de datos ficticios con dos empresas y tres establecimientos, sin mezclar con empresas reales.

## Cómo ejecutar (Windows 10/11, macOS, Linux)

Requiere **Python 3.10 o superior**. En Windows, PowerShell:

```powershell
cd ecogestion_ec_mvp
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Si PowerShell bloquea la activación, **no** cambies la política global: usa directamente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Si algún ajuste de pip ajeno al proyecto causa problemas, puedes intentar:

```powershell
.\.venv\Scripts\python.exe -m pip --isolated install -r requirements.txt
```

En macOS/Linux:

```bash
cd ecogestion_ec_mvp
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Abre la URL local que muestre Streamlit (habitualmente `http://localhost:8501`). En la barra lateral, pulsa **Cargar datos ficticios** para explorar los módulos sin datos de clientes.

### Pruebas

```bash
python -m pip install pytest
python -m pytest -q
```

## Estructura

```
ecogestion_ec_mvp/
  DEMO_RAPIDA.html      # Demo instantánea, sin dependencias (solo navegador)
  GUIA_DEMO.md         # Guion para reunión y limitaciones
  sample_docs/         # PDFs ficticios de prueba
  app.py               # UI Streamlit
  database.py          # tablas y consultas SQLite
  logic.py             # semáforo + fragmentos textuales
  requirements.txt
  tests/
  data/                # BD y PDFs locales (no subir a repositorios)
```

### Modelo de datos

```
Empresas 1 ─── N Proyectos/instalaciones
                     ├── N Diagnósticos
                     ├── N Documentos ── N Fragmentos pendientes
                     ├── N Obligaciones ── N Evidencias revisables
                     └── N Registros de residuos

Bitácora de actividad: eventos básicos (NO auditoría segura).
```

## Decisiones regulatorias importantes

- La autorización ambiental **no se infiere únicamente** del CIIU, el número de empleados o del cuestionario. Debe confirmarse según actividad, catálogo, ubicación y autoridad competente.
- Un PDF que menciona «anual» **no define automáticamente la fecha de vencimiento**. La fecha se introduce cuando un responsable puede fundamentarla.
- La extracción de PDF actual usa **reglas de palabras clave**, no IA. Puede omitir obligaciones o señalar texto que no corresponda a una obligación. Toda decisión debe validarse.
- Para residuos peligrosos/especiales, la obligación de tener registros, documentos, gestores y manifiestos debe contrastarse con el Reglamento al Código Orgánico del Ambiente y regulaciones vigentes, bajo supervisión profesional.
- Las obligaciones recurrentes requieren un modelo de **ciclos / períodos**: una sola fila no representa el cumplimiento anual de por vida. Es trabajo futuro.

## Fuentes normativas de partida

- [Reglamento al Código Orgánico del Ambiente (archivo del Ministerio)](https://www.ambiente.gob.ec/wp-content/uploads/downloads/2021/06/REGLAMENTO-AL-CODIGO-ORGANICO-DEL-AMBIENTE.pdf), especialmente artículos 625–626.
- [Repositorio oficial del Ministerio: preguntas frecuentes sobre residuos](https://sustanciasyresiduos.ambiente.gob.ec/faq/).
- [Repositorio oficial: Acuerdo Ministerial 026](https://sustanciasyresiduos.ambiente.gob.ec/producto/acuerdo-ministerial-no-026-procedimientos-para-registro-de-generadores-de-desechos-peligrosos-gestion-de-desechos-peligrosos-previo-al-licenciamiento-ambiental-y-para-el-transporte-de-materiales-pe/).

**Hay que verificar vigencia, reformas y exigencias locales antes de producción.**

## Limitaciones / seguridad

- Local y **de un solo usuario**; no tiene login, cifrado de datos en reposo, política de retención ni permisos.
- Los archivos y la base se guardan en `data/`. **No usar con información confidencial real ni publicar esta aplicación en Internet.**
- PDFs protegidos o escaneados pueden no extraer texto; no hay OCR. Máximo 25 MB por archivo, hasta 150 páginas analizadas, y hasta 60 fragmentos candidatos por PDF.
- No verifica RUC con SRI, no verifica autorizaciones de gestores y no se conecta a SUIA.
- Los campos de manifiesto y disposición final son **referencias textuales**, aún no adjuntos con validación de trazabilidad.
- La cantidad acumulada de residuos es el volumen de registros, no un saldo de inventario. Es necesario modelar entradas/salidas para inventario.
- Las fechas del semáforo no son notificaciones externas, y el estado “cumplida” refleja la revisión dentro de la herramienta, no una certificación de la autoridad.

## Camino a un producto comercial

**Fase 1:** Entrevistas con un consultor ambiental ecuatoriano; 3–5 documentos reales anonimizados (permiso, PMA, informe y manifiesto); corregir la taxonomía y estructura de obligaciones.

**Fase 2:** Migrar a API FastAPI + PostgreSQL; gestión de clientes multi-tenant, roles, cifrado, backups, auditoría inmutable y ciclos recurrentes.

**Fase 3:** Extracción semiestructurada con IA, citas exactas al documento, aprobación humana, evaluación de calidad contra un conjunto de datos revisado.

**Fase 4:** Notificaciones email/WhatsApp a través de servicios autorizados; calendario y reportes exportables; importación/sincronización con SUIA solo si hay un medio legal y técnico habilitado.

> Aviso: EcoGestión EC es un prototipo de desarrollo, no asesoría legal ni producto terminado.
