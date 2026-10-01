from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    desc,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from fleetguard_db.base import Base, TimestampMixin, UUIDPrimaryKey
from fleetguard_db.config import get_settings


class Organization(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "organizations"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_organizations_slug"),
        CheckConstraint("status IN ('active', 'suspended')", name="status"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")


class User(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_users_organization_id"),
        CheckConstraint("status IN ('active', 'disabled', 'invited')", name="status"),
        Index("uq_users_organization_email_lower", "organization_id", func.lower(text("email")), unique=True),
        Index("ix_users_organization_status", "organization_id", "status"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("fleetguard.organizations.id", ondelete="RESTRICT"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="invited")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Role(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_roles_organization_id"),
        UniqueConstraint("organization_id", "name", name="uq_roles_organization_name"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("fleetguard.organizations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    is_system_role: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))


class Permission(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "permissions"
    __table_args__ = (UniqueConstraint("code", name="uq_permissions_code"),)

    code: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "role_id"],
            ["fleetguard.roles.organization_id", "fleetguard.roles.id"],
            ondelete="CASCADE",
            name="fk_role_permissions_role_tenant",
        ),
        Index("ix_role_permissions_permission_id", "permission_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    role_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    permission_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("fleetguard.permissions.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "user_id"],
            ["fleetguard.users.organization_id", "fleetguard.users.id"],
            ondelete="CASCADE",
            name="fk_user_roles_user_tenant",
        ),
        ForeignKeyConstraint(
            ["organization_id", "role_id"],
            ["fleetguard.roles.organization_id", "fleetguard.roles.id"],
            ondelete="CASCADE",
            name="fk_user_roles_role_tenant",
        ),
        Index("ix_user_roles_role_id", "role_id"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    role_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Fleet(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "fleets"
    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_fleets_organization_id"),
        UniqueConstraint("organization_id", "fleet_code", name="uq_fleets_organization_code"),
        CheckConstraint("status IN ('active', 'inactive', 'archived')", name="status"),
        Index("ix_fleets_organization_status", "organization_id", "status"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("fleetguard.organizations.id", ondelete="RESTRICT"), nullable=False
    )
    fleet_code: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")


class Vehicle(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_vehicles_organization_id"),
        UniqueConstraint("organization_id", "vin", name="uq_vehicles_organization_vin"),
        ForeignKeyConstraint(
            ["organization_id", "fleet_id"],
            ["fleetguard.fleets.organization_id", "fleetguard.fleets.id"],
            ondelete="RESTRICT",
            name="fk_vehicles_fleet_tenant",
        ),
        CheckConstraint("status IN ('active', 'inactive', 'maintenance', 'retired')", name="status"),
        CheckConstraint("model_year IS NULL OR model_year BETWEEN 1886 AND 2200", name="model_year"),
        CheckConstraint("fuel_capacity_l IS NULL OR fuel_capacity_l > 0", name="fuel_capacity"),
        CheckConstraint("battery_capacity_kwh IS NULL OR battery_capacity_kwh > 0", name="battery_capacity"),
        CheckConstraint("powertrain_type IN ('ice', 'hybrid', 'plug_in_hybrid', 'electric', 'other')", name="powertrain"),
        Index("ix_vehicles_organization_fleet", "organization_id", "fleet_id"),
        Index("ix_vehicles_organization_status", "organization_id", "status"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    fleet_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    vin: Mapped[str] = mapped_column(String(32), nullable=False)
    make: Mapped[str | None] = mapped_column(String(100))
    model: Mapped[str | None] = mapped_column(String(100))
    model_year: Mapped[int | None] = mapped_column(Integer)
    vehicle_type: Mapped[str] = mapped_column(String(60), nullable=False)
    powertrain_type: Mapped[str] = mapped_column(String(30), nullable=False)
    fuel_type: Mapped[str | None] = mapped_column(String(40))
    fuel_capacity_l: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    battery_capacity_kwh: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")


class Driver(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "drivers"
    __table_args__ = (
        UniqueConstraint("organization_id", "id", name="uq_drivers_organization_id"),
        CheckConstraint("status IN ('active', 'inactive', 'suspended')", name="status"),
        Index("ix_drivers_organization_status", "organization_id", "status"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("fleetguard.organizations.id", ondelete="RESTRICT"), nullable=False
    )
    external_driver_id: Mapped[str | None] = mapped_column(String(100))
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    license_class: Mapped[str | None] = mapped_column(String(40))
    license_region: Mapped[str | None] = mapped_column(String(80))
    license_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class VehicleDriverAssignment(UUIDPrimaryKey, Base):
    __tablename__ = "vehicle_driver_assignments"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "vehicle_id"],
            ["fleetguard.vehicles.organization_id", "fleetguard.vehicles.id"],
            ondelete="RESTRICT",
            name="fk_assignments_vehicle_tenant",
        ),
        ForeignKeyConstraint(
            ["organization_id", "driver_id"],
            ["fleetguard.drivers.organization_id", "fleetguard.drivers.id"],
            ondelete="RESTRICT",
            name="fk_assignments_driver_tenant",
        ),
        CheckConstraint("ends_at IS NULL OR ends_at > starts_at", name="assignment_dates"),
        Index("ix_assignments_vehicle_started", "organization_id", "vehicle_id", desc("starts_at")),
        Index("ix_assignments_driver_started", "organization_id", "driver_id", desc("starts_at")),
        Index(
            "uq_assignments_active_vehicle",
            "organization_id",
            "vehicle_id",
            unique=True,
            postgresql_where=text("ends_at IS NULL"),
        ),
        Index(
            "uq_assignments_active_driver",
            "organization_id",
            "driver_id",
            unique=True,
            postgresql_where=text("ends_at IS NULL"),
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    vehicle_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    driver_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assignment_source: Mapped[str] = mapped_column(String(40), nullable=False, server_default="manual")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Trip(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "trips"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "vehicle_id"],
            ["fleetguard.vehicles.organization_id", "fleetguard.vehicles.id"],
            ondelete="RESTRICT",
            name="fk_trips_vehicle_tenant",
        ),
        ForeignKeyConstraint(
            ["organization_id", "driver_id"],
            ["fleetguard.drivers.organization_id", "fleetguard.drivers.id"],
            ondelete="RESTRICT",
            name="fk_trips_driver_tenant",
        ),
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="trip_dates"),
        CheckConstraint("distance_km IS NULL OR distance_km >= 0", name="distance"),
        CheckConstraint("fuel_used_l IS NULL OR fuel_used_l >= 0", name="fuel_used"),
        CheckConstraint("energy_used_kwh IS NULL OR energy_used_kwh >= 0", name="energy_used"),
        CheckConstraint("status IN ('in_progress', 'completed', 'cancelled')", name="status"),
        CheckConstraint("start_latitude IS NULL OR start_latitude BETWEEN -90 AND 90", name="start_latitude"),
        CheckConstraint("start_longitude IS NULL OR start_longitude BETWEEN -180 AND 180", name="start_longitude"),
        CheckConstraint("end_latitude IS NULL OR end_latitude BETWEEN -90 AND 90", name="end_latitude"),
        CheckConstraint("end_longitude IS NULL OR end_longitude BETWEEN -180 AND 180", name="end_longitude"),
        Index("ix_trips_vehicle_started", "organization_id", "vehicle_id", desc("started_at")),
        Index("ix_trips_driver_started", "organization_id", "driver_id", desc("started_at")),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    vehicle_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    driver_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    start_latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    start_longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    end_latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    end_longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    fuel_used_l: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    energy_used_kwh: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="in_progress")


class MaintenanceRecord(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "maintenance_records"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "vehicle_id"],
            ["fleetguard.vehicles.organization_id", "fleetguard.vehicles.id"],
            ondelete="RESTRICT",
            name="fk_maintenance_vehicle_tenant",
        ),
        CheckConstraint("status IN ('planned', 'scheduled', 'completed', 'cancelled')", name="status"),
        CheckConstraint("cost IS NULL OR cost >= 0", name="cost"),
        CheckConstraint("odometer_km IS NULL OR odometer_km >= 0", name="odometer"),
        Index("ix_maintenance_vehicle_service", "organization_id", "vehicle_id", desc("service_at")),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    vehicle_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    maintenance_type: Mapped[str] = mapped_column(String(80), nullable=False)
    service_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    odometer_km: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[str | None] = mapped_column(String(3))
    service_provider: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="planned")
    service_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )


class Alert(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "alerts"
    __table_args__ = (
    UniqueConstraint("organization_id", "id", name="uq_alerts_organization_id"),
        ForeignKeyConstraint(
            ["organization_id", "fleet_id"],
            ["fleetguard.fleets.organization_id", "fleetguard.fleets.id"],
            ondelete="RESTRICT",
            name="fk_alerts_fleet_tenant",
        ),
        ForeignKeyConstraint(
            ["organization_id", "vehicle_id"],
            ["fleetguard.vehicles.organization_id", "fleetguard.vehicles.id"],
            ondelete="RESTRICT",
            name="fk_alerts_vehicle_tenant",
        ),
        ForeignKeyConstraint(
            ["organization_id", "driver_id"],
            ["fleetguard.drivers.organization_id", "fleetguard.drivers.id"],
            ondelete="RESTRICT",
            name="fk_alerts_driver_tenant",
        ),
        ForeignKeyConstraint(
            ["organization_id", "acknowledged_by_user_id"],
            ["fleetguard.users.organization_id", "fleetguard.users.id"],
            ondelete="RESTRICT",
            name="fk_alerts_acknowledged_user_tenant",
        ),
        CheckConstraint("severity IN ('info', 'low', 'medium', 'high', 'critical')", name="severity"),
        CheckConstraint("status IN ('active', 'acknowledged', 'resolved', 'dismissed')", name="status"),
        CheckConstraint("resolved_at IS NULL OR resolved_at >= event_at", name="resolved_after_event"),
        Index("ix_alerts_vehicle_created", "organization_id", "vehicle_id", desc("created_at")),
        Index("ix_alerts_fleet_status_severity", "organization_id", "fleet_id", "status", "severity"),
        Index("ix_alerts_organization_status_severity_time", "organization_id", "status", "severity", desc("created_at")),
        Index("ix_alerts_recent", "organization_id", desc("created_at")),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("fleetguard.organizations.id", ondelete="RESTRICT"), nullable=False
    )
    fleet_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    vehicle_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    driver_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_by_user_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    alert_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )


class AlertAcknowledgement(UUIDPrimaryKey, Base):
    __tablename__ = "alert_acknowledgements"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "alert_id"],
            ["fleetguard.alerts.organization_id", "fleetguard.alerts.id"],
            ondelete="CASCADE",
            name="fk_alert_acknowledgements_alert_tenant",
        ),
        ForeignKeyConstraint(
            ["organization_id", "user_id"],
            ["fleetguard.users.organization_id", "fleetguard.users.id"],
            ondelete="RESTRICT",
            name="fk_alert_acknowledgements_user_tenant",
        ),
        Index("ix_alert_acknowledgements_alert_time", "organization_id", "alert_id", desc("acknowledged_at")),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    alert_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    acknowledged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    note: Mapped[str | None] = mapped_column(Text)


class MaintenancePlan(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "maintenance_plans"
    __table_args__ = (
    UniqueConstraint("organization_id", "id", name="uq_maintenance_plans_organization_id"),
        ForeignKeyConstraint(
            ["organization_id", "fleet_id"],
            ["fleetguard.fleets.organization_id", "fleetguard.fleets.id"],
            ondelete="CASCADE",
            name="fk_maintenance_plans_fleet_tenant",
        ),
        ForeignKeyConstraint(
            ["organization_id", "vehicle_id"],
            ["fleetguard.vehicles.organization_id", "fleetguard.vehicles.id"],
            ondelete="CASCADE",
            name="fk_maintenance_plans_vehicle_tenant",
        ),
        CheckConstraint("fleet_id IS NOT NULL OR vehicle_id IS NOT NULL", name="target_required"),
        CheckConstraint("interval_days IS NULL OR interval_days > 0", name="interval_days"),
        CheckConstraint("interval_distance_km IS NULL OR interval_distance_km > 0", name="interval_distance"),
        CheckConstraint("status IN ('active', 'paused', 'retired')", name="status"),
        Index("ix_maintenance_plans_fleet_status", "organization_id", "fleet_id", "status"),
        Index("ix_maintenance_plans_vehicle_status", "organization_id", "vehicle_id", "status"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("fleetguard.organizations.id", ondelete="CASCADE"), nullable=False
    )
    fleet_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    vehicle_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    maintenance_type: Mapped[str] = mapped_column(String(80), nullable=False)
    interval_days: Mapped[int | None] = mapped_column(Integer)
    interval_distance_km: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    plan_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )


class MaintenanceWorkOrder(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "maintenance_work_orders"
    __table_args__ = (
        UniqueConstraint("organization_id", "work_order_number", name="uq_work_orders_organization_number"),
        ForeignKeyConstraint(
            ["organization_id", "vehicle_id"],
            ["fleetguard.vehicles.organization_id", "fleetguard.vehicles.id"],
            ondelete="RESTRICT",
            name="fk_work_orders_vehicle_tenant",
        ),
        ForeignKeyConstraint(
            ["organization_id", "plan_id"],
            ["fleetguard.maintenance_plans.organization_id", "fleetguard.maintenance_plans.id"],
            ondelete="RESTRICT",
            name="fk_work_orders_plan_tenant",
        ),
        CheckConstraint("status IN ('open', 'scheduled', 'in_progress', 'completed', 'cancelled')", name="status"),
        CheckConstraint("priority IN ('low', 'normal', 'high', 'urgent')", name="priority"),
        CheckConstraint("estimated_cost IS NULL OR estimated_cost >= 0", name="estimated_cost"),
        Index("ix_work_orders_vehicle_status", "organization_id", "vehicle_id", "status"),
        Index("ix_work_orders_due", "organization_id", "status", "scheduled_for"),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    vehicle_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    plan_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    work_order_number: Mapped[str] = mapped_column(String(80), nullable=False)
    maintenance_type: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, server_default="normal")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="open")
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    estimated_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    currency: Mapped[str | None] = mapped_column(String(3))


class VehicleRiskSummary(UUIDPrimaryKey, Base):
    __tablename__ = "vehicle_risk_summaries"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "vehicle_id"],
            ["fleetguard.vehicles.organization_id", "fleetguard.vehicles.id"],
            ondelete="CASCADE",
            name="fk_vehicle_risk_vehicle_tenant",
        ),
        UniqueConstraint("organization_id", "vehicle_id", "window_start", "window_end", name="uq_vehicle_risk_window"),
        CheckConstraint("window_end > window_start", name="window_dates"),
        CheckConstraint("score IS NULL OR score BETWEEN 0 AND 100", name="score_range"),
        CheckConstraint("risk_level IN ('unknown', 'low', 'medium', 'high', 'critical')", name="risk_level"),
        Index("ix_vehicle_risk_latest", "organization_id", "vehicle_id", desc("window_end")),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    vehicle_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, server_default="unknown")
    calculation_source: Mapped[str | None] = mapped_column(String(40))
    model_name: Mapped[str | None] = mapped_column(String(100))
    model_version: Mapped[str | None] = mapped_column(String(100))
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    features: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class DriverRiskSummary(UUIDPrimaryKey, Base):
    __tablename__ = "driver_risk_summaries"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "driver_id"],
            ["fleetguard.drivers.organization_id", "fleetguard.drivers.id"],
            ondelete="CASCADE",
            name="fk_driver_risk_driver_tenant",
        ),
        UniqueConstraint("organization_id", "driver_id", "window_start", "window_end", name="uq_driver_risk_window"),
        CheckConstraint("window_end > window_start", name="window_dates"),
        CheckConstraint("score IS NULL OR score BETWEEN 0 AND 100", name="score_range"),
        CheckConstraint("risk_level IN ('unknown', 'low', 'medium', 'high', 'critical')", name="risk_level"),
        Index("ix_driver_risk_latest", "organization_id", "driver_id", desc("window_end")),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    driver_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, server_default="unknown")
    calculation_source: Mapped[str | None] = mapped_column(String(40))
    model_name: Mapped[str | None] = mapped_column(String(100))
    model_version: Mapped[str | None] = mapped_column(String(100))
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    features: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class FleetRiskSummary(UUIDPrimaryKey, Base):
    __tablename__ = "fleet_risk_summaries"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "fleet_id"],
            ["fleetguard.fleets.organization_id", "fleetguard.fleets.id"],
            ondelete="CASCADE",
            name="fk_fleet_risk_fleet_tenant",
        ),
        UniqueConstraint("organization_id", "fleet_id", "window_start", "window_end", name="uq_fleet_risk_window"),
        CheckConstraint("window_end > window_start", name="window_dates"),
        CheckConstraint("score IS NULL OR score BETWEEN 0 AND 100", name="score_range"),
        CheckConstraint("risk_level IN ('unknown', 'low', 'medium', 'high', 'critical')", name="risk_level"),
        CheckConstraint(
            "vehicle_count >= 0 AND (high_risk_vehicle_count IS NULL OR high_risk_vehicle_count >= 0)",
            name="vehicle_counts",
        ),
        Index("ix_fleet_risk_latest", "organization_id", "fleet_id", desc("window_end")),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    fleet_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, server_default="unknown")
    vehicle_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    high_risk_vehicle_count: Mapped[int | None] = mapped_column(Integer)
    calculation_source: Mapped[str | None] = mapped_column(String(40))
    model_version: Mapped[str | None] = mapped_column(String(100))
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class FleetCostSummary(UUIDPrimaryKey, Base):
    __tablename__ = "fleet_cost_summaries"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "fleet_id"],
            ["fleetguard.fleets.organization_id", "fleetguard.fleets.id"],
            ondelete="CASCADE",
            name="fk_fleet_cost_fleet_tenant",
        ),
        UniqueConstraint("organization_id", "fleet_id", "period_start", "period_end", name="uq_fleet_cost_period"),
        CheckConstraint("period_end > period_start", name="period_dates"),
        CheckConstraint("total_cost IS NULL OR total_cost >= 0", name="total_cost"),
        CheckConstraint("distance_km IS NULL OR distance_km >= 0", name="distance"),
        Index("ix_fleet_cost_latest", "organization_id", "fleet_id", desc("period_end")),
    )

    organization_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    fleet_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(16, 2))
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    distance_km: Mapped[Decimal | None] = mapped_column(Numeric(16, 3))
    vehicle_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Subscription(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint("status IN ('trial', 'active', 'past_due', 'cancelled', 'expired')", name="status"),
        CheckConstraint("ends_at IS NULL OR ends_at > starts_at", name="subscription_dates"),
        Index("ix_subscriptions_organization_status", "organization_id", "status"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("fleetguard.organizations.id", ondelete="RESTRICT"), nullable=False
    )
    plan_code: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="trial")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    seat_limit: Mapped[int | None] = mapped_column(Integer)
    external_reference: Mapped[str | None] = mapped_column(String(200))


