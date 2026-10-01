import React from "react";
import { DtcCode } from "../types/telemetry";

export function DtcList({ codes }: { codes: DtcCode[] }) {
  return (
    <ul className="dtc-list">
      {codes.map((c) => <li key={c.code}>{c.code} - {c.description} ({c.severity})</li>)}
    </ul>
  );
}
