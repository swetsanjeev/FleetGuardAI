import { describe, it, expect } from "vitest";
import { aggregateRisk } from "../../utils/riskUtils";

describe("aggregateRisk", () => {
  it("caps at 100", () => {
    expect(aggregateRisk(["speeding", "speeding", "speeding", "speeding", "speeding", "speeding", "speeding", "speeding"])).toBeLessThanOrEqual(100);
  });
});
