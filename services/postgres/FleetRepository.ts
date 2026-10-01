import { PostgresClient } from "./PostgresClient";

export class FleetRepository {
  constructor(private db: PostgresClient) {}
  async findAll() { return this.db.query("SELECT * FROM fleets"); }
}
