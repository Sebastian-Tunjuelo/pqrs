"""Carga de ``secretarias_routing.yaml`` validado vía shared-kernel."""

from __future__ import annotations

from shared_kernel.glossary_loader import SecretariasRoutingGlossary, load_glossary

from routing.infrastructure.paths import glosarios_dir


def load_secretarias_routing() -> SecretariasRoutingGlossary:
    path = glosarios_dir() / "secretarias_routing.yaml"
    return load_glossary(path, kind="secretarias_routing")
