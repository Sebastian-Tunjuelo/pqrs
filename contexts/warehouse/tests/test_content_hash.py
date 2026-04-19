from warehouse.domain.content_hash import compute_contenido_hash


def test_hash_estable_y_normalizado() -> None:
    a = compute_contenido_hash("  Hola   Mundo  ")
    b = compute_contenido_hash("hola mundo")
    assert a == b
    assert len(a) == 64


def test_hash_distinto_si_cambia_texto() -> None:
    assert compute_contenido_hash("uno") != compute_contenido_hash("dos")
