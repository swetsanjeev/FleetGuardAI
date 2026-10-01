import { describe, it, expect } from "vitest";
import { isValidVin } from "../../utils/validators";

describe("isValidVin", () => {
  it("accepts a 17-char VIN", () => {
    expect(isValidVin("1FAGV37P8VG000001".slice(0, 17).padEnd(17, "0"))).toBe(true);
  });
});
