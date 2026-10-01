import { describe, it, expect } from "vitest";
import { haversineKm } from "../../utils/telemetryUtils";

describe("haversineKm", () => {
  it("returns zero for same point", () => {
    expect(haversineKm({ lat: 0, lon: 0 }, { lat: 0, lon: 0 })).toBe(0);
  });
});
