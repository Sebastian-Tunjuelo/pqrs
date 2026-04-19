"""Coincidencia de texto contra glosarios de riesgo (poblacional + personal)."""

from __future__ import annotations

import re
import unicodedata

from shared_kernel.glossary_loader import load_glossary
from shared_kernel.value_objects.enums import NivelRiesgo

from prioritization.infrastructure.paths import glosarios_dir


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower()


def _phrases_for_level(g: object, nivel: NivelRiesgo) -> list[str]:
    block = getattr(g, nivel.name, None)
    if not block:
        return []
    out: list[str] = []
    for phrases in block.values():
        out.extend(phrases)
    return out


def _merged_phrases() -> dict[NivelRiesgo, list[str]]:
    p = load_glossary(glosarios_dir() / "riesgo_poblacional.yaml", kind="riesgo_poblacional")
    q = load_glossary(glosarios_dir() / "riesgo_personal.yaml", kind="riesgo_personal")
    return {
        lvl: _phrases_for_level(p, lvl) + _phrases_for_level(q, lvl)
        for lvl in NivelRiesgo
    }


def match_nivel_desde_glosarios(texto: str) -> tuple[NivelRiesgo, list[str]]:
    norm = _norm(texto)
    norm_compact = re.sub(r"\s+", " ", norm)
    merged = _merged_phrases()

    orden = (
        NivelRiesgo.CRITICO,
        NivelRiesgo.ALTO,
        NivelRiesgo.MEDIO,
        NivelRiesgo.BAJO,
    )
    matches: list[tuple[NivelRiesgo, str]] = []

    for nivel in orden:
        for phrase in merged.get(nivel, []):
            p = _norm(phrase.strip())
            if len(p) < 3:
                continue
            if p in norm_compact or p in norm.replace(" ", ""):
                matches.append((nivel, phrase.strip()))

    if not matches:
        return NivelRiesgo.BAJO, []

    best = max(matches, key=lambda m: orden.index(m[0]))[0]
    hits = [phrase for nivel, phrase in matches if nivel == best]

    uniq: list[str] = []
    for h in hits:
        if h not in uniq:
            uniq.append(h)

    return best, uniq[:20]
