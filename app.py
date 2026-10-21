"""EcoGestión EC | prototype dashboard. Run with `streamlit run app.py`."""
from __future__ import annotations

import hashlib
import io
import json
import re
import sqlite3
import uuid
from datetime import date
from pathlib import Path

import streamlit as st
from pypdf import PdfReader

from database import DATA_DIR, UPLOAD_DIR, fetch_all, fetch_one, initialize, insert, seed_demo, update
from logic import alert_status, diagnosis_summary, extract_candidates

st.set_page_config(page_title='EcoGestión EC · Prototipo', page_icon='🌿', layout='wide')
initialize()
st.markdown('''
<style>
  .block-container {padding-top:1.6rem; max-width:1240px}
  h1, h2, h3 {letter-spacing:-.035em}
  [data-testid="stMetric"] {background:#f7f8f5; border:1px solid #e1e6df;
    padding:13px 16px; border-radius:12px;}
  .eyebrow {letter-spacing:.09em; text-transform:uppercase; color:#6d8274; font-size:.77rem; font-weight:700}
  .tag {display:inline-block; border:1px solid #cad4c9; padding:3px 9px; border-radius:50px;
    font-size:.8rem; color:#45654c; margin-bottom:6px}
</style>
''', unsafe_allow_html=True)

SECTIONS = ['📊 Panel general', '🏢 Empresas y proyectos', '📝 Diagnóstico',
            '📄 Documentos / extracción', '📋 Obligaciones y evidencias',
            '🔔 Alertas', '♻️ Residuos', '📈 Reporte ejecutivo', 'ℹ️ Alcance y seguridad']
QUESTIONS = [
    'Residuos peligrosos', 'Residuos especiales', 'Emisiones atmosféricas',
    'Descargas de agua', 'Fuentes fijas', 'Ruido', 'Sustancias químicas',
    'Almacenamiento de combustibles', 'Monitoreos ambientales',
    'Obligaciones pendientes', 'Plan de Manejo Ambiental',
]
STATUS_ICONS = {'Vencida':'🔴','0–7 días':'🟠','8–30 días':'🟡',
                'Cumplida':'🟢','Sin fecha':'⚪','En plazo':'🔵'}


def title(name, subtitle):
    st.markdown('<div class="eyebrow">ECOGESTIÓN EC · MVP LOCAL</div>', unsafe_allow_html=True)
    st.title(name)
    st.caption(subtitle)


def companies():
    return fetch_all('SELECT * FROM companies ORDER BY legal_name')


def sites():
    return fetch_all('''SELECT s.*, c.legal_name, c.ruc FROM sites s
                        JOIN companies c ON c.id=s.company_id ORDER BY c.legal_name,s.name''')


def obligations(site_id=None):
    sql = '''SELECT o.*, s.name AS site_name, c.legal_name FROM obligations o
             JOIN sites s ON s.id=o.site_id JOIN companies c ON c.id=s.company_id'''
    if site_id:
        return fetch_all(sql+' WHERE o.site_id=? ORDER BY o.due_date IS NULL,o.due_date,o.id', (site_id,))
    return fetch_all(sql+' ORDER BY o.due_date IS NULL,o.due_date,o.id')


def save_upload(upload, directory):
    if len(upload.getvalue()) > 25 * 1024 * 1024:
        raise ValueError('El límite por archivo es 25 MB en este prototipo.')
    suffix = Path(upload.name).suffix.lower()
    if suffix not in ('.pdf', '.png', '.jpg', '.jpeg'):
        raise ValueError('Formato no permitido.')
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'{uuid.uuid4().hex}{suffix}'
    path.write_bytes(upload.getvalue())
    return path


def selected_site(label='Proyecto / establecimiento'):
    all_sites = sites()
    if not all_sites:
        st.info('Primero registra una empresa y, después, un proyecto o establecimiento.')
        return None
    site_names = {s['id']: f"{s['legal_name']} · {s['name']} (#{s['id']})" for s in all_sites}
    site_id = st.selectbox(label, options=list(site_names), format_func=lambda i: site_names[i])
    return next(s for s in all_sites if s['id'] == site_id)


