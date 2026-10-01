import { RedisService } from "./RedisClient";

export class RateLimiter {
  constructor(private redis: RedisService) {}
  async allow(key: string): Promise<boolean> {
    // TODO: sliding window counter
    return true;
  }
}
