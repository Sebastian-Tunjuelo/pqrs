from datetime import date, datetime, timezone

import pytest

from shared_kernel.events import (
    PqrsIngestedPayload,
    validate_event_payload,
)


def test_pqrs_ingested_dcat_source_validates() -> None:
    ts = datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    p = PqrsIngestedPayload(
        occurred_at=ts,
        pqrs_id="550e8400-e29b-41d4-a716-446655440000",
        contenido="Catálogo DCAT MEData.",
        fecha_radicado=ts,
        source="medata_dcat",
        metadata={"catalog": "data.json"},
    )
    d = p.model_dump(mode="json")
    validate_event_payload("PqrsIngested", d)


def test_pqrs_ingested_roundtrip_schema() -> None:
    ts = datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    p = PqrsIngestedPayload(
        occurred_at=ts,
        pqrs_id="550e8400-e29b-41d4-a716-446655440000",
        contenido="Solicitud de información sobre trámites.",
        fecha_radicado=ts,
        source="medata_api",
        metadata={"foo": 1},
    )
    d = p.model_dump(mode="json")
    validate_event_payload("PqrsIngested", d)


def test_pqrs_ingested_rejects_bad_uuid() -> None:
    ts = datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    bad = {
        "event_type": "PqrsIngested",
        "version": 1,
        "occurred_at": ts.isoformat().replace("+00:00", "Z"),
        "pqrs_id": "not-a-uuid",
        "contenido": "x",
        "fecha_radicado": ts.isoformat().replace("+00:00", "Z"),
        "source": "medata_api",
        "metadata": {},
    }
    with pytest.raises(Exception):
        validate_event_payload("PqrsIngested", bad)


def test_pqrs_prioritized_validates_date_format() -> None:
    payload = {
        "event_type": "PqrsPrioritized",
        "version": 1,
        "occurred_at": "2025-06-01T12:00:00Z",
        "pqrs_id": "550e8400-e29b-41d4-a716-446655440000",
        "nivel_riesgo": "MEDIO",
        "sla_dias_habiles": 15,
        "fecha_limite": date(2025, 6, 20).isoformat(),
        "factores_riesgo": [],
        "justificacion": None,
    }
    validate_event_payload("PqrsPrioritized", payload)
