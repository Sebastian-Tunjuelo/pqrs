"""Recomienda secretaría(s) competente(s) por keywords + opcional tie-break LLM."""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError

from routing.domain.routing_decision import RoutingDecision, SecretariaMatch
from routing.infrastructure.ollama_json_client import OllamaJsonClient, SupportsJsonChat
from routing.infrastructure.paths import router_prompt_path
from routing.infrastructure.scoring import score_secretarias
from routing.infrastructure.secretarias_loader import load_secretarias_routing


def _strip_json_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


class _TieBreakResponse(BaseModel):
    secretaria_lider: str
    secretarias_orden: list[str] = Field(min_length=1)


class RecommendSecretariaUseCase:
    def __init__(
        self,
        ollama_client: SupportsJsonChat | None = None,
        system_prompt_path: Path | None = None,
        umbral_multidependencia: float = 0.6,
        delta_tie_break: float = 0.03,
        top_k: int = 5,
    ) -> None:
        self._ollama = ollama_client or OllamaJsonClient()
        self._prompt_path = system_prompt_path or router_prompt_path()
        self._umbral = umbral_multidependencia
        self._delta = delta_tie_break
        self._top_k = top_k

    async def execute(self, texto: str) -> RoutingDecision:
        glossary = load_secretarias_routing()
        scores, meta = score_secretarias(texto, glossary)

        if not scores or max(scores.values()) <= 0.0:
            sgh = glossary.secretarias["SGH"]
            return RoutingDecision(
                secretarias_recomendadas=[
                    SecretariaMatch(
                        codigo="SGH",
                        nombre=sgh.nombre,
                        score=0.0,
                        motivo="Sin coincidencias claras de keywords; derivación a atención ciudadana.",
                    )
                ],
                es_multidependencia=False,
                secretaria_lider="SGH",
                tie_breaker_usado=False,
            )

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_map = dict(ranked[: self._top_k])
        top_list = [(c, s) for c, s in ranked[: self._top_k] if s > 0][: self._top_k]

        tie_used = False
        lider_override: str | None = None
        orden_override: list[str] | None = None

        if len(top_list) >= 2:
            s0, s1 = top_list[0][1], top_list[1][1]
            if abs(s0 - s1) < self._delta and s1 >= (self._umbral - 0.05):
                system = self._prompt_path.read_text(encoding="utf-8")
                user = json.dumps(
                    {
                        "texto_pqrs": texto,
                        "candidatos": [
                            {
                                "codigo": c,
                                "nombre": glossary.secretarias[c].nombre,
                                "score": round(s, 4),
                            }
                            for c, s in top_list[:4]
                        ],
                    },
                    ensure_ascii=False,
                )
                raw = await self._ollama.chat_json(system=system, user=user)
                try:
                    tb = _TieBreakResponse.model_validate(
                        json.loads(_strip_json_fence(raw))
                    )
                    orden = [c for c in tb.secretarias_orden if c in top_map]
                    if tb.secretaria_lider in top_map and orden:
                        tie_used = True
                        lider_override = tb.secretaria_lider
                        orden_override = orden
                except (json.JSONDecodeError, ValidationError):
                    pass

        if orden_override and lider_override:
            seen: set[str] = set()
            final_codigos: list[str] = []
            for c in orden_override:
                if c in top_map and c not in seen:
                    seen.add(c)
                    final_codigos.append(c)
            for c, _ in top_list:
                if c not in seen:
                    final_codigos.append(c)
                    seen.add(c)
            top_list = [(c, top_map[c]) for c in final_codigos[: self._top_k]]
        else:
            top_list = [(c, top_map[c]) for c, _ in top_list if c in top_map][: self._top_k]

        matches = [
            SecretariaMatch(
                codigo=cod,
                nombre=glossary.secretarias[cod].nombre,
                score=round(sc, 3),
                motivo=_motivo(meta.get(cod, [])),
            )
            for cod, sc in top_list
        ]

        lider = (
            lider_override
            if lider_override and lider_override in {m.codigo for m in matches}
            else matches[0].codigo
        )

        sobre_umbral = sum(1 for sc in scores.values() if sc >= self._umbral)
        es_multi = sobre_umbral >= 2

        return RoutingDecision(
            secretarias_recomendadas=matches,
            es_multidependencia=es_multi,
            secretaria_lider=lider,
            tie_breaker_usado=tie_used,
        )


def _motivo(kws: list[str]) -> str:
    if not kws:
        return "Coincidencias por reglas de ruteo."
    return "Keywords / reglas: " + ", ".join(kws[:12])
