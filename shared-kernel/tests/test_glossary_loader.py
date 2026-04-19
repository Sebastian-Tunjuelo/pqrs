from pathlib import Path

from shared_kernel.glossary_loader import load_glossary


ROOT = Path(__file__).resolve().parents[2]


def test_load_ofensivo_glossary() -> None:
    glossary = load_glossary(ROOT / "glosarios" / "ofensivo.yaml", kind="ofensivo")
    assert glossary.no_entendible.min_caracteres == 20
    assert "hijueputa" in glossary.insultos_directos


def test_load_secretarias_routing() -> None:
    glossary = load_glossary(
        ROOT / "glosarios" / "secretarias_routing.yaml",
        kind="secretarias_routing",
    )
    assert "SDE" in glossary.secretarias
    assert len(glossary.multidependencias) == 3
