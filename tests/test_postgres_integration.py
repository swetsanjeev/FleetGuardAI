from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fleetguard_db.base import SCHEMA_NAME
from fleetguard_db.models import (
    Driver,
    Fleet,
    KnowledgeChunk,
    KnowledgeDocument,
    Organization,
    Vehicle,
    VehicleRiskSummary,
)
from fleetguard_db.repositories import FleetRepository, search_knowledge_chunks
from fleetguard_db.seed import seed_development_data


def _organization(slug: str) -> Organization:
    return Organization(name=f"Organization {slug}", slug=slug, status="active")


def _vehicle(organization_id, fleet_id, suffix: int) -> Vehicle:
    return Vehicle(
        organization_id=organization_id,
        fleet_id=fleet_id,
        vin=f"TEST{suffix:014d}",
        vehicle_type="delivery_van",
        powertrain_type="electric",
        status="active",
    )


def test_initial_migration_creates_domain_tables_indexes_and_vector(postgres_engine) -> None:
    inspector = inspect(postgres_engine)
    table_names = set(inspector.get_table_names(schema=SCHEMA_NAME))
    assert {
        "organizations",
        "users",
        "roles",
        "permissions",
        "fleets",
        "vehicles",
        "drivers",
        "vehicle_driver_assignments",
        "trips",
        "maintenance_plans",
        "maintenance_records",
        "maintenance_work_orders",
        "alerts",
        "alert_acknowledgements",
        "vehicle_risk_summaries",
        "driver_risk_summaries",
        "fleet_risk_summaries",
        "fleet_cost_summaries",
        "subscriptions",
        "audit_logs",
        "knowledge_documents",
        "knowledge_chunks",
    } <= table_names
    vehicle_indexes = {index["name"] for index in inspector.get_indexes("vehicles", schema=SCHEMA_NAME)}
    assert "ix_vehicles_organization_fleet" in vehicle_indexes
    assert "ix_vehicles_organization_status" in vehicle_indexes
    chunk_indexes = {index["name"] for index in inspector.get_indexes("knowledge_chunks", schema=SCHEMA_NAME)}
    assert "ix_knowledge_chunks_embedding_hnsw" in chunk_indexes
    with postgres_engine.connect() as connection:
        extension = connection.scalar(text("SELECT extversion FROM pg_extension WHERE extname = 'vector'"))
    assert extension is not None


def test_vehicle_crud_and_tenant_composite_foreign_key(postgres_session: Session) -> None:
    organization = _organization(f"org-{uuid4().hex[:10]}")
    other_organization = _organization(f"org-{uuid4().hex[:10]}")
    postgres_session.add_all([organization, other_organization])
    postgres_session.flush()
    fleet = Fleet(
        organization_id=organization.id,
        fleet_code="FLEET-A",
        name="Fleet A",
        status="active",
    )
    other_fleet = Fleet(
        organization_id=other_organization.id,
        fleet_code="FLEET-B",
        name="Fleet B",
        status="active",
    )
    postgres_session.add_all([fleet, other_fleet])
    postgres_session.flush()
    vehicle = _vehicle(organization.id, fleet.id, 1)
    postgres_session.add(vehicle)
    postgres_session.flush()

    assert postgres_session.get(Vehicle, vehicle.id).vin == vehicle.vin
    invalid_vehicle = _vehicle(organization.id, other_fleet.id, 2)
    postgres_session.add(invalid_vehicle)
    with pytest.raises(IntegrityError):
        postgres_session.flush()


def test_vehicle_repository_keyset_pagination(postgres_session: Session) -> None:
    organization = _organization(f"org-{uuid4().hex[:10]}")
    postgres_session.add(organization)
    postgres_session.flush()
    fleet = Fleet(
        organization_id=organization.id,
        fleet_code="FLEET-PAGE",
        name="Pagination Fleet",
        status="active",
    )
    postgres_session.add(fleet)
    postgres_session.flush()
    vehicles = [_vehicle(organization.id, fleet.id, index) for index in range(10, 15)]
    postgres_session.add_all(vehicles)
    postgres_session.flush()

    repository = FleetRepository(postgres_session)
    first = repository.list_vehicles(organization.id, fleet_id=fleet.id, limit=2)
    second = repository.list_vehicles(
        organization.id,
        fleet_id=fleet.id,
        after_id=first[-1].id,
        limit=2,
    )

    assert len(first) == len(second) == 2
    assert first[-1].id < second[0].id
    assert not ({vehicle.id for vehicle in first} & {vehicle.id for vehicle in second})
    with pytest.raises(ValueError):
        repository.list_vehicles(organization.id, limit=0)


def test_transaction_rollback_removes_uncommitted_record(postgres_session: Session) -> None:
    organization = _organization(f"org-{uuid4().hex[:10]}")
    postgres_session.add(organization)
    postgres_session.flush()
    organization_id = organization.id

    postgres_session.rollback()

    assert postgres_session.scalar(select(Organization.id).where(Organization.id == organization_id)) is None


