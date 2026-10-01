import { MongoClient as Driver } from "mongodb";

export class MongoService {
  private client = new Driver(process.env.MONGO_URL ?? "mongodb://localhost:27017");
  async telemetryCollection() {
    await this.client.connect();
    return this.client.db("fleetguard").collection("telemetry_events");
  }
}
