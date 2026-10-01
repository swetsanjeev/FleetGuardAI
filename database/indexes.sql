CREATE INDEX idx_vehicles_fleet ON vehicles(fleet_id);
CREATE INDEX idx_trips_vehicle ON trips(vehicle_vin);
CREATE INDEX idx_trips_started ON trips(started_at);
CREATE INDEX idx_alerts_vehicle ON alerts(vehicle_vin);
CREATE INDEX idx_alerts_severity ON alerts(severity);
CREATE INDEX idx_maintenance_vin ON maintenance_records(vehicle_vin);
CREATE INDEX idx_risk_vin ON risk_assessments(vehicle_vin);
