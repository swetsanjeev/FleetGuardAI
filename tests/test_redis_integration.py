import pytest

from fleetguard_db.redis_cache import (
    ACTIVE_ALERTS_TTL_SECONDS,
    FLEET_SUMMARY_TTL_SECONDS,
    RedisCache,
    redis_key_driver_score,
    redis_key_fleet_summary,
    redis_key_vehicle_alerts,
    redis_key_vehicle_location,
    redis_key_vehicle_risk,
    redis_key_vehicle_state,
)


def test_cache_keys_and_json_round_trip(redis_client) -> None:
    cache = RedisCache(redis_client)
    cache.cache_vehicle_state("vehicle-1", {"speed_kmh": 42.0})
    cache.cache_vehicle_location("vehicle-1", {"latitude": 37.7, "longitude": -122.4})
    cache.cache_vehicle_risk("vehicle-1", {"risk_level": "unknown", "score": None})
    cache.cache_driver_score("driver-1", {"score": None, "risk_level": "unknown"})
    cache.cache_fleet_summary("fleet-1", {"active_vehicle_count": 2})

    assert cache.get_json(redis_key_vehicle_state("vehicle-1")) == {"speed_kmh": 42.0}
    assert cache.get_json(redis_key_vehicle_location("vehicle-1"))["latitude"] == 37.7
    assert cache.get_json(redis_key_vehicle_risk("vehicle-1"))["risk_level"] == "unknown"
    assert cache.get_json(redis_key_driver_score("driver-1"))["score"] is None
    assert cache.get_json(redis_key_fleet_summary("fleet-1"))["active_vehicle_count"] == 2
    assert redis_client.ttl(redis_key_fleet_summary("fleet-1")) <= FLEET_SUMMARY_TTL_SECONDS


def test_active_alert_set_has_expiry_and_retrieval(redis_client) -> None:
    cache = RedisCache(redis_client)
    cache.add_active_alert("vehicle-7", "alert-a")
    cache.add_active_alert("vehicle-7", "alert-b")

    key = redis_key_vehicle_alerts("vehicle-7")
    assert cache.get_active_alerts("vehicle-7") == {"alert-a", "alert-b"}
    assert 0 < redis_client.ttl(key) <= ACTIVE_ALERTS_TTL_SECONDS


def test_cache_rejects_nonpositive_expiration(redis_client) -> None:
    cache = RedisCache(redis_client)

    with pytest.raises(ValueError, match="TTL must be positive"):
        cache.set_json("vehicle:test:latest", {"state": "temporary"}, ttl_seconds=0)