def test_high_risk_repository_uses_latest_window_and_tenant_scope(postgres_session: Session) -> None:
    organization = _organization(f"org-{uuid4().hex[:10]}")
    other_organization = _organization(f"org-{uuid4().hex[:10]}")
    postgres_session.add_all([organization, other_organization])
    postgres_session.flush()
    fleet = Fleet(organization_id=organization.id, fleet_code="RISK-A", name="Risk Fleet", status="active")
    other_fleet = Fleet(
        organization_id=other_organization.id,
        fleet_code="RISK-B",
        name="Other Fleet",
        status="active",
    )
    postgres_session.add_all([fleet, other_fleet])
    postgres_session.flush()
    vehicle = _vehicle(organization.id, fleet.id, 91)
    eligible_vehicle = _vehicle(organization.id, fleet.id, 93)
    other_vehicle = _vehicle(other_organization.id, other_fleet.id, 92)
    postgres_session.add_all([vehicle, eligible_vehicle, other_vehicle])
    postgres_session.flush()
    window_end = datetime.now(timezone.utc).replace(microsecond=0)
    postgres_session.add_all(
        [
            VehicleRiskSummary(
                organization_id=organization.id,
                vehicle_id=vehicle.id,
                window_start=window_end - timedelta(hours=48),
                window_end=window_end - timedelta(hours=24),
                score=Decimal("98.00"),
                risk_level="critical",
                calculation_source="test",
            ),
            VehicleRiskSummary(
                organization_id=organization.id,
                vehicle_id=vehicle.id,
                window_start=window_end - timedelta(hours=24),
                window_end=window_end,
                score=Decimal("22.00"),
                risk_level="low",
                calculation_source="test",
            ),
            VehicleRiskSummary(
                organization_id=organization.id,
                vehicle_id=eligible_vehicle.id,
                window_start=window_end - timedelta(hours=24),
                window_end=window_end,
                score=Decimal("88.00"),
                risk_level="critical",
                calculation_source="test",
            ),
            VehicleRiskSummary(
                organization_id=other_organization.id,
                vehicle_id=other_vehicle.id,
                window_start=window_end - timedelta(hours=24),
                window_end=window_end,
                score=Decimal("99.00"),
                risk_level="critical",
                calculation_source="test",
            ),
        ]
    )
    postgres_session.flush()

    results = FleetRepository(postgres_session).high_risk_vehicles(
        organization.id, fleet_id=fleet.id, limit=10
    )

    assert len(results) == 1
    assert results[0][0].id == eligible_vehicle.id
    assert results[0][1] == Decimal("88.00")
    assert results[0][2] == "critical"


def test_seed_data_is_deterministic_idempotent_and_unscored(postgres_session: Session) -> None:
    first = seed_development_data(postgres_session, vehicle_count=10)
    second = seed_development_data(postgres_session, vehicle_count=10)
    organization = postgres_session.scalar(
        select(Organization).where(Organization.slug == "fleetguard-development")
    )

    assert first == {"created": True, "vehicles": 10}
    assert second == {"created": False, "vehicles": 0}
    vehicle_summaries = list(
        postgres_session.scalars(
            select(VehicleRiskSummary).where(VehicleRiskSummary.organization_id == organization.id)
        )
    )
    assert len(vehicle_summaries) == 10
    assert all(summary.score is None and summary.risk_level == "unknown" for summary in vehicle_summaries)
    with pytest.raises(ValueError):
        seed_development_data(postgres_session, vehicle_count=10_001)


def test_vector_document_chunk_insert_and_cosine_query(postgres_session: Session) -> None:
    organization = _organization(f"org-{uuid4().hex[:10]}")
    postgres_session.add(organization)
    postgres_session.flush()
    document = KnowledgeDocument(
        organization_id=organization.id,
        document_type="maintenance_manual",
        title="Test manual",
        source="integration-test",
        is_active=True,
    )
    postgres_session.add(document)
    postgres_session.flush()
    embedding = [1.0] + [0.0] * 1535
    chunk = KnowledgeChunk(
        document_id=document.id,
        chunk_index=0,
        content="Replace the cabin air filter every year.",
        embedding=embedding,
        embedding_model="test-configured-vector",
        embedding_dimensions=len(embedding),
    )
    postgres_session.add(chunk)
    postgres_session.flush()

    matches = search_knowledge_chunks(
        postgres_session,
        embedding,
        organization_id=organization.id,
        document_type="maintenance_manual",
    )

    assert matches[0][0].id == chunk.id
    assert matches[0][1] == pytest.approx(0.0, abs=1e-6)
    with pytest.raises(ValueError):
        search_knowledge_chunks(postgres_session, [0.0] * 3)


def test_migration_downgrade_and_reupgrade(postgres_engine) -> None:
    config = Config(str(__import__("pathlib").Path(__file__).resolve().parents[1] / "services" / "api" / "alembic.ini"))
    command.downgrade(config, "base")
    assert "vehicles" not in inspect(postgres_engine).get_table_names(schema=SCHEMA_NAME)

    command.upgrade(config, "head")

    assert "vehicles" in inspect(postgres_engine).get_table_names(schema=SCHEMA_NAME)