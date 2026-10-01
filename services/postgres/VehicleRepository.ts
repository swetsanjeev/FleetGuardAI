import { PostgresClient } from "./PostgresClient";

export class VehicleRepository {
  constructor(private db: PostgresClient) {}
  async findAll() { return this.db.query("SELECT * FROM vehicles"); }
  async findByVin(vin: string) { return this.db.query("SELECT * FROM vehicles WHERE vin = $1", [vin]); }
}
