from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from fleetguard_db.config import get_settings
from fleetguard_db.models import (
    Alert,
    AuditLog,
    DriverRiskSummary,
    Fleet,
    FleetCostSummary,
    FleetRiskSummary,
    KnowledgeChunk,
    KnowledgeDocument,
    MaintenanceRecord,
    Trip,
    Vehicle,
    VehicleRiskSummary,
)


class FleetRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_vehicles(
        self,
        organization_id: UUID,
        fleet_id: UUID | None = None,
        status: str | None = None,
        after_id: UUID | None = None,
        limit: int = 100,
    ) -> list[Vehicle]:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        statement = select(Vehicle).where(Vehicle.organization_id == organization_id)
        if fleet_id is not None:
            statement = statement.where(Vehicle.fleet_id == fleet_id)
        if status is not None:
            statement = statement.where(Vehicle.status == status)
        if after_id is not None:
            statement = statement.where(Vehicle.id > after_id)
        return list(self.session.scalars(statement.order_by(Vehicle.id).limit(limit)))

    def get_vehicle(self, organization_id: UUID, vehicle_id: UUID) -> Vehicle | None:
        return self.session.scalar(
            select(Vehicle).where(
                Vehicle.organization_id == organization_id,
                Vehicle.id == vehicle_id,
            )
        )

    def maintenance_history(
        self, organization_id: UUID, vehicle_id: UUID, limit: int = 100
    ) -> list[MaintenanceRecord]:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        statement = (
            select(MaintenanceRecord)
            .where(
                MaintenanceRecord.organization_id == organization_id,
                MaintenanceRecord.vehicle_id == vehicle_id,
            )
            .order_by(MaintenanceRecord.service_at.desc().nullslast(), MaintenanceRecord.id)
            .limit(limit)
        )
        return list(self.session.scalars(statement))

    def vehicle_alerts(
        self,
        organization_id: UUID,
        vehicle_id: UUID,
        status: str | None = None,
        limit: int = 100,
    ) -> list[Alert]:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        statement = select(Alert).where(
            Alert.organization_id == organization_id,
            Alert.vehicle_id == vehicle_id,
        )
        if status is not None:
            statement = statement.where(Alert.status == status)
        return list(self.session.scalars(statement.order_by(Alert.created_at.desc(), Alert.id).limit(limit)))

    def vehicle_trips(
        self,
        organization_id: UUID,
        vehicle_id: UUID,
        before: tuple[datetime, UUID] | None = None,
        limit: int = 100,
    ) -> list[Trip]:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        statement = select(Trip).where(
            Trip.organization_id == organization_id,
            Trip.vehicle_id == vehicle_id,
        )
        if before is not None:
            before_time, before_id = before
            statement = statement.where(
                or_(
                    Trip.started_at < before_time,
                    and_(Trip.started_at == before_time, Trip.id < before_id),
                )
            )
        return list(self.session.scalars(statement.order_by(Trip.started_at.desc(), Trip.id.desc()).limit(limit)))

    def latest_vehicle_risk(
        self, organization_id: UUID, vehicle_id: UUID
    ) -> VehicleRiskSummary | None:
        return self.session.scalar(
            select(VehicleRiskSummary)
            .where(
                VehicleRiskSummary.organization_id == organization_id,
                VehicleRiskSummary.vehicle_id == vehicle_id,
            )
            .order_by(VehicleRiskSummary.window_end.desc())
            .limit(1)
        )

    def high_risk_vehicles(
        self,
        organization_id: UUID,
        fleet_id: UUID | None = None,
        limit: int = 100,
    ) -> list[tuple[Vehicle, Decimal | None, str, datetime]]:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        latest_risk = (
            select(
                VehicleRiskSummary.organization_id.label("organization_id"),
                VehicleRiskSummary.vehicle_id.label("vehicle_id"),
                VehicleRiskSummary.score.label("score"),
                VehicleRiskSummary.risk_level.label("risk_level"),
                VehicleRiskSummary.window_end.label("window_end"),
                func.row_number()
                .over(
                    partition_by=(VehicleRiskSummary.organization_id, VehicleRiskSummary.vehicle_id),
                    order_by=(VehicleRiskSummary.window_end.desc(), VehicleRiskSummary.id.desc()),
                )
                .label("risk_rank"),
            )
            .where(VehicleRiskSummary.organization_id == organization_id)
            .subquery()
        )
        statement = (
            select(Vehicle, latest_risk.c.score, latest_risk.c.risk_level, latest_risk.c.window_end)
            .join(
                latest_risk,
                and_(
                    latest_risk.c.organization_id == Vehicle.organization_id,
                    latest_risk.c.vehicle_id == Vehicle.id,
                ),
            )
            .where(
                Vehicle.organization_id == organization_id,
                latest_risk.c.risk_rank == 1,
                latest_risk.c.risk_level.in_(("high", "critical")),
            )
        )
        if fleet_id is not None:
            statement = statement.where(Vehicle.fleet_id == fleet_id)
        statement = statement.order_by(latest_risk.c.score.desc().nullslast(), Vehicle.id).limit(limit)
        return list(self.session.execute(statement).all())

    def driver_risk(
        self, organization_id: UUID, driver_id: UUID
    ) -> DriverRiskSummary | None:
        return self.session.scalar(
            select(DriverRiskSummary)
            .where(
                DriverRiskSummary.organization_id == organization_id,
                DriverRiskSummary.driver_id == driver_id,
            )
            .order_by(DriverRiskSummary.window_end.desc())
            .limit(1)
        )

    def fleet_summary(self, organization_id: UUID, fleet_id: UUID) -> dict[str, int | str]:
        fleet_exists = self.session.scalar(
            select(Fleet.id).where(
                Fleet.organization_id == organization_id,
                Fleet.id == fleet_id,
            )
        )
        if fleet_exists is None:
            raise LookupError("fleet not found")
        vehicle_count = self.session.scalar(
            select(func.count()).select_from(Vehicle).where(
                Vehicle.organization_id == organization_id,
                Vehicle.fleet_id == fleet_id,
                Vehicle.status == "active",
            )
        )
        active_alert_count = self.session.scalar(
            select(func.count()).select_from(Alert).where(
                Alert.organization_id == organization_id,
                Alert.fleet_id == fleet_id,
                Alert.status == "active",
            )
        )
        return {
            "fleet_id": str(fleet_id),
            "active_vehicle_count": int(vehicle_count or 0),
            "active_alert_count": int(active_alert_count or 0),
        }

    def latest_fleet_risk(
        self, organization_id: UUID, fleet_id: UUID
    ) -> FleetRiskSummary | None:
        return self.session.scalar(
            select(FleetRiskSummary)
            .where(
                FleetRiskSummary.organization_id == organization_id,
                FleetRiskSummary.fleet_id == fleet_id,
            )
            .order_by(FleetRiskSummary.window_end.desc())
            .limit(1)
        )

    def latest_fleet_cost(
        self, organization_id: UUID, fleet_id: UUID
    ) -> FleetCostSummary | None:
        return self.session.scalar(
            select(FleetCostSummary)
            .where(
                FleetCostSummary.organization_id == organization_id,
                FleetCostSummary.fleet_id == fleet_id,
            )
            .order_by(FleetCostSummary.period_end.desc())
            .limit(1)
        )

    def recent_alerts(
        self,
        organization_id: UUID,
        status: str | None = "active",
        severity: str | None = None,
        before: tuple[datetime, UUID] | None = None,
        limit: int = 100,
    ) -> list[Alert]:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        statement = select(Alert).where(Alert.organization_id == organization_id)
        if status is not None:
            statement = statement.where(Alert.status == status)
        if severity is not None:
            statement = statement.where(Alert.severity == severity)
        if before is not None:
            before_time, before_id = before
            statement = statement.where(
                or_(
                    Alert.created_at < before_time,
                    and_(Alert.created_at == before_time, Alert.id < before_id),
                )
            )
        return list(self.session.scalars(statement.order_by(Alert.created_at.desc(), Alert.id.desc()).limit(limit)))

    def audit_history(
        self,
        organization_id: UUID,
        before: tuple[datetime, UUID] | None = None,
        limit: int = 100,
    ) -> list[AuditLog]:
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        statement = select(AuditLog).where(AuditLog.organization_id == organization_id)
        if before is not None:
            before_time, before_id = before
            statement = statement.where(
                or_(
                    AuditLog.occurred_at < before_time,
                    and_(AuditLog.occurred_at == before_time, AuditLog.id < before_id),
                )
            )
        return list(self.session.scalars(statement.order_by(AuditLog.occurred_at.desc(), AuditLog.id.desc()).limit(limit)))


def search_knowledge_chunks(
    session: Session,
    embedding: list[float],
    limit: int = 10,
    organization_id: UUID | None = None,
    document_type: str | None = None,
) -> list[tuple[KnowledgeChunk, float]]:
    expected_dimensions = get_settings().pgvector_embedding_dimension
    if len(embedding) != expected_dimensions:
        raise ValueError(f"embedding must contain {expected_dimensions} values")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    distance = KnowledgeChunk.embedding.cosine_distance(embedding).label("distance")
    statement = (
        select(KnowledgeChunk, distance)
        .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
        .where(KnowledgeDocument.is_active.is_(True), KnowledgeChunk.embedding.is_not(None))
    )
    if organization_id is not None:
        statement = statement.where(
            or_(
                KnowledgeDocument.organization_id.is_(None),
                KnowledgeDocument.organization_id == organization_id,
            )
        )
    if document_type is not None:
        statement = statement.where(KnowledgeDocument.document_type == document_type)
    return list(session.execute(statement.order_by(distance).limit(limit)).all())