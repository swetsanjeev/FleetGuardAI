from collections import defaultdict
from datetime import timezone
from io import BytesIO
import json
from uuid import uuid4

import pyarrow as pa
import pyarrow.parquet as pq
from boto3.session import Session

from fleetguard_db.config import get_settings
from fleetguard_db.mongo import TelemetryEvent

TELEMETRY_SCHEMA = pa.schema(
    [
        pa.field("event_id", pa.string(), nullable=False),
        pa.field("organization_id", pa.string(), nullable=False),
        pa.field("vehicle_id", pa.string(), nullable=False),
        pa.field("vin", pa.string()),
        pa.field("event_ts", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("ingest_ts", pa.timestamp("us", tz="UTC"), nullable=False),
        pa.field("sequence_no", pa.int64(), nullable=False),
        pa.field("schema_version", pa.int32(), nullable=False),
        pa.field("event_type", pa.string(), nullable=False),
        pa.field("latitude", pa.float64()),
        pa.field("longitude", pa.float64()),
        pa.field("speed_kmh", pa.float64()),
        pa.field("acceleration_mps2", pa.float64()),
        pa.field("battery_soc_pct", pa.float64()),
        pa.field("fuel_pct", pa.float64()),
        pa.field("odometer_km", pa.float64()),
        pa.field("dtc_codes", pa.list_(pa.string()), nullable=False),
        pa.field("oem_metadata_json", pa.string(), nullable=False),
    ]
)


def _s3_client():
    settings = get_settings()
    if not all((settings.object_storage_endpoint, settings.object_storage_access_key, settings.object_storage_secret_key)):
        raise RuntimeError("OBJECT_STORAGE_ENDPOINT and object-storage credentials are required")
    return Session().client(
        "s3",
        endpoint_url=settings.object_storage_endpoint,
        aws_access_key_id=settings.object_storage_access_key,
        aws_secret_access_key=settings.object_storage_secret_key,
        region_name="us-east-1",
    )


def write_telemetry_batch(events: list[TelemetryEvent], s3_client=None) -> list[str]:
    """Write one compressed Parquet object per date/hour/organization group."""
    if not events:
        return []
    settings = get_settings()
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for event in events:
        event_utc = event.event_ts.astimezone(timezone.utc)
        grouped[(event_utc.strftime("%Y-%m-%d"), event_utc.strftime("%H"), event.organization_id)].append(
            {
                **event.model_dump(mode="python", exclude={"oem_metadata"}),
                "oem_metadata_json": json.dumps(event.oem_metadata, sort_keys=True),
            }
        )

    client = s3_client or _s3_client()
    keys = []
    for (event_date, hour, organization_id), rows in grouped.items():
        table = pa.Table.from_pylist(rows, schema=TELEMETRY_SCHEMA)
        buffer = BytesIO()
        pq.write_table(table, buffer, compression="zstd")
        key = (
            f"raw/event_date={event_date}/hour={hour}/organization_id={organization_id}/"
            f"telemetry-{uuid4().hex}.parquet"
        )
        client.put_object(
            Bucket=settings.object_storage_bucket,
            Key=key,
            Body=buffer.getvalue(),
            ContentType="application/vnd.apache.parquet",
        )
        keys.append(key)
    return keys