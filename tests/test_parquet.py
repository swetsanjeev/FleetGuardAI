from datetime import datetime, timezone
from io import BytesIO

import pyarrow.parquet as pq

from fleetguard_db.config import Settings
from fleetguard_db.mongo import TelemetryEvent
from fleetguard_db.parquet import write_telemetry_batch


class FakeS3Client:
    def __init__(self) -> None:
        self.objects = []

    def put_object(self, **kwargs) -> None:
        self.objects.append(kwargs)


def test_parquet_writer_groups_by_date_hour_and_organization(monkeypatch) -> None:
    import fleetguard_db.parquet as parquet

    monkeypatch.setattr(
        parquet,
        "get_settings",
        lambda: Settings(object_storage_bucket="fleetguard-test"),
    )
    first = TelemetryEvent(
        event_id="event-1",
        organization_id="org-1",
        vehicle_id="vehicle-1",
        event_ts=datetime(2026, 1, 3, 10, 10, tzinfo=timezone.utc),
        sequence_no=1,
        schema_version=1,
        event_type="telemetry",
        dtc_codes=["P0301"],
        oem_metadata={"source": "test"},
    )
    same_partition = first.model_copy(update={"event_id": "event-2", "sequence_no": 2})
    next_hour = first.model_copy(
        update={
            "event_id": "event-3",
            "sequence_no": 3,
            "event_ts": datetime(2026, 1, 3, 11, 10, tzinfo=timezone.utc),
        }
    )
    client = FakeS3Client()

    keys = write_telemetry_batch([first, same_partition, next_hour], client)

    assert len(keys) == len(client.objects) == 2
    assert all(item["Bucket"] == "fleetguard-test" for item in client.objects)
    assert any("event_date=2026-01-03/hour=10/organization_id=org-1" in key for key in keys)
    assert any("event_date=2026-01-03/hour=11/organization_id=org-1" in key for key in keys)
    table = pq.read_table(BytesIO(client.objects[0]["Body"]))
    assert table.num_rows == 2
    assert table.schema == parquet.TELEMETRY_SCHEMA
    assert table.to_pylist()[0]["oem_metadata_json"] == '{"source": "test"}'