"""Scoring por coincidencias de keywords (normalizado 0–1)."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict

from shared_kernel.glossary_loader import SecretariasRoutingGlossary


def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def _tokenize(norm: str) -> set[str]:
    return set(re.findall(r"[\wáéíóúñüÁÉÍÓÚÑÜ]+", norm, flags=re.UNICODE))


def _keyword_hits(norm_compact: str, tokens: set[str], keyword: str) -> int:
    kw = _normalize(keyword).strip()
    if not kw:
        return 0
    if " " in kw:
        return 1 if kw in norm_compact else 0
    if len(kw) <= 3:
        return 1 if kw in tokens else 0
    return norm_compact.count(kw)


def score_secretarias(
    texto: str, glossary: SecretariasRoutingGlossary
) -> tuple[dict[str, float], dict[str, list[str]]]:
    norm = _normalize(texto)
    norm_compact = re.sub(r"\s+", " ", norm.strip())
    tokens = _tokenize(norm)

    raw: dict[str, float] = defaultdict(float)
    matched_kw: dict[str, list[str]] = defaultdict(list)

    for codigo, entry in glossary.secretarias.items():
        for kw in entry.keywords:
            hits = _keyword_hits(norm_compact, tokens, kw)
            if hits:
                raw[codigo] += float(hits)
                matched_kw[codigo].append(kw)

    for rule in glossary.multidependencias:
        if all(_normalize(t) in norm_compact for t in rule.trigger):
            for cod in rule.secretarias:
                raw[cod] += 5.0
                matched_kw[cod].append(f"multidependencia:{','.join(rule.trigger)}")

    if not raw:
        return {}, {}

    mx = max(raw.values())
    if mx <= 0:
        mx = 1.0
    normalized = {k: v / mx for k, v in raw.items()}
    return dict(normalized), {k: list(dict.fromkeys(v)) for k, v in matched_kw.items()}
