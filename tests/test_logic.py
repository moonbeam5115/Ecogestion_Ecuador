from datetime import date, timedelta

from logic import alert_status, diagnosis_summary, extract_candidates, frequency_from_text


def test_alert_boundaries():
    day = date(2026, 10, 16)
    assert alert_status('2026-10-15', False, day) == 'Vencida'
    assert alert_status('2026-10-16', False, day) == '0–7 días'
    assert alert_status('2026-10-23', False, day) == '0–7 días'
    assert alert_status('2026-10-24', False, day) == '8–30 días'
    assert alert_status('2026-11-15', False, day) == '8–30 días'
    assert alert_status('2026-11-16', False, day) == 'En plazo'
    assert alert_status(None, False, day) == 'Sin fecha'
    assert alert_status('2026-10-15', True, day) == 'Cumplida'


def test_extraction_provenance_and_no_invented_date():
    pages = [
        'El titular deberá realizar un monitoreo anual de ruido en las instalaciones. '
        'Las instalaciones contarán con ventilación apropiada.',
        'La empresa presentará un informe de seguimiento semestral a la autoridad.'
    ]
    matches = extract_candidates(pages)
    assert matches
    assert any(x['page_number']==1 and x['suggested_frequency']=='Anual' for x in matches)
    assert any(x['page_number']==2 and x['suggested_frequency']=='Semestral' for x in matches)
    assert all('due_date' not in x for x in matches)


def test_frequency_and_diagnostic():
    assert frequency_from_text('Capacitación cada seis meses') == 'Semestral'
    result = diagnosis_summary({'A':'Sí','B':'No sé','C':'No'})
    assert result['positive_count']==1
    assert result['unknown_count']==1