with st.sidebar:
    st.markdown('## 🌿 EcoGestión EC')
    st.caption('Gestión ambiental · Ecuador')
    section = st.radio('Navegación', SECTIONS, label_visibility='collapsed')
    st.divider()
    st.caption('🧪 DEMO LOCAL · Los datos de ejemplo son ficticios. No consulta SUIA ni determina obligaciones legales.')
    if st.button('🧪 Cargar datos ficticios', use_container_width=True):
        if seed_demo():
            st.success('Ejemplo creado. Ve a Panel general.')
        else:
            st.info('El ejemplo ya existe.')


if section == SECTIONS[0]:
    title('Panel de cumplimiento', 'Vista para consultores y operadores: datos ficticios del piloto; no certifica el cumplimiento legal.')
    all_companies, all_sites, all_obligations = companies(), sites(), obligations()
    counts = {k: 0 for k in STATUS_ICONS}
    for item in all_obligations:
        counts[alert_status(item['due_date'], bool(item['completed']))] += 1
    c1,c2,c3,c4 = st.columns(4)
    c1.metric('Empresas', len(all_companies))
    c2.metric('Establecimientos', len(all_sites))
    c3.metric('Obligaciones', len(all_obligations))
    c4.metric('Vencidas', counts['Vencida'])
    c1,c2,c3,c4 = st.columns(4)
    c1.metric('🔴 Vencidas',counts['Vencida'])
    c2.metric('🟠 Próximos 7 días',counts['0–7 días'])
    c3.metric('🟡 Próximos 30 días',counts['8–30 días'])
    c4.metric('🟢 Cumplidas',counts['Cumplida'])
    st.subheader('Próximas obligaciones')
    rows = []
    for o in all_obligations:
        state = alert_status(o['due_date'], bool(o['completed']))
        rows.append({'Estado':STATUS_ICONS[state]+' '+state, 'Empresa':o['legal_name'],
                     'Proyecto':o['site_name'], 'Obligación':o['title'],
                     'Vence':o['due_date'] or 'Sin definir', 'Responsable':o['responsible']})
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info('Aún no hay obligaciones. Puedes usar datos de ejemplo o registrar una empresa.')
    st.caption('Una obligación completada cuenta como cumplida únicamente cuando tiene evidencia revisada y se confirma manualmente.')
    st.info('🎬 **Ruta de la demo:** Empresas y proyectos → Documentos / extracción → Obligaciones y evidencias → Alertas → Residuos → Reporte ejecutivo. La carga ficticia crea 2 empresas, 3 instalaciones y fragmentos pendientes de revisión.')

