INSERT INTO organizations (name, plan) VALUES ('FleetGuard Logistics', 'enterprise');
INSERT INTO fleets (name, region) VALUES ('Metro Delivery', 'us-east');
INSERT INTO vehicles (vin, model, year, battery_soc, status) VALUES
  ('1FAGV37P8VG000001', 'Transit E-450', 2024, 64, 'active'),
  ('1FAGV37P8VG000002', 'eSprinter', 2023, 18, 'charging');
INSERT INTO drivers (full_name, license_no, safety_score) VALUES
  ('Amara Osei', 'CA-D8841203', 94),
  ('Liam Chen', 'CA-D7819921', 88);
