import { describe, it, expect } from "vitest";
import { formatters } from "../../utils/formatters";

describe("formatters.energy", () => {
  it("formats kWh", () => {
    expect(formatters.energy(41.2)).toContain("kWh");
  });
});