elif section == SECTIONS[1]:
    title('Empresas y proyectos', 'Una empresa puede tener varias instalaciones o proyectos con obligaciones diferentes.')
    tab1,tab2,tab3 = st.tabs(['Registrar empresa','Registrar proyecto / instalación','Directorio'])
    with tab1:
        with st.form('new_company', clear_on_submit=True):
            ruc = st.text_input('RUC (13 dígitos para registros reales)')
            legal = st.text_input('Razón social *')
            trade = st.text_input('Nombre comercial')
            rep = st.text_input('Representante legal')
            email = st.text_input('Correo de contacto')
            ok = st.form_submit_button('Guardar empresa', type='primary')
            if ok:
                if not re.fullmatch(r'\d{13}', ruc.strip()):
                    st.error('Para empresas reales, introduce un RUC de 13 dígitos (sin verificar validez ante SRI).')
                elif not legal.strip():
                    st.error('Introduce la razón social.')
                else:
                    try:
                        new_id = insert('''INSERT INTO companies(ruc,legal_name,trade_name,legal_representative,email)
                          VALUES(?,?,?,?,?)''',(ruc.strip(),legal.strip(),trade.strip(),rep.strip(),email.strip()),
                          'Empresa creada','company')
                        st.success(f'Empresa registrada (ID {new_id}).')
                    except sqlite3.IntegrityError:
                        st.error('Este RUC ya está registrado.')
    with tab2:
        comps = companies()
        if not comps:
            st.info('Primero crea una empresa.')
        else:
            comp_dict = {x['id']: x['legal_name'] for x in comps}
            with st.form('new_site', clear_on_submit=True):
                cid = st.selectbox('Empresa *', list(comp_dict), format_func=lambda i: comp_dict[i])
                name = st.text_input('Nombre del proyecto / establecimiento *')
                activity = st.text_area('Actividad real (descripción operativa)')
                x1,x2 = st.columns(2)
                ciiu = x1.text_input('CIIU (declarado, sin validación automática)')
                permit = x2.selectbox('Autorización existente (si conoce)',
                     ['Sin determinar','Certificado Ambiental','Registro Ambiental','Licencia Ambiental'])
                x1,x2 = st.columns(2)
                province = x1.text_input('Provincia')
                canton = x2.text_input('Cantón')
                address = st.text_input('Dirección')
                x1,x2,x3,x4 = st.columns(4)
                lat = x1.text_input('Latitud (opcional)')
                lon = x2.text_input('Longitud (opcional)')
                workers = x3.number_input('Trabajadores',0,1_000_000,0)
                area = x4.number_input('Área m²',0.0,100_000_000.0,0.0)
                suia = st.text_input('Código o referencia SUIA (si existe)')
                submitted = st.form_submit_button('Guardar proyecto',type='primary')
                if submitted:
                    try:
                        latitude = float(lat) if lat.strip() else None
                        longitude = float(lon) if lon.strip() else None
                        if latitude is not None and not -90 <= latitude <= 90: raise ValueError('Latitud fuera de rango')
                        if longitude is not None and not -180 <= longitude <= 180: raise ValueError('Longitud fuera de rango')
                        if not name.strip(): raise ValueError('Falta el nombre del proyecto')
                        new_id = insert('''INSERT INTO sites(company_id,name,activity,ciiu,province,canton,address,
                           latitude,longitude,workers,area_m2,permit_type,suia_code)
                           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                           (cid,name,activity,ciiu,province,canton,address,latitude,longitude,
                            workers,area,permit,suia),'Proyecto creado','site')
                        st.success(f'Proyecto guardado (ID {new_id}).')
                    except ValueError as e:
                        st.error(f'Revisa los datos: {e}')
    with tab3:
        st.subheader('Empresas')
        st.dataframe(comps if (comps:=companies()) else [],hide_index=True,use_container_width=True)
        st.subheader('Establecimientos')
        st.dataframe(sites(),hide_index=True,use_container_width=True)

elif section == SECTIONS[2]:
    title('Diagnóstico ambiental', 'Cuestionario preliminar: indicadores para revisión profesional, no categorización automática.')
    site = selected_site()
    if site:
        st.warning('La clasificación ambiental oficial debe verificarse en SUIA y contra la normativa aplicable al proyecto específico.')
        latest = fetch_one('SELECT * FROM diagnostics WHERE site_id=? ORDER BY id DESC LIMIT 1',(site['id'],))
        if latest:
            old = json.loads(latest['responses_json'])
            summ = diagnosis_summary(old)
            st.caption(f"Último registro: {latest['created_at']} · {summ['positive_count']} respuestas Sí · {summ['unknown_count']} respuestas No sé")
        with st.form('diag_form'):
            st.subheader('Condiciones ambientales de la operación')
            answers = {}
            for q in QUESTIONS:
                answers[q] = st.selectbox(f'¿Presenta: {q.lower()}?', ['No sé','Sí','No'],key='diag_'+q)
            observations = st.text_area('Observaciones / preguntas para el consultor')
            save = st.form_submit_button('Guardar diagnóstico',type='primary')
            if save:
                insert('INSERT INTO diagnostics(site_id,responses_json,observations) VALUES(?,?,?)',
                       (site['id'],json.dumps(answers,ensure_ascii=False),observations),
                       'Diagnóstico registrado','diagnosis')
                result = diagnosis_summary(answers)
                st.success(f"Diagnóstico guardado. {result['positive_count']} condiciones presentes y {result['unknown_count']} por aclarar.")
                st.info(result['status'])

elif section == SECTIONS[3]:
    title('Documentos y extracción', 'Extracción de texto por reglas: los fragmentos son candidatos y requieren confirmación humana.')
    site = selected_site()
    if site:
        st.info('Admite PDF con texto seleccionable. Este MVP no incluye OCR, IA generativa ni conexión a SUIA.')
        with st.form('upload_pdf',clear_on_submit=True):
            kind = st.selectbox('Tipo de documento',['Registro Ambiental','Licencia Ambiental',
                'Certificado Ambiental','Plan de Manejo Ambiental','Informe','Otro'])
            upload = st.file_uploader('Subir PDF (máximo 25 MB)',type=['pdf'])
            submitted = st.form_submit_button('Subir y analizar',type='primary')
            if submitted:
                if upload is None:
                    st.error('Selecciona un PDF.')
                elif len(upload.getvalue())>25*1024*1024:
                    st.error('Límite: 25 MB.')
                else:
                    digest = hashlib.sha256(upload.getvalue()).hexdigest()
                    existing = fetch_one('SELECT id FROM documents WHERE sha256=? AND site_id=?',
                                         (digest,site['id']))
                    if existing:
                        st.warning(f'Este PDF ya se registró (documento #{existing["id"]}).')
                    else:
                        try:
                            reader = PdfReader(io.BytesIO(upload.getvalue()))
                            pages = [(p.extract_text() or '') for p in reader.pages[:150]]
                            path = save_upload(upload,UPLOAD_DIR / 'documents')
                            doc_id = insert('''INSERT INTO documents(site_id,filename,document_type,
                              stored_path,sha256,page_count) VALUES(?,?,?,?,?,?)''',
                              (site['id'],Path(upload.name).name,kind,str(path),digest,len(reader.pages)),
                              'PDF cargado','document')
                            proposals = extract_candidates(pages,limit=60)
                            for entry in proposals:
                                insert('''INSERT INTO candidates(site_id,document_id,page_number,snippet,
                                  suggested_frequency) VALUES(?,?,?,?,?)''',
                                  (site['id'],doc_id,entry['page_number'],entry['snippet'],entry['suggested_frequency']))
                            st.success(f'Documento guardado. {len(proposals)} fragmentos candidatos encontrados.')
                            if len(reader.pages)>150: st.warning('Solo se analizaron las primeras 150 páginas.')
                            if not any(p.strip() for p in pages):
                                st.warning('No se extrajo texto. Parece escaneado o protegido; requiere OCR externo.')
                        except Exception as e:
                            st.error(f'No se pudo procesar el PDF: {type(e).__name__}. Comprueba que el archivo no esté cifrado o dañado.')
        st.subheader('Documentos del proyecto')
        docs = fetch_all('''SELECT id,filename,document_type,page_count,created_at FROM documents
                            WHERE site_id=? ORDER BY id DESC''',(site['id'],))
        st.dataframe(docs,use_container_width=True,hide_index=True)
        st.subheader('Fragmentos pendientes de revisión')
        candidates = fetch_all('''SELECT c.*,d.filename FROM candidates c JOIN documents d ON d.id=c.document_id
                                 WHERE c.site_id=? AND c.review_status='Por revisar'
                                 ORDER BY c.id DESC LIMIT 60''',(site['id'],))
        if not candidates:
            st.caption('No hay fragmentos pendientes. Puedes crear obligaciones manualmente en el módulo correspondiente.')
        for candidate in candidates:
            with st.expander(f"PDF #{candidate['document_id']} · pág. {candidate['page_number']} · {candidate['suggested_frequency']} · fragmento #{candidate['id']}"):
                st.caption(candidate['filename'])
                st.write(candidate['snippet'])
                st.warning('Un fragmento no implica necesariamente una obligación. Revisa el contexto, vigencia y aplicabilidad.')
                with st.form('candidate_form_'+str(candidate['id'])):
                    title_value = st.text_input('Título de obligación (revisado) *',key='cand_title_'+str(candidate['id']))
                    frequency = st.selectbox('Frecuencia confirmada',
                        ['Sin especificar','Única','Diaria','Semanal','Mensual','Trimestral','Semestral','Anual','Continua','Otra'],
                        index=(['Sin especificar','Única','Diaria','Semanal','Mensual','Trimestral','Semestral','Anual','Continua','Otra'].index(candidate['suggested_frequency']) if candidate['suggested_frequency'] in ['Sin especificar','Única','Diaria','Semanal','Mensual','Trimestral','Semestral','Anual','Continua','Otra'] else 0),
                        key='cand_freq_'+str(candidate['id']))
                    known_due = st.checkbox('Fecha de vencimiento confirmada',key='cand_chk_'+str(candidate['id']))
                    due = st.date_input('Fecha confirmada',value=date.today(),disabled=not known_due,key='cand_date_'+str(candidate['id']))
                    responsible = st.text_input('Responsable',key='cand_resp_'+str(candidate['id']))
                    evidence_type = st.text_input('Evidencia requerida',key='cand_ev_'+str(candidate['id']))
                    a,b = st.columns(2)
                    approve = a.form_submit_button('Aceptar obligación',type='primary')
                    reject = b.form_submit_button('Descartar fragmento')
                    if approve:
                        if not title_value.strip():
                            st.error('Introduce un título validado por una persona.')
                        else:
                            insert('''INSERT INTO obligations(site_id,source_document_id,source_page,title,
                              details,frequency,due_date,responsible,evidence_required)
                              VALUES(?,?,?,?,?,?,?,?,?)''',
                              (site['id'],candidate['document_id'],candidate['page_number'],title_value.strip(),
                               candidate['snippet'],frequency,due.isoformat() if known_due else None,
                               responsible,evidence_type),'Obligación validada','obligation')
                            update('UPDATE candidates SET review_status=? WHERE id=?',('Aceptada',candidate['id']))
                            st.success('Obligación registrada con referencia a la página del PDF.')
                            st.rerun()
                    elif reject:
                        update('UPDATE candidates SET review_status=? WHERE id=?',('Descartada',candidate['id']))
                        st.rerun()

elif section == SECTIONS[4]:
    title('Obligaciones y evidencias', 'El responsable valida fechas, carga evidencias y marca como cumplido después de revisarlas.')
    site = selected_site()
    if site:
        with st.expander('➕ Añadir obligación manualmente',expanded=False):
            with st.form('new_obligation',clear_on_submit=True):
                obligation_name = st.text_input('Obligación *')
                detail = st.text_area('Descripción o fundamento')
                freq = st.selectbox('Frecuencia',['Sin especificar','Única','Diaria','Semanal','Mensual','Trimestral','Semestral','Anual','Continua','Otra'])
                date_confirmed = st.checkbox('Conozco la fecha de vencimiento')
                due = st.date_input('Fecha confirmada',value=date.today(),disabled=not date_confirmed)
                responsible = st.text_input('Responsable')
                required = st.text_input('Evidencia que se requiere')
                save = st.form_submit_button('Guardar obligación',type='primary')
                if save:
                    if obligation_name.strip():
                        insert('''INSERT INTO obligations(site_id,title,details,frequency,due_date,responsible,evidence_required)
                                  VALUES(?,?,?,?,?,?,?)''',(site['id'],obligation_name.strip(),detail,freq,
                                    due.isoformat() if date_confirmed else None,responsible,required),
                               'Obligación manual creada','obligation')
                        st.success('Guardada; no se ha calculado una fecha sin fundamento.')
                    else:
                        st.error('La obligación debe tener un título.')
        obs = obligations(site['id'])
        if not obs:
            st.info('Todavía no hay obligaciones para este proyecto.')
        else:
            st.dataframe([{'ID':o['id'],'Obligación':o['title'],'Frecuencia':o['frequency'],
                'Vence':o['due_date'] or 'Sin definir',
                'Estado':STATUS_ICONS[alert_status(o['due_date'],bool(o['completed']))]+' '+alert_status(o['due_date'],bool(o['completed'])),
                'Responsable':o['responsible'], 'Fuente':f"PDF #{o['source_document_id']} p.{o['source_page']}" if o['source_document_id'] else 'Manual'}
                for o in obs],hide_index=True,use_container_width=True)
            names = {o['id']:f"#{o['id']} · {o['title']}" for o in obs}
            oid = st.selectbox('Selecciona una obligación para gestionar',list(names),format_func=lambda x:names[x])
            current = next(x for x in obs if x['id']==oid)
            with st.expander('Actualizar fecha y responsable',expanded=False):
                with st.form('update_obligation'):
                    x1,x2 = st.columns(2)
                    has_due = x1.checkbox('Fecha de vencimiento definida',value=bool(current['due_date']))
                    from datetime import date as _date
                    value = _date.fromisoformat(current['due_date']) if current['due_date'] else date.today()
                    change_due = x2.date_input('Fecha',value=value,disabled=not has_due)
                    edit_responsible = st.text_input('Responsable',value=current['responsible'])
                    update_now = st.form_submit_button('Guardar cambios')
                    if update_now:
                        update('UPDATE obligations SET due_date=?,responsible=? WHERE id=?',
                               (change_due.isoformat() if has_due else None,edit_responsible,oid),
                               'Datos de obligación actualizados','obligation',oid)
                        st.success('Actualizada.')
                        st.rerun()
            st.subheader('Evidencias')
            evid = fetch_all('SELECT * FROM evidence WHERE obligation_id=? ORDER BY id DESC',(oid,))
            for ev in evid:
                a,b = st.columns([5,1])
                a.write(f"📎 {ev['filename']} · {'Revisada' if ev['reviewed'] else 'Pendiente de revisión'}")
                if not ev['reviewed'] and b.button('Revisar',key='review_'+str(ev['id'])):
                    update('UPDATE evidence SET reviewed=1 WHERE id=?',(ev['id'],),
                           'Evidencia revisada','evidence',ev['id'])
                    st.rerun()
            with st.form('add_evidence',clear_on_submit=True):
                evidence_upload = st.file_uploader('Adjuntar evidencia (PDF, JPG, PNG; hasta 25 MB)',
                                  type=['pdf','jpg','jpeg','png'])
                reviewer_note = st.text_input('Nota de evidencia')
                save_ev = st.form_submit_button('Agregar evidencia')
                if save_ev:
                    if evidence_upload:
                        try:
                            location = save_upload(evidence_upload,UPLOAD_DIR/'evidence')
                            insert('''INSERT INTO evidence(obligation_id,filename,stored_path,reviewer_note)
                                VALUES(?,?,?,?)''',(oid,Path(evidence_upload.name).name,str(location),reviewer_note),
                                'Evidencia adjuntada','evidence')
                            st.success('Evidencia adjuntada. Un revisor debe marcarla como revisada.')
                            st.rerun()
                        except ValueError as e: st.error(str(e))
                    else: st.error('Selecciona un archivo.')
            reviewed = fetch_one('SELECT COUNT(*) AS n FROM evidence WHERE obligation_id=? AND reviewed=1',(oid,))['n']
            if current['completed']:
                st.success(f'Obligación marcada como cumplida. Evidencias revisadas: {reviewed}.')
                if st.button('Reabrir obligación'):
                    update('UPDATE obligations SET completed=0,completed_at=NULL WHERE id=?',(oid,),
                           'Obligación reabierta','obligation',oid)
                    st.rerun()
            else:
                if not reviewed:
                    st.info('Para confirmar cumplimiento, primero adjunta evidencia y marca al menos una como revisada.')
                if st.button('✅ Confirmar cumplimiento',disabled=(reviewed==0)):
                    update('UPDATE obligations SET completed=1,completed_at=CURRENT_TIMESTAMP WHERE id=?',
                           (oid,),'Obligación cumplida','obligation',oid)
                    st.rerun()
            st.caption('Las obligaciones recurrentes deben registrarse por período/ciclo. La fecha siguiente no se genera automáticamente.')

elif section == SECTIONS[5]:
    title('Alertas', 'Semáforo de vencimientos basado en fechas explícitamente confirmadas.')
    site = selected_site()
    if site:
        obs = obligations(site['id'])
        summary = {key:0 for key in STATUS_ICONS}
        rows=[]
        for o in obs:
            state=alert_status(o['due_date'],bool(o['completed']))
            summary[state]+=1
            rows.append({'Alerta':STATUS_ICONS[state]+' '+state,'Obligación':o['title'],
                'Vencimiento':o['due_date'] or 'No establecido','Responsable':o['responsible']})
        a,b,c,d=st.columns(4)
        a.metric('🔴 Vencida',summary['Vencida'])
        b.metric('🟠 0–7 días',summary['0–7 días'])
        c.metric('🟡 8–30 días',summary['8–30 días'])
        d.metric('🟢 Cumplida',summary['Cumplida'])
        st.dataframe(rows,hide_index=True,use_container_width=True)
        st.caption('Alertas visibles al abrir la aplicación. Envíos por email/WhatsApp aún NO implementados.')

elif section == SECTIONS[6]:
    title('Gestión de residuos', 'Bitácora piloto por proyecto para conectar generación, almacenamiento y trazabilidad.')
    site = selected_site()
    if site:
        st.warning('La selección de clasificación es declarativa. No se verifica autorización de gestores ni límites legales de almacenamiento.')
        with st.expander('➕ Registrar movimiento / generación',expanded=False):
            with st.form('new_waste',clear_on_submit=True):
                a,b=st.columns(2)
                generated = a.date_input('Fecha de generación',value=date.today())
                name = b.text_input('Tipo de residuo o desecho *')
                a,b,c=st.columns(3)
                code = a.text_input('Código de residuo (si aplica)')
                classification=b.selectbox('Clasificación',['Por determinar','Peligroso','Especial','No peligroso'])
                qty=c.number_input('Cantidad generada (kg)',min_value=0.0,step=1.0)
                storage=st.text_input('Almacenamiento / ubicación')
                a,b=st.columns(2)
                departure_enabled=a.checkbox('Registrar salida del almacenamiento')
                departure=b.date_input('Fecha de salida',value=date.today(),disabled=not departure_enabled)
                a,b=st.columns(2)
                manager=a.text_input('Gestor receptor')
                authorization=b.text_input('Número de autorización del gestor (no verificado)')
                a,b=st.columns(2)
                transporter=a.text_input('Transportista')
                destination=b.text_input('Destino / disposición final')
                a,b=st.columns(2)
                manifest=a.text_input('Número de manifiesto (si aplica)')
                disposition=b.text_input('Referencia del acta / evidencia de disposición final')
                a,b=st.columns(2)
                cost=a.number_input('Costo USD',min_value=0.0,step=1.0)
                notes=b.text_input('Observaciones')
                submitted=st.form_submit_button('Guardar registro',type='primary')
                if submitted:
                    if not name.strip() or qty <= 0:
                        st.error('Ingresa tipo de residuo y cantidad mayor que cero.')
                    elif departure_enabled and departure<generated:
                        st.error('La fecha de salida no puede anteceder a la de generación.')
                    else:
                        insert('''INSERT INTO waste_entries(site_id,generated_on,waste_name,waste_code,
                            classification,quantity_kg,storage_location,departure_on,manager_name,
                            manager_authorization,transporter,final_destination,manifest_number,
                            disposition_evidence,cost_usd,notes)
                            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                            (site['id'],generated.isoformat(),name,code,classification,qty,storage,
                             departure.isoformat() if departure_enabled else None,manager,authorization,
                             transporter,destination,manifest,disposition,cost,notes),
                            'Generación / movimiento de residuo registrado','waste')
                        st.success('Movimiento registrado.')
        records=fetch_all('SELECT * FROM waste_entries WHERE site_id=? ORDER BY generated_on DESC,id DESC',(site['id'],))
        total=sum(r['quantity_kg'] for r in records)
        costs=sum(r['cost_usd'] for r in records)
        a,b,c=st.columns(3)
        a.metric('Cantidad registrada',f'{total:,.1f} kg')
        b.metric('Costo registrado',f'$ {costs:,.2f}')
        c.metric('Movimientos',len(records))
        st.subheader('Bitácora')
        if records:
            st.dataframe([{'Fecha':r['generated_on'],'Residuo':r['waste_name'],
              'Clasificación':r['classification'],'Cantidad kg':r['quantity_kg'],
              'Almacenamiento':r['storage_location'],'Fecha salida':r['departure_on'],
              'Gestor':r['manager_name'],'Autorización gestor':r['manager_authorization'],
              'Transportista':r['transporter'],'Manifiesto':r['manifest_number'],
              'Destino':r['final_destination'],'Evidencia final':r['disposition_evidence'],
              'Costo USD':r['cost_usd']} for r in records],hide_index=True,use_container_width=True)
            st.download_button('Descargar CSV de movimientos',
                data=__import__('pandas').DataFrame(records).to_csv(index=False).encode('utf-8-sig'),
                file_name='residuos.csv',mime='text/csv')
        else:
            st.info('No hay movimientos registrados para este establecimiento.')
        st.caption('El total es la suma de cantidades registradas, NO el inventario disponible. Requiere un módulo posterior de balance de inventario para evitar duplicaciones.')

