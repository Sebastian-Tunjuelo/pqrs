from __future__ import annotations

import textwrap

import pytest
import yaml
from pydantic import ValidationError

from banco_qa.domain.catalog import QaCatalogFile


def test_load_glosario_fixture() -> None:
    raw = textwrap.dedent(
        """
        version: 1
        entries:
          - pregunta: "¿Hola?"
            respuesta: "Respuesta larga suficiente para validar el mínimo de caracteres requeridos."
            secretaria_codigo: SGH
            tags: ["a", "b"]
        """
    )
    data = yaml.safe_load(raw)
    cat = QaCatalogFile.model_validate(data)
    assert len(cat.entries) == 1
    assert cat.entries[0].secretaria_codigo == "SGH"
    assert cat.entries[0].tags == ["a", "b"]


def test_secretaria_invalida() -> None:
    raw = """
version: 1
entries:
  - pregunta: "¿Pregunta válida mínima?"
    respuesta: "Respuesta con más de tres caracteres para cumplir validación."
    secretaria_codigo: XXX
"""
    data = yaml.safe_load(raw)
    with pytest.raises(ValidationError):
        QaCatalogFile.model_validate(data)


def test_null_secretaria() -> None:
    raw = """
version: 1
entries:
  - pregunta: "¿Otra pregunta válida aquí?"
    respuesta: "Otra respuesta con longitud suficiente para el validador del dominio."
    secretaria_codigo: null
    tags: []
"""
    data = yaml.safe_load(raw)
    cat = QaCatalogFile.model_validate(data)
    assert cat.entries[0].secretaria_codigo is None
