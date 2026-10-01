import { describe, it, expect } from "vitest";
import { vehicleService } from "../../src/services/vehicleService";

describe("vehicleService", () => {
  it("lists vehicles", async () => {
    const v = await vehicleService.list();
    expect(Array.isArray(v)).toBe(true);
  });
});