elif section == SECTIONS[7]:
    title('Reporte ejecutivo', 'Exportación de resumen gerencial del estado registrado. No constituye informe oficial.')
    rows = obligations()
    if rows:
        selected_company = st.selectbox('Filtrar empresa',
            ['Todas'] + sorted({o['legal_name'] for o in rows}))
        filtered = [o for o in rows if selected_company == 'Todas' or o['legal_name'] == selected_company]
        states = [alert_status(o['due_date'], bool(o['completed'])) for o in filtered]
        a,b,c,d = st.columns(4)
        a.metric('Obligaciones',len(filtered))
        b.metric('Vencidas',states.count('Vencida'))
        c.metric('Próximos 30 días',states.count('0–7 días')+states.count('8–30 días'))
        d.metric('Cumplidas',states.count('Cumplida'))
        report_rows = [{
            'Empresa':o['legal_name'], 'Establecimiento':o['site_name'],
            'Obligación':o['title'],'Frecuencia':o['frequency'],
            'Vencimiento':o['due_date'] or '',
            'Semáforo':alert_status(o['due_date'],bool(o['completed'])),
            'Responsable':o['responsible'],
            'Evidencia requerida':o['evidence_required'],
            'Procedencia':('PDF #'+str(o['source_document_id'])+', pág. '+str(o['source_page']))
                          if o['source_document_id'] else 'Registro manual',
        } for o in filtered]
        st.dataframe(report_rows,hide_index=True,use_container_width=True)
        import csv
        buf = io.StringIO()
        writer = csv.DictWriter(buf,fieldnames=list(report_rows[0]))
        writer.writeheader()
        writer.writerows(report_rows)
        st.download_button('📥 Descargar reporte CSV (Excel)',data=buf.getvalue().encode('utf-8-sig'),
                           file_name='ecogestion_reporte_demo.csv',mime='text/csv',type='primary')
        st.caption('El reporte describe registros internos, NO verifica vigencia normativa ni permisos.')
    else:
        st.info('Carga datos ficticios para mostrar un reporte de ejemplo.')

