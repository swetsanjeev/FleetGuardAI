import json
from functools import lru_cache
from typing import Any

from redis import Redis

from fleetguard_db.config import get_settings

VEHICLE_STATE_TTL_SECONDS = 300
VEHICLE_LOCATION_TTL_SECONDS = 120
VEHICLE_RISK_TTL_SECONDS = 900
DRIVER_SCORE_TTL_SECONDS = 900
FLEET_SUMMARY_TTL_SECONDS = 30
ACTIVE_ALERTS_TTL_SECONDS = 86_400


@lru_cache(maxsize=1)
def get_redis_client() -> Redis:
    url = get_settings().redis_url
    if not url:
        raise RuntimeError("REDIS_URL is required for Redis access")
    return Redis.from_url(url, decode_responses=True, health_check_interval=30)


def redis_key_vehicle_state(vehicle_id: str) -> str:
    return f"vehicle:{vehicle_id}:latest"


def redis_key_vehicle_location(vehicle_id: str) -> str:
    return f"vehicle:{vehicle_id}:location"


def redis_key_vehicle_risk(vehicle_id: str) -> str:
    return f"vehicle:{vehicle_id}:risk"


def redis_key_vehicle_alerts(vehicle_id: str) -> str:
    return f"vehicle:{vehicle_id}:alerts"


def redis_key_driver_score(driver_id: str) -> str:
    return f"driver:{driver_id}:score"


def redis_key_fleet_summary(fleet_id: str) -> str:
    return f"fleet:{fleet_id}:summary"


class RedisCache:
    def __init__(self, client: Redis | None = None) -> None:
        self.client = client or get_redis_client()

    @staticmethod
    def _encode(value: Any) -> str:
        return json.dumps(value, separators=(",", ":"), default=str)

    def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            raise ValueError("TTL must be positive")
        self.client.set(key, self._encode(value), ex=ttl_seconds)

    def get_json(self, key: str) -> dict[str, Any] | list[Any] | None:
        value = self.client.get(key)
        return json.loads(value) if value is not None else None

    def cache_vehicle_state(self, vehicle_id: str, state: dict[str, Any]) -> None:
        self.set_json(redis_key_vehicle_state(vehicle_id), state, VEHICLE_STATE_TTL_SECONDS)

    def cache_vehicle_location(self, vehicle_id: str, location: dict[str, Any]) -> None:
        self.set_json(redis_key_vehicle_location(vehicle_id), location, VEHICLE_LOCATION_TTL_SECONDS)

    def cache_vehicle_risk(self, vehicle_id: str, risk: dict[str, Any]) -> None:
        self.set_json(redis_key_vehicle_risk(vehicle_id), risk, VEHICLE_RISK_TTL_SECONDS)

    def cache_driver_score(self, driver_id: str, score: dict[str, Any]) -> None:
        self.set_json(redis_key_driver_score(driver_id), score, DRIVER_SCORE_TTL_SECONDS)

    def cache_fleet_summary(self, fleet_id: str, summary: dict[str, Any]) -> None:
        self.set_json(redis_key_fleet_summary(fleet_id), summary, FLEET_SUMMARY_TTL_SECONDS)

    def add_active_alert(self, vehicle_id: str, alert_id: str) -> None:
        key = redis_key_vehicle_alerts(vehicle_id)
        with self.client.pipeline() as pipeline:
            pipeline.sadd(key, alert_id)
            pipeline.expire(key, ACTIVE_ALERTS_TTL_SECONDS)
            pipeline.execute()

    def get_active_alerts(self, vehicle_id: str) -> set[str]:
        return set(self.client.smembers(redis_key_vehicle_alerts(vehicle_id)))

    def close(self) -> None:
        self.client.close()


def check_redis() -> None:
    get_redis_client().ping()


def close_redis_client() -> None:
    if get_redis_client.cache_info().currsize:
        get_redis_client().close()
        get_redis_client.cache_clear()