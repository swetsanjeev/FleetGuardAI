import { MongoService } from "./MongoClient";

export class TelemetryRepository {
  constructor(private mongo: MongoService) {}
  async latestForVin(vin: string) {
    const col = await this.mongo.telemetryCollection();
    return col.find({ vin }).sort({ timestamp: -1 }).limit(50).toArray();
  }
}
