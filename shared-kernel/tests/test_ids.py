import pytest

from shared_kernel.value_objects.ids import (
    parse_ciudadano_id,
    parse_pqrs_id,
    parse_secretaria_codigo,
)


def test_parse_pqrs_id() -> None:
    s = "550E8400-E29B-41D4-A716-446655440000"
    pid = parse_pqrs_id(s)
    assert pid == "550e8400-e29b-41d4-a716-446655440000"


def test_parse_pqrs_id_invalid() -> None:
    with pytest.raises(ValueError):
        parse_pqrs_id("oops")


def test_parse_secretaria() -> None:
    assert parse_secretaria_codigo("  sde  ") == "SDE"


def test_parse_secretaria_invalid() -> None:
    with pytest.raises(ValueError):
        parse_secretaria_codigo("")
