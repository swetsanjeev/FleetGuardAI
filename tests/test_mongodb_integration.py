from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError
from pymongo.errors import OperationFailure
from pymongo import ASCENDING, DESCENDING

from fleetguard_db.mongo import (
    DiagnosticEvent,
    DiagnosticRepository,
    TelemetryEvent,
    TelemetryRepository,
    ensure_mongo_schema,
)


def _telemetry(event_id: str, event_ts: datetime, sequence_no: int) -> TelemetryEvent:
    return TelemetryEvent(
        event_id=event_id,
        organization_id="organization-test",
        vehicle_id="vehicle-test",
        vin="SIM00000000001",
        event_ts=event_ts,
        sequence_no=sequence_no,
        schema_version=1,
        event_type="telemetry",
        latitude=37.7749,
        longitude=-122.4194,
        speed_kmh=32.5,
        battery_soc_pct=78.0,
        odometer_km=120.0,
        dtc_codes=["P0301"],
        oem_metadata={"vendor": "synthetic", "nested": {"version": 2}},
    )


def test_telemetry_insert_dedup_and_time_range(mongo_database) -> None:
    ensure_mongo_schema(mongo_database)
    repository = TelemetryRepository(mongo_database.telemetry_events)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    earlier = _telemetry("event-1", start + timedelta(minutes=1), 1)
    later = _telemetry("event-2", start + timedelta(minutes=2), 2)

    assert repository.insert(earlier) is True
    assert repository.insert(earlier) is False
    assert repository.insert(later) is True

    result = repository.get_vehicle_events(
        "vehicle-test",
        start,
        start + timedelta(minutes=3),
        limit=10,
    )

    assert [document["event_type"] for document in result] == ["telemetry", "telemetry"]
    assert [document["sequence_no"] for document in result] == [2, 1]
    assert result[0]["oem_metadata"]["nested"]["version"] == 2


def test_diagnostic_documents_validate_and_index_by_code(mongo_database) -> None:
    ensure_mongo_schema(mongo_database)
    repository = DiagnosticRepository(mongo_database.diagnostic_events)
    event = DiagnosticEvent(
        event_id="diagnostic-1",
        organization_id="organization-test",
        vehicle_id="vehicle-test",
        event_ts=datetime.now(timezone.utc),
        code="P0301",
        severity="warning",
        description="Synthetic misfire diagnostic.",
        oem_metadata={"manufacturer_extension": {"raw": "value"}},
    )

    assert repository.insert(event) is True
    assert repository.insert(event) is False
    names = {index["name"] for index in mongo_database.diagnostic_events.list_indexes()}
    assert "ix_diagnostics_code_event_ts" in names


def test_mongo_schema_rejects_malformed_telemetry(mongo_database) -> None:
    ensure_mongo_schema(mongo_database)

    with pytest.raises(OperationFailure):
        mongo_database.telemetry_events.insert_one({"_id": "malformed-event"})

    malformed = _telemetry("bad-coordinate", datetime.now(timezone.utc), 1).model_dump()
    malformed["latitude"] = 95
    with pytest.raises(ValidationError):
        TelemetryEvent.model_validate(malformed)


def test_mongo_indexes_match_vehicle_time_and_event_query_patterns(mongo_database) -> None:
    ensure_mongo_schema(mongo_database)
    index_keys = {
        index["name"]: list(index["key"].items())
        for index in mongo_database.telemetry_events.list_indexes()
    }

    assert index_keys["ix_telemetry_vehicle_event_ts"] == [
        ("vehicle_id", ASCENDING),
        ("event_ts", DESCENDING),
    ]
    assert index_keys["ix_telemetry_type_event_ts"] == [
        ("event_type", ASCENDING),
        ("event_ts", DESCENDING),
    ]