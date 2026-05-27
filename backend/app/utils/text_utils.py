"""Normalizador Sentence case estricto (espejo del JS frontend)."""
import re


def _normalize_word(word):
    if not word:
        return word
    if re.match(r'^[a-zA-ZÁÉÍÓÚÑÜáéíóúñü]+$', word):
        if word == word.upper() and len(word) <= 4:
            return word  # Sigla corta (DHL, IBM, MTN)
        return word.lower()
    return word  # Matricula/codigo: se preserva


def normalize_text(value):
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    t = re.sub(r'\s+', ' ', value.strip())
    if not t:
        return ''
    words = [_normalize_word(w) for w in t.split(' ')]
    result = ' '.join(words)
    return result[0].upper() + result[1:]


def normalize_or_none(value):
    n = normalize_text(value)
    return n if n else None
