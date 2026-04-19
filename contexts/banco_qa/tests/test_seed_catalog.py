from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from banco_qa.application.seed_catalog import SeedBancoQaCatalog


def test_seed_rejects_empty_catalog(tmp_path: Path) -> None:
    y = tmp_path / "empty.yaml"
    y.write_text(
        textwrap.dedent(
            """
            version: 1
            entries: []
            """
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="no tiene entradas"):
        SeedBancoQaCatalog().execute(y, "postgresql://invalid")