else:
    title('Alcance del prototipo', 'Capacidades actuales, límites y próximos pasos antes de operar con clientes.')
    st.markdown('''
**Incluido:** registro de empresas y proyectos; cuestionario de diagnóstico; carga de PDF textual;
extracción heurística de posibles cláusulas con página de origen; aceptación y descarte manual;
obligaciones con responsable y fecha verificada; evidencias con revisión; semáforo de alertas;
bitácora básica de residuos; datos de ejemplo y almacenamiento local SQLite.

**No incluido:** conexión a SUIA/SRI; categorización oficial; validación real de gestores;
OCR de PDFs escaneados; IA generativa; alertas automáticas por correo/WhatsApp;
control de versiones legales; autenticación, cifrado en reposo, roles y auditoría robusta;
renovaciones periódicas automáticas; reportes legales certificados.

**Seguridad:** los PDFs quedan en la carpeta local `data/uploads/` sin cifrado y SQLite en
`data/ecogestion.db`. No subas información sensible de clientes ni expongas el servidor a Internet.
Para pruebas, usa PDFs ficticios o debidamente anonimizados.

**Fuentes iniciales para validar con especialistas:** Reglamento al Código Orgánico del Ambiente,
SUIA y guías oficiales de sustancias y residuos. Este programa no constituye asesoría legal.
    ''')
    st.code('streamlit run app.py',language='bash')
    st.caption('Próxima fase: modelo de períodos, autorización de roles, motores de reglas versionadas y clasificación documental asistida por IA con citas obligatorias.')

