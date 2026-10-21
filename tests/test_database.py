import importlib
from pathlib import Path
from pypdf import PdfReader


def test_schema_and_seed(tmp_path, monkeypatch):
    monkeypatch.setenv('ECOGESTION_DATA_DIR', str(tmp_path))
    import database
    importlib.reload(database)
    database.initialize()
    assert database.seed_demo() is True
    assert database.seed_demo() is False
    company = database.fetch_one("SELECT * FROM companies WHERE ruc='DEMO-000000000'")
    assert company and 'FICTICIA' in company['legal_name']
    assert database.fetch_one('SELECT COUNT(*) AS n FROM companies')['n'] == 2
    assert database.fetch_one('SELECT COUNT(*) AS n FROM sites')['n'] == 3
    assert database.fetch_one('SELECT COUNT(*) AS n FROM obligations')['n'] == 8
    assert database.fetch_one('SELECT COUNT(*) AS n FROM waste_entries')['n'] == 2
    assert database.fetch_one('SELECT COUNT(*) AS n FROM candidates')['n'] == 2
    completed = database.fetch_all('SELECT id FROM obligations WHERE completed=1')
    assert len(completed) == 1
    assert database.fetch_one('SELECT COUNT(*) AS n FROM evidence WHERE obligation_id=? AND reviewed=1',
                              (completed[0]['id'],))['n'] == 1
    assert database.fetch_one('SELECT COUNT(*) AS n FROM sites WHERE company_id=?',(company['id'],))['n']==2


def test_demo_pdf_extracts_candidates_with_sources():
    from logic import extract_candidates
    path = Path(__file__).resolve().parents[1] / 'sample_docs' / 'resolucion_ficticia_demo.pdf'
    reader = PdfReader(path)
    assert len(reader.pages) == 2
    candidates = extract_candidates([p.extract_text() for p in reader.pages])
    assert any(c['page_number'] == 1 and c['suggested_frequency']=='Anual' for c in candidates)
    assert any(c['page_number'] == 2 and c['suggested_frequency']=='Semestral' for c in candidates)
    assert all('due_date' not in c for c in candidates)
