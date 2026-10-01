import { useEffect, useState } from "react";

export function useRiskScore(vin: string) {
  const [score, setScore] = useState<number>(0);
  useEffect(() => { setScore(0); }, [vin]);
  return { score };
}
