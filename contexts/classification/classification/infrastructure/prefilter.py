"""Keyword / pattern pre-filters before invoking the LLM."""

from __future__ import annotations

import re
import unicodedata

from nltk.stem.snowball import SnowballStemmer
from shared_kernel.glossary_loader import load_glossary

from classification.infrastructure.paths import glosarios_dir


def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in s if not unicodedata.combining(ch)).lower()


_stemmer = SnowballStemmer("spanish")
_WORD_RE = re.compile(r"[\wáéíóúñüÁÉÍÓÚÑÜ]+", re.UNICODE)


def _tokens(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _stem_set(words: list[str]) -> set[str]:
    return {_stemmer.stem(w) for w in words if len(w) > 1}


def match_offensive_prefilter(text: str, phrases: list[str]) -> list[str]:
    """Subcadena normalizada, límites de palabra y stemming (español)."""
    norm = _normalize(text)
    norm_spaced = re.sub(r"\s+", " ", norm.strip())
    hits: list[str] = []

    for phrase in phrases:
        raw_p = phrase.strip()
        if not raw_p:
            continue
        p = raw_p.lower()
        if "(" in p:
            p = p.split("(")[0].strip()
        p_norm = _normalize(p)
        if not p_norm:
            continue
        if " " in p_norm:
            if p_norm in norm_spaced:
                hits.append(raw_p)
            continue
        if re.search(rf"\b{re.escape(p_norm)}\b", norm_spaced):
            hits.append(raw_p)
            continue
        if len(p_norm) <= 4 and p_norm in norm_spaced.replace(" ", ""):
            hits.append(raw_p)

    stems_text = _stem_set(_tokens(text))
    for phrase in phrases:
        raw_p = phrase.strip()
        p = raw_p.lower()
        if "(" in p:
            p = p.split("(")[0].strip()
        p_norm = _normalize(p)
        if not p_norm or " " in p_norm:
            continue
        st = _stemmer.stem(p_norm)
        if st in stems_text and raw_p not in hits:
            hits.append(raw_p)

    seen: set[str] = set()
    out: list[str] = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def load_offensive_phrases() -> list[str]:
    path = glosarios_dir() / "ofensivo.yaml"
    g = load_glossary(path, kind="ofensivo")
    return (
        list(g.insultos_directos)
        + list(g.amenazas)
        + list(g.discriminacion)
    )


def check_no_entendible(text: str, min_caracteres: int, patrones: list[str]) -> list[str]:
    """Devuelve lista de patrones detectados (vacía si parece entendible)."""
    raw = text.strip()
    reasons: list[str] = []

    if len(raw) < min_caracteres:
        reasons.append("muy_corto")

    if raw and not re.search(r"[0-9A-Za-záéíóúñüÁÉÍÓÚÑÜ]", raw):
        if "solo_emojis" in patrones:
            reasons.append("solo_emojis")

    if raw and re.fullmatch(r"[\d\s\.,]+", raw) and "solo_numeros" in patrones:
        reasons.append("solo_numeros")

    if re.search(r"(.)\1{6,}", raw.lower()) and "repeticion_letras" in patrones:
        reasons.append("repeticion_letras")

    return reasons


def load_no_entendible_config() -> tuple[int, list[str]]:
    path = glosarios_dir() / "ofensivo.yaml"
    g = load_glossary(path, kind="ofensivo")
    ne = g.no_entendible
    return ne.min_caracteres, list(ne.patrones_rechazo)
