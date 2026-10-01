import argparse
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from fleetguard_db.config import get_settings
from fleetguard_db.database import get_session_factory
from fleetguard_db.models import (
    Alert,
    AuditLog,
    Driver,
    DriverRiskSummary,
    Fleet,
    FleetCostSummary,
    FleetRiskSummary,
    MaintenancePlan,
    MaintenanceRecord,
    MaintenanceWorkOrder,
    Organization,
    Permission,
    Role,
    RolePermission,
    Subscription,
    Trip,
    User,
    UserRole,
    Vehicle,
    VehicleDriverAssignment,
    VehicleRiskSummary,
)

logger = logging.getLogger(__name__)
SEED_ORGANIZATION_KEY = "fleetguard-development"


def _id(entity: str, key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"fleetguard-seed:{entity}:{key}")


def seed_development_data(session: Session, vehicle_count: int) -> dict[str, int | bool]:
    if not 1 <= vehicle_count <= 10_000:
        raise ValueError("vehicle_count must be between 1 and 10,000")
    existing = session.scalar(
        select(Organization.id).where(Organization.slug == SEED_ORGANIZATION_KEY)
    )
    if existing is not None:
        return {"created": False, "vehicles": 0}

    now = datetime.now(timezone.utc).replace(microsecond=0)
    organization_id = _id("organization", SEED_ORGANIZATION_KEY)
    session.add(
        Organization(
            id=organization_id,
            name="FleetGuard Development",
            slug=SEED_ORGANIZATION_KEY,
            status="active",
        )
    )
    session.flush()

    user_id = _id("user", "operations@example.test")
    role_id = _id("role", "fleet-admin")
    permission_id = _id("permission", "fleet.read")
    session.add_all(
        [
            User(
                id=user_id,
                organization_id=organization_id,
                email="operations@example.test",
                display_name="Development Operator",
                status="active",
            ),
            Role(
                id=role_id,
                organization_id=organization_id,
                name="Fleet Admin",
                description="Seed-only development role; authentication is not configured.",
                is_system_role=True,
            ),
            Permission(
                id=permission_id,
                code="fleet.read",
                description="Read fleet and vehicle data.",
            ),
            Subscription(
                id=_id("subscription", "development"),
                organization_id=organization_id,
                plan_code="development",
                status="trial",
                starts_at=now,
            ),
        ]
    )
    session.flush()
    session.add_all(
        [
            UserRole(organization_id=organization_id, user_id=user_id, role_id=role_id),
            RolePermission(organization_id=organization_id, role_id=role_id, permission_id=permission_id),
        ]
    )
    session.flush()

    fleet_count = min(10, max(1, (vehicle_count + 999) // 1000))
    fleet_ids = []
    plan_ids: list[UUID] = []
    plans = []
    vehicles_per_fleet = (vehicle_count + fleet_count - 1) // fleet_count
    for fleet_index in range(fleet_count):
        fleet_id = _id("fleet", str(fleet_index))
        fleet_ids.append(fleet_id)
        session.add(
            Fleet(
                id=fleet_id,
                organization_id=organization_id,
                fleet_code=f"DEV-{fleet_index + 1:03d}",
                name=f"Development Fleet {fleet_index + 1}",
                status="active",
            )
        )
    session.flush()
    for fleet_index, fleet_id in enumerate(fleet_ids):
        plan_id = _id("maintenance-plan", str(fleet_index))
        plan_ids.append(plan_id)
        plans.append(
            MaintenancePlan(
                id=plan_id,
                organization_id=organization_id,
                fleet_id=fleet_id,
                name="Annual vehicle inspection",
                maintenance_type="inspection",
                interval_days=365,
                status="active",
            )
        )
    session.add_all(plans)
    session.flush()

    driver_count = max(1, (vehicle_count + 3) // 4)
    driver_ids = []
    for index in range(driver_count):
        driver_id = _id("driver", str(index))
        driver_ids.append(driver_id)
        session.add(
            Driver(
                id=driver_id,
                organization_id=organization_id,
                external_driver_id=f"DEV-DRIVER-{index + 1:06d}",
                full_name=f"Development Driver {index + 1:06d}",
                status="active",
                license_class="commercial",
                license_region="US-CA",
                license_expires_at=now + timedelta(days=365),
            )
        )
    session.flush()

    dependent_records: list[Any] = []
    for index in range(vehicle_count):
        fleet_index = min(index // vehicles_per_fleet, fleet_count - 1)
        fleet_id = fleet_ids[fleet_index]
        vehicle_id = _id("vehicle", str(index))
        driver_id = driver_ids[index % driver_count] if index < driver_count else None
        session.add(
            Vehicle(
                id=vehicle_id,
                organization_id=organization_id,
                fleet_id=fleet_id,
                vin=f"SIM{index:011d}",
                make="FleetGuard",
                model="Development Van",
                model_year=2024,
                vehicle_type="delivery_van",
                powertrain_type="electric",
                fuel_type=None,
                battery_capacity_kwh=Decimal("82.0"),
                status="active",
            )
        )
        trip_start = now - timedelta(days=1, minutes=index % 120)
        dependent_records.append(
            Trip(
                id=_id("trip", str(index)),
                organization_id=organization_id,
                vehicle_id=vehicle_id,
                driver_id=driver_id,
                started_at=trip_start,
                ended_at=trip_start + timedelta(minutes=45),
                start_latitude=Decimal("37.774900"),
                start_longitude=Decimal("-122.419400"),
                end_latitude=Decimal("37.784900"),
                end_longitude=Decimal("-122.409400"),
                distance_km=Decimal("18.400"),
                energy_used_kwh=Decimal("4.600"),
                status="completed",
            )
        )
        dependent_records.append(
            VehicleRiskSummary(
                id=_id("vehicle-risk", str(index)),
                organization_id=organization_id,
                vehicle_id=vehicle_id,
                window_start=now - timedelta(hours=24),
                window_end=now,
                score=None,
                risk_level="unknown",
                calculation_source="unscored_seed",
            )
        )
        if driver_id is not None:
            dependent_records.append(
                VehicleDriverAssignment(
                    id=_id("assignment", str(index)),
                    organization_id=organization_id,
                    vehicle_id=vehicle_id,
                    driver_id=driver_id,
                    starts_at=now - timedelta(days=30),
                    assignment_source="development_seed",
                )
            )
        if index % 20 == 0:
            dependent_records.append(
                MaintenanceRecord(
                    id=_id("maintenance", str(index)),
                    organization_id=organization_id,
                    vehicle_id=vehicle_id,
                    maintenance_type="inspection",
                    service_at=now - timedelta(days=40),
                    description="Development seed inspection record.",
                    odometer_km=Decimal("12500.000"),
                    cost=Decimal("225.00"),
                    currency="USD",
                    service_provider="Development Service Center",
                    status="completed",
                )
            )
        if index % max(1, vehicle_count // 10) == 0:
            dependent_records.append(
                Alert(
                    id=_id("alert", str(index)),
                    organization_id=organization_id,
                    fleet_id=fleet_id,
                    vehicle_id=vehicle_id,
                    driver_id=driver_id,
                    alert_type="maintenance_review",
                    severity="medium",
                    status="active",
                    message="Development seed alert; no live risk inference has run.",
                    event_at=now - timedelta(hours=2),
                    alert_metadata={"source": "development_seed"},
                )
            )

    session.flush()

    for index, driver_id in enumerate(driver_ids):
        dependent_records.append(
            DriverRiskSummary(
                id=_id("driver-risk", str(index)),
                organization_id=organization_id,
                driver_id=driver_id,
                window_start=now - timedelta(days=7),
                window_end=now,
                score=None,
                risk_level="unknown",
                calculation_source="unscored_seed",
            )
        )

    for index, fleet_id in enumerate(fleet_ids):
        fleet_vehicle_count = min(
            vehicles_per_fleet,
            max(0, vehicle_count - index * vehicles_per_fleet),
        )
        dependent_records.extend(
            [
                FleetRiskSummary(
                    id=_id("fleet-risk", str(index)),
                    organization_id=organization_id,
                    fleet_id=fleet_id,
                    window_start=now - timedelta(hours=24),
                    window_end=now,
                    score=None,
                    risk_level="unknown",
                    vehicle_count=fleet_vehicle_count,
                    high_risk_vehicle_count=None,
                    calculation_source="unscored_seed",
                ),
                FleetCostSummary(
                    id=_id("fleet-cost", str(index)),
                    organization_id=organization_id,
                    fleet_id=fleet_id,
                    period_start=now - timedelta(days=30),
                    period_end=now,
                    total_cost=None,
                    currency="USD",
                    distance_km=None,
                    vehicle_count=fleet_vehicle_count,
                ),
                MaintenanceWorkOrder(
                    id=_id("work-order", str(index)),
                    organization_id=organization_id,
                    vehicle_id=_id("vehicle", str(min(index * vehicles_per_fleet, vehicle_count - 1))),
                    plan_id=plan_ids[index],
                    work_order_number=f"DEV-WO-{index + 1:05d}",
                    maintenance_type="inspection",
                    description="Development seed work order.",
                    priority="normal",
                    status="open",
                    scheduled_for=now + timedelta(days=14),
                ),
            ]
        )

    dependent_records.append(
        AuditLog(
            id=_id("audit", "seed-created"),
            organization_id=organization_id,
            actor_user_id=user_id,
            action="DEVELOPMENT_SEED_CREATED",
            resource_type="organization",
            resource_id=organization_id,
            occurred_at=now,
            result="success",
            audit_metadata={"seed_vehicle_count": vehicle_count},
        )
    )
    session.add_all(dependent_records)
    session.flush()
    return {"created": True, "vehicles": vehicle_count}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = get_settings()
    if not settings.seed_data_enabled:
        logger.info("Development seed disabled")
        return
    parser = argparse.ArgumentParser()
    parser.add_argument("--vehicles", type=int, default=settings.seed_vehicle_count)
    count = parser.parse_args().vehicles
    with get_session_factory().begin() as session:
        result = seed_development_data(session, count)
    logger.info("Development seed result: %s", result)


if __name__ == "__main__":
    import logging

    main()