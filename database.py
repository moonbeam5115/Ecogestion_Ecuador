"""SQLite persistence for the local EcoGestión EC prototype.

This is intentionally single-user, local software, not a production SaaS backend.
"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get('ECOGESTION_DATA_DIR', str(BASE / 'data')))
DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR = DATA_DIR / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / 'ecogestion.db'


@contextmanager
def connect():
    db = sqlite3.connect(DB_PATH, timeout=20)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys = ON')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def initialize():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS companies (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ruc TEXT NOT NULL UNIQUE,
          legal_name TEXT NOT NULL,
          trade_name TEXT NOT NULL DEFAULT '',
          legal_representative TEXT NOT NULL DEFAULT '',
          email TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS sites (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          company_id INTEGER NOT NULL REFERENCES companies(id),
          name TEXT NOT NULL,
          activity TEXT NOT NULL DEFAULT '', ciiu TEXT NOT NULL DEFAULT '',
          province TEXT NOT NULL DEFAULT '', canton TEXT NOT NULL DEFAULT '',
          address TEXT NOT NULL DEFAULT '', latitude REAL, longitude REAL,
          workers INTEGER, area_m2 REAL,
          permit_type TEXT NOT NULL DEFAULT 'Sin determinar',
          suia_code TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS diagnostics (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          site_id INTEGER NOT NULL REFERENCES sites(id),
          responses_json TEXT NOT NULL,
          observations TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS documents (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          site_id INTEGER NOT NULL REFERENCES sites(id),
          filename TEXT NOT NULL, document_type TEXT NOT NULL,
          stored_path TEXT NOT NULL, sha256 TEXT NOT NULL,
          page_count INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS candidates (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          site_id INTEGER NOT NULL REFERENCES sites(id),
          document_id INTEGER NOT NULL REFERENCES documents(id),
          page_number INTEGER NOT NULL,
          snippet TEXT NOT NULL,
          suggested_frequency TEXT NOT NULL DEFAULT 'Sin especificar',
          review_status TEXT NOT NULL DEFAULT 'Por revisar'
            CHECK(review_status IN ('Por revisar', 'Aceptada', 'Descartada')),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS obligations (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          site_id INTEGER NOT NULL REFERENCES sites(id),
          source_document_id INTEGER REFERENCES documents(id),
          source_page INTEGER,
          title TEXT NOT NULL, details TEXT NOT NULL DEFAULT '',
          frequency TEXT NOT NULL DEFAULT 'Sin especificar',
          due_date TEXT, responsible TEXT NOT NULL DEFAULT '',
          evidence_required TEXT NOT NULL DEFAULT '',
          review_status TEXT NOT NULL DEFAULT 'Validada manualmente',
          completed INTEGER NOT NULL DEFAULT 0 CHECK(completed IN (0,1)),
          completed_at TEXT,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS evidence (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          obligation_id INTEGER NOT NULL REFERENCES obligations(id),
          filename TEXT NOT NULL, stored_path TEXT NOT NULL,
          reviewer_note TEXT NOT NULL DEFAULT '',
          reviewed INTEGER NOT NULL DEFAULT 0 CHECK(reviewed IN (0,1)),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS waste_entries (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          site_id INTEGER NOT NULL REFERENCES sites(id),
          generated_on TEXT NOT NULL,
          waste_name TEXT NOT NULL,
          waste_code TEXT NOT NULL DEFAULT '',
          classification TEXT NOT NULL DEFAULT 'Por determinar',
          quantity_kg REAL NOT NULL CHECK(quantity_kg >= 0),
          storage_location TEXT NOT NULL DEFAULT '',
          departure_on TEXT, manager_name TEXT NOT NULL DEFAULT '',
          manager_authorization TEXT NOT NULL DEFAULT '',
          transporter TEXT NOT NULL DEFAULT '',
          final_destination TEXT NOT NULL DEFAULT '',
          manifest_number TEXT NOT NULL DEFAULT '',
          disposition_evidence TEXT NOT NULL DEFAULT '',
          cost_usd REAL NOT NULL DEFAULT 0 CHECK(cost_usd >= 0),
          notes TEXT NOT NULL DEFAULT '',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS activity_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          event TEXT NOT NULL, target_type TEXT NOT NULL, target_id INTEGER NOT NULL,
          timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_obligations_site ON obligations(site_id);
        CREATE INDEX IF NOT EXISTS idx_obligations_due ON obligations(due_date);
        CREATE INDEX IF NOT EXISTS idx_waste_site ON waste_entries(site_id);
        ''')


def fetch_all(sql, params=()):
    with connect() as db:
        return [dict(row) for row in db.execute(sql, params).fetchall()]


def fetch_one(sql, params=()):
    with connect() as db:
        row = db.execute(sql, params).fetchone()
        return dict(row) if row else None


def insert(sql, params=(), event=None, target_type=None):
    with connect() as db:
        cur = db.execute(sql, params)
        new_id = cur.lastrowid
        if event and target_type:
            db.execute('INSERT INTO activity_log(event,target_type,target_id) VALUES(?,?,?)',
                       (event, target_type, new_id))
        return new_id


def update(sql, params=(), event=None, target_type=None, target_id=None):
    with connect() as db:
        db.execute(sql, params)
        if event and target_type and target_id:
            db.execute('INSERT INTO activity_log(event,target_type,target_id) VALUES(?,?,?)',
                       (event, target_type, target_id))


def seed_demo():
    '''Seed a coherent, explicitly fictitious walkthrough; safe to run repeatedly.'''
    from datetime import date, timedelta
    import hashlib

    with connect() as db:
        if db.execute("SELECT 1 FROM companies WHERE ruc='DEMO-000000000'").fetchone():
            return False
        today = date.today()
        cid = db.execute('''INSERT INTO companies(ruc,legal_name,trade_name,email)
            VALUES(?,?,?,?)''', ('DEMO-000000000', 'Andes Circular S.A. (FICTICIA)',
                                'Andes Circular', 'demo@ejemplo.invalid')).lastrowid
        sid1 = db.execute('''INSERT INTO sites(company_id,name,activity,province,canton,
            permit_type,suia_code) VALUES(?,?,?,?,?,?,?)''',
            (cid,'Planta Cuenca','Recuperación de materiales y almacenamiento',
             'Azuay','Cuenca','Sin determinar','REFERENCIA-DEMO-001')).lastrowid
        sid2 = db.execute('''INSERT INTO sites(company_id,name,activity,province,canton,
            permit_type) VALUES(?,?,?,?,?,?)''',
            (cid,'Centro logístico Guayaquil','Transporte y acopio (ficticio)',
             'Guayas','Guayaquil','Sin determinar')).lastrowid
        company2 = db.execute('''INSERT INTO companies(ruc,legal_name,trade_name,email)
            VALUES(?,?,?,?)''',('DEMO-000000001','Pacífico Textil Cía. Ltda. (FICTICIA)',
                              'Pacífico Textil','demo2@ejemplo.invalid')).lastrowid
        sid3 = db.execute('''INSERT INTO sites(company_id,name,activity,province,canton,
            permit_type) VALUES(?,?,?,?,?,?)''',
            (company2,'Taller Manta','Operación textil demostrativa','Manabí','Manta','Sin determinar')).lastrowid
        sample = [
          (sid1,'Monitoreo de ruido','Anual',5,'Equipo ambiental','Informe técnico',0),
          (sid1,'Informe de seguimiento','Semestral',24,'Consultora externa','Informe firmado',0),
          (sid1,'Registro de residuos','Mensual',-4,'Encargado ambiental','Bitácora',0),
          (sid1,'Capacitación de personal','Semestral',-12,'RR. HH.','Lista de asistencia',1),
          (sid2,'Verificación de almacenamiento','Mensual',3,'Coordinación logística','Lista de inspección',0),
          (sid2,'Actualización documental','Única',45,'Encargado de planta','Expediente',0),
          (sid3,'Revisión de descargas','Anual',-2,'Equipo ambiental','Informe',0),
          (sid3,'Inspección de planta','Mensual',18,'Jefatura técnica','Checklist',0),
        ]
        for site,title,freq,days,resp,evi,done in sample:
            oid = db.execute('''INSERT INTO obligations(site_id,title,frequency,due_date,
                responsible,evidence_required,completed,completed_at)
                VALUES(?,?,?,?,?,?,?,?)''',
                (site,title,freq,(today+timedelta(days=days)).isoformat(),resp,evi,done,
                 today.isoformat() if done else None)).lastrowid
            if done:
                sample_file = BASE / 'sample_docs' / 'evidencia_ficticia.pdf'
                if sample_file.exists():
                    db.execute('''INSERT INTO evidence(obligation_id,filename,stored_path,
                        reviewer_note,reviewed) VALUES(?,?,?,?,1)''',
                        (oid,sample_file.name,str(sample_file),
                         'Revisada como ejemplo de un flujo de aprobación ficticio.'))
        db.execute('''INSERT INTO waste_entries(site_id,generated_on,waste_name,
            classification,quantity_kg,storage_location,cost_usd,notes)
            VALUES(?,?,?,?,?,?,?,?)''',
            (sid1,today.isoformat(),'Aceite usado (FICTICIO)','Por determinar',
             850,'Bodega A',125,'No constituye clasificación legal'))
        db.execute('''INSERT INTO waste_entries(site_id,generated_on,waste_name,
            classification,quantity_kg,storage_location,cost_usd,notes)
            VALUES(?,?,?,?,?,?,?,?)''',
            (sid2,today.isoformat(),'Envases contaminados (FICTICIO)',
             'Por determinar',125,'Bodega logística',35,'Ejemplo no verificado'))
        sample_pdf = BASE / 'sample_docs' / 'resolucion_ficticia_demo.pdf'
        if sample_pdf.exists():
            document_id = db.execute('''INSERT INTO documents(site_id,filename,document_type,
                stored_path,sha256,page_count) VALUES(?,?,?,?,?,?)''',
                (sid1,sample_pdf.name,'Otro',str(sample_pdf),
                 hashlib.sha256(sample_pdf.read_bytes()).hexdigest(),2)).lastrowid
            db.execute('''INSERT INTO candidates(site_id,document_id,page_number,snippet,
                suggested_frequency) VALUES(?,?,?,?,?)''',
                (sid1,document_id,1,
                 'En el presente caso ficticio, el operador debera realizar un monitoreo anual de ruido.',
                 'Anual'))
            db.execute('''INSERT INTO candidates(site_id,document_id,page_number,snippet,
                suggested_frequency) VALUES(?,?,?,?,?)''',
                (sid1,document_id,2,
                 'El operador presentara un informe de seguimiento semestral.',
                 'Semestral'))
        db.execute('''INSERT INTO activity_log(event,target_type,target_id)
            VALUES(?,?,?)''',('Datos ficticios de demostración cargados','company',cid))
        return True
