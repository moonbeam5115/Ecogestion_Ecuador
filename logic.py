"""Reviewable text heuristics and deadline classification. No AI or legal determinations."""
from __future__ import annotations
from datetime import date
import re
from typing import Iterable

FREQUENCIES = [
    ('Semestral', r'\b(?:semestral|cada\s+seis\s+meses)\b'),
    ('Trimestral', r'\b(?:trimestral|cada\s+tres\s+meses)\b'),
    ('Mensual', r'\b(?:mensual|cada\s+mes)\b'),
    ('Anual', r'\b(?:anual(?:mente)?|cada\s+a[nñ]o)\b'),
    ('Semanal', r'\b(?:semanal|cada\s+semana)\b'),
]
KEYWORDS = re.compile(
    r'\b(?:deber[aá]n?|obligaci[oó]n(?:es)?|monitoreo|seguimiento|'
    r'presentar|capacitaci[oó]n|registro|reporte|informe|'
    r'manejo de residuos|manejo de desechos|auditor[ií]a|'
    r'gesti[oó]n de residuos|gesti[oó]n de desechos)\b', re.IGNORECASE)


def frequency_from_text(text: str) -> str:
    for name, pattern in FREQUENCIES:
        if re.search(pattern, text, re.IGNORECASE):
            return name
    return 'Sin especificar'


def extract_candidates(pages: Iterable[str], limit: int = 50):
    """Conservative keyword spotting. Returns suggestions with *page provenance*.

    Limit length, dedupe, and never invent regulatory obligation or due date.
    """
    results, seen = [], set()
    for page, text in enumerate(pages, start=1):
        normalized = re.sub(r'\s+', ' ', text or '').strip()
        # PDFs vary greatly in layout: punctuation and line breaks aren't reliable.
        chunks = re.split(r'(?<=[.!?;])\s+|(?<=:)\s+', normalized)
        for chunk in chunks:
            if not KEYWORDS.search(chunk):
                continue
            chunk = chunk.strip()
            if len(chunk) < 24:
                continue
            snippet = chunk[:650]
            signature = re.sub(r'\W+', '', snippet.lower())[:180]
            if signature in seen:
                continue
            seen.add(signature)
            results.append({'page_number': page,
                            'snippet': snippet,
                            'suggested_frequency': frequency_from_text(snippet)})
            if len(results) >= limit:
                return results
    return results


def alert_status(due_date: str | None, completed: bool, today: date | None = None) -> str:
    if completed:
        return 'Cumplida'
    if not due_date:
        return 'Sin fecha'
    day = today or date.today()
    distance = (date.fromisoformat(due_date) - day).days
    if distance < 0:
        return 'Vencida'
    if distance <= 7:
        return '0–7 días'
    if distance <= 30:
        return '8–30 días'
    return 'En plazo'


def diagnosis_summary(responses: dict):
    flagged = [name for name, value in responses.items() if value == 'Sí']
    unknown = [name for name, value in responses.items() if value == 'No sé']
    return {'positive_count': len(flagged), 'unknown_count': len(unknown),
            'positive': flagged, 'unknown': unknown,
            'status': 'Evaluación preliminar: verificar en SUIA y normativa aplicable'}
