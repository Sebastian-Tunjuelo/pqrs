"""Dependencias inyectables en el grafo (casos de uso de otros bounded contexts)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from classification.application.classify_use_case import ClassifyPqrsUseCase
    from prioritization.application.prioritize_use_case import PrioritizePqrsUseCase
    from routing.application.recommend_secretaria_use_case import RecommendSecretariaUseCase


@dataclass
class OrchestrationDeps:
    classify_use_case: ClassifyPqrsUseCase | None = None
    prioritize_use_case: PrioritizePqrsUseCase | None = None
    route_use_case: RecommendSecretariaUseCase | None = None


def default_deps() -> OrchestrationDeps:
    from classification.application.classify_use_case import ClassifyPqrsUseCase
    from prioritization.application.prioritize_use_case import PrioritizePqrsUseCase
    from routing.application.recommend_secretaria_use_case import RecommendSecretariaUseCase

    return OrchestrationDeps(
        classify_use_case=ClassifyPqrsUseCase(),
        prioritize_use_case=PrioritizePqrsUseCase(),
        route_use_case=RecommendSecretariaUseCase(),
    )
