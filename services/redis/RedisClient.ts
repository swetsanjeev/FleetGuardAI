import Redis from "ioredis";
import { redisConfig } from "../../config/redis.config";

export class RedisService {
  private client = new Redis(redisConfig.url);
  get(key: string) { return this.client.get(redisConfig.keyPrefix + key); }
  set(key: string, value: string, ttl = redisConfig.vehicleStateTtlSec) {
    return this.client.set(redisConfig.keyPrefix + key, value, "EX", ttl);
  }
}
