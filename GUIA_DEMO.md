# EcoGestión EC · Guía para una demostración de 5 minutos

**Versión:** 0.1.1-demo (21 octubre 2026)

## Opción A: demostrar sin instalar nada

1. Abre `DEMO_RAPIDA.html` en Google Chrome, Edge o Firefox.
2. Verás un panel ya poblado con **2 empresas, 3 instalaciones, 8 obligaciones**, 2 fragmentos de documento y 2 entradas de residuos: todo completamente ficticio.
3. Explora "Empresas y proyectos". Selecciona "Planta Cuenca" y observa el filtrado.
4. En "Documentos y revisión", usa **Revisar y aceptar** sobre el fragmento de página 2. Introduce un título y, si conoces una fecha para ese ejemplo, introdúcela. Sin fecha, seguirá como "Sin fecha".
5. Ve a "Obligaciones" y haz clic en **Gestionar** sobre la obligación creada. Selecciona un PDF o imagen *ficticio*, usa **Agregar referencia**, luego **Revisar** y finalmente **Confirmar cumplimiento**. Solo el nombre del archivo se guarda en el navegador: no se almacena el documento ni se envía a un servidor.
6. Consulta "Alertas" y "Reportes". Descarga el resumen CSV en tu ordenador.
7. Si quieres empezar desde cero, pulsa **Restaurar datos de demostración** en el menú izquierdo.

**Nota:** esta versión HTML es una maqueta interactiva y funcional para presentación rápida. Funciona completamente dentro del navegador y no tiene servidor. Los fragmentos PDF están precargados, no hay extracción de un PDF en el navegador. Los cambios se guardan localmente en el almacenamiento del navegador cuando el navegador lo permite; no se sincronizan ni se comparten.

## Opción B: prototipo con datos persistentes y carga real de PDF

En Windows, con Python 3.10+ ya instalado:

1. Extrae el ZIP y abre la carpeta `ecogestion_ec_mvp`.
2. Haz doble clic en **`INICIAR_EN_WINDOWS.bat`**. La primera ejecución crea el entorno e instala las dependencias, por lo que **requiere Internet**.
3. Abre la dirección local que muestre la consola (normalmente `http://localhost:8501`).
4. En el menú izquierdo, pulsa **🧪 Cargar datos ficticios**.
5. En "Documentos / extracción" selecciona "Planta Cuenca" y examina las **propuestas pendientes** ya cargadas, con nombre y página de origen. También puedes subir el PDF en `sample_docs/resolucion_ficticia_demo.pdf` a **otro** proyecto para probar el motor de extracción, o crear tu propio PDF ficticio de texto seleccionable.
6. Acepta un fragmento. Luego usa "Obligaciones y evidencias" para adjuntar `sample_docs/evidencia_ficticia.pdf`, marcarlo como revisado y confirmar el cumplimiento.
7. Visita "Reporte ejecutivo" y "Residuos" para descargar CSV.

También se puede lanzar en macOS/Linux: `python3 -m venv .venv`, activar el entorno, `python -m pip install -r requirements.txt`, `python -m streamlit run app.py`.

La versión Python **sí** guarda registros y archivos en SQLite y `data/uploads`, pero sigue siendo monousuario, sin autenticación ni cifrado, y no está lista para subirla a un servidor público o usar documentos confidenciales de clientes.

## Guion de venta / conversación con el colaborador

> "EcoGestión EC busca centralizar las empresas y sus establecimientos, sus compromisos ambientales, fechas, evidencias y bitácoras. El prototipo nos permite enseñar el flujo de un consultor: registrar el proyecto, revisar un documento con fragmentos de origen, aprobar manualmente las obligaciones, priorizar vencimientos y mantener registros para elaborar reportes. El siguiente paso es validar esto con un especialista ambiental, determinar el modelo de períodos y permisos, y definir el producto multiusuario. No estamos automatizando juicios legales ni reemplazando SUIA."

### Preguntas para validar

- ¿Qué módulo resolvería primero un dolor operativo real para un consultor o empresa: permisos, obligaciones, informes, residuos o vencimientos?
- ¿Qué campos faltan en la ficha de proyecto, obligación o manifiesto?
- ¿Qué documento real **anonimizado** podríamos usar para evaluar la extracción?
- ¿Las obligaciones se reportan por año, semestre, proyecto o por cada autorización?
- ¿Quién debe revisar/firmar una obligación y su evidencia?
- ¿Qué formato de exportación se necesita realmente?

### Fuera del alcance de esta demo

SUIA, SRI, verificación normativa, clasificación oficial, OCR de escaneos, IA documental, notificaciones externas, trabajo multiusuario, seguridad de producción, inventario de residuos con entradas/salidas y recurrencia automática de obligaciones.