class AuditLog(UUIDPrimaryKey, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id", "actor_user_id"],
            ["fleetguard.users.organization_id", "fleetguard.users.id"],
            ondelete="SET NULL",
            name="fk_audit_actor_tenant",
        ),
        Index("ix_audit_organization_time", "organization_id", desc("occurred_at")),
        Index("ix_audit_resource_time", "organization_id", "resource_type", "resource_id", desc("occurred_at")),
        Index("ix_audit_request_id", "request_id"),
    )

    organization_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("fleetguard.organizations.id", ondelete="SET NULL")
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ip_address: Mapped[str | None] = mapped_column(INET)
    request_id: Mapped[str | None] = mapped_column(String(160))
    result: Mapped[str] = mapped_column(String(30), nullable=False, server_default="success")
    audit_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )


class KnowledgeDocument(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "knowledge_documents"
    __table_args__ = (
        ForeignKeyConstraint(
            ["organization_id"], ["fleetguard.organizations.id"], ondelete="CASCADE",
            name="fk_knowledge_documents_organization",
        ),
        Index("ix_knowledge_documents_type", "document_type", "created_at"),
        Index("ix_knowledge_documents_fault_code", "fault_code"),
    )

    organization_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    document_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(500), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(500))
    fault_code: Mapped[str | None] = mapped_column(String(40))
    vehicle_make: Mapped[str | None] = mapped_column(String(100))
    vehicle_model: Mapped[str | None] = mapped_column(String(100))
    document_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))


class KnowledgeChunk(UUIDPrimaryKey, Base):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (
        ForeignKeyConstraint(
            ["document_id"], ["fleetguard.knowledge_documents.id"], ondelete="CASCADE",
            name="fk_knowledge_chunks_document",
        ),
        UniqueConstraint("document_id", "chunk_index", name="uq_knowledge_chunks_document_index"),
        Index("ix_knowledge_chunks_document", "document_id", "chunk_index"),
        Index(
            "ix_knowledge_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    document_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(get_settings().pgvector_embedding_dimension), nullable=True
    )
    embedding_model: Mapped[str | None] = mapped_column(String(160))
    embedding_dimensions: Mapped[int | None] = mapped_column(Integer)
    chunk_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )