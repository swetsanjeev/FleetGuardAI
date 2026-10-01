from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from fleetguard_db.config import get_settings


class TelemetryEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=160)
    organization_id: str = Field(min_length=1, max_length=100)
    vehicle_id: str = Field(min_length=1, max_length=100)
    vin: str | None = Field(default=None, max_length=32)
    event_ts: datetime
    ingest_ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sequence_no: int = Field(ge=0)
    schema_version: int = Field(ge=1)
    event_type: str = Field(min_length=1, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    speed_kmh: float | None = Field(default=None, ge=0)
    acceleration_mps2: float | None = None
    battery_soc_pct: float | None = Field(default=None, ge=0, le=100)
    fuel_pct: float | None = Field(default=None, ge=0, le=100)
    odometer_km: float | None = Field(default=None, ge=0)
    dtc_codes: list[str] = Field(default_factory=list)
    oem_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_ts", "ingest_ts")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamps must include a timezone")
        return value.astimezone(timezone.utc)


class DiagnosticEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=160)
    organization_id: str = Field(min_length=1, max_length=100)
    vehicle_id: str = Field(min_length=1, max_length=100)
    event_ts: datetime
    ingest_ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    code: str = Field(min_length=1, max_length=80)
    severity: str | None = Field(default=None, max_length=40)
    description: str | None = Field(default=None, max_length=4000)
    schema_version: int = Field(default=1, ge=1)
    oem_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_ts", "ingest_ts")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamps must include a timezone")
        return value.astimezone(timezone.utc)


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    url = get_settings().mongodb_url
    if not url:
        raise RuntimeError("MONGODB_URL is required for MongoDB access")
    return MongoClient(url, appname="fleetguard-api", serverSelectionTimeoutMS=5000)


def get_database():
    return get_mongo_client()[get_settings().mongodb_database]


def ensure_mongo_schema(database) -> None:
    telemetry_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": [
                "_id", "organization_id", "vehicle_id", "event_ts", "ingest_ts",
                "sequence_no", "schema_version", "event_type", "dtc_codes",
            ],
            "properties": {
                "_id": {"bsonType": "string"},
                "organization_id": {"bsonType": "string"},
                "vehicle_id": {"bsonType": "string"},
                "vin": {"bsonType": ["string", "null"]},
                "event_ts": {"bsonType": "date"},
                "ingest_ts": {"bsonType": "date"},
                "sequence_no": {"bsonType": ["int", "long"], "minimum": 0},
                "schema_version": {"bsonType": ["int", "long"], "minimum": 1},
                "event_type": {"bsonType": "string"},
                "dtc_codes": {"bsonType": "array", "items": {"bsonType": "string"}},
                "oem_metadata": {"bsonType": "object"},
            },
        }
    }
    diagnostic_validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["_id", "organization_id", "vehicle_id", "event_ts", "code"],
            "properties": {
                "_id": {"bsonType": "string"},
                "organization_id": {"bsonType": "string"},
                "vehicle_id": {"bsonType": "string"},
                "event_ts": {"bsonType": "date"},
                "code": {"bsonType": "string"},
                "ingest_ts": {"bsonType": "date"},
                "oem_metadata": {"bsonType": "object"},
            },
        }
    }
    for name, validator in (
        ("telemetry_events", telemetry_validator),
        ("diagnostic_events", diagnostic_validator),
    ):
        if name not in database.list_collection_names():
            database.create_collection(name, validator=validator)
        else:
            database.command({"collMod": name, "validator": validator})

    database.telemetry_events.create_index(
        [("vehicle_id", ASCENDING), ("event_ts", DESCENDING)],
        name="ix_telemetry_vehicle_event_ts",
    )
    database.telemetry_events.create_index(
        [("event_type", ASCENDING), ("event_ts", DESCENDING)],
        name="ix_telemetry_type_event_ts",
    )
    database.telemetry_events.create_index(
        [("vehicle_id", ASCENDING), ("event_type", ASCENDING), ("event_ts", DESCENDING)],
        name="ix_telemetry_vehicle_type_event_ts",
    )
    database.diagnostic_events.create_index(
        [("vehicle_id", ASCENDING), ("event_ts", DESCENDING)],
        name="ix_diagnostics_vehicle_event_ts",
    )
    database.diagnostic_events.create_index(
        [("code", ASCENDING), ("event_ts", DESCENDING)],
        name="ix_diagnostics_code_event_ts",
    )
    database.vehicle_state.create_index(
        [("vehicle_id", ASCENDING)], unique=True, name="uq_vehicle_state_vehicle"
    )


class TelemetryRepository:
    def __init__(self, collection: Collection | None = None) -> None:
        self.collection = collection if collection is not None else get_database().telemetry_events

    def insert(self, event: TelemetryEvent) -> bool:
        document = event.model_dump(mode="python")
        document["_id"] = document.pop("event_id")
        try:
            self.collection.insert_one(document)
        except DuplicateKeyError:
            return False
        return True

    def get_vehicle_events(
        self,
        vehicle_id: str,
        start: datetime,
        end: datetime,
        limit: int = 100,
        before: datetime | None = None,
    ) -> list[dict[str, Any]]:
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError("time-range boundaries must include a timezone")
        if end <= start:
            raise ValueError("end must be after start")
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        query: dict[str, Any] = {
            "vehicle_id": vehicle_id,
            "event_ts": {"$gte": start, "$lt": end},
        }
        if before is not None:
            query["event_ts"]["$lt"] = min(end, before)
        return list(self.collection.find(query, {"_id": 0}).sort("event_ts", DESCENDING).limit(limit))


class DiagnosticRepository:
    def __init__(self, collection: Collection | None = None) -> None:
        self.collection = collection if collection is not None else get_database().diagnostic_events

    def insert(self, event: DiagnosticEvent) -> bool:
        document = event.model_dump(mode="python")
        document["_id"] = document.pop("event_id")
        try:
            self.collection.insert_one(document)
        except DuplicateKeyError:
            return False
        return True


def check_mongodb() -> None:
    get_mongo_client().admin.command("ping")


def close_mongo_client() -> None:
    if get_mongo_client.cache_info().currsize:
        get_mongo_client().close()
        get_mongo_client.cache_clear()