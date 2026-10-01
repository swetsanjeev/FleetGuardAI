-- FleetGuard AI core schema
CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  plan TEXT NOT NULL DEFAULT 'starter'
);

CREATE TABLE fleets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID REFERENCES organizations(id),
  name TEXT NOT NULL,
  region TEXT
);

CREATE TABLE vehicles (
  vin TEXT PRIMARY KEY,
  fleet_id UUID REFERENCES fleets(id),
  model TEXT,
  year INT,
  battery_soc NUMERIC,
  battery_soh NUMERIC,
  odometer_km NUMERIC,
  status TEXT
);

CREATE TABLE drivers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name TEXT NOT NULL,
  license_no TEXT UNIQUE,
  safety_score NUMERIC
);

CREATE TABLE trips (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vehicle_vin TEXT REFERENCES vehicles(vin),
  driver_id UUID REFERENCES drivers(id),
  started_at TIMESTAMPTZ,
  ended_at TIMESTAMPTZ,
  distance_km NUMERIC,
  energy_used_kwh NUMERIC
);

CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vehicle_vin TEXT REFERENCES vehicles(vin),
  severity TEXT,
  message TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  acknowledged BOOLEAN DEFAULT false
);

CREATE TABLE maintenance_records (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vehicle_vin TEXT REFERENCES vehicles(vin),
  component TEXT,
  predicted_failure_at DATE,
  confidence NUMERIC,
  status TEXT
);

CREATE TABLE risk_assessments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  vehicle_vin TEXT REFERENCES vehicles(vin),
  score NUMERIC,
  factors JSONB,
  assessed_at TIMESTAMPTZ DEFAULT now()
);
