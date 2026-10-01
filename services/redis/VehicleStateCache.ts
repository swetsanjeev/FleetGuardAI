import { RedisService } from "./RedisClient";

export class VehicleStateCache {
  constructor(private redis: RedisService) {}
  cacheState(vin: string, state: unknown) { return this.redis.set(`state:${vin}`, JSON.stringify(state)); }
  async getState(vin: string) {
    const raw = await this.redis.get(`state:${vin}`);
    return raw ? JSON.parse(raw) : null;
  }
}
