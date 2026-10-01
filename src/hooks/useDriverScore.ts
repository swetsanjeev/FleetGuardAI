import { useEffect, useState } from "react";
import { Driver } from "../types/driver";

export function useDriverScore() {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  useEffect(() => { setDrivers([]); }, []);
  return { drivers };
}
