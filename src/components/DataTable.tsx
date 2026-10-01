import React from "react";

export function DataTable<T extends Record<string, unknown>>({ rows, columns }: { rows: T[]; columns: (keyof T)[] }) {
  return (
    <table>
      <thead><tr>{columns.map((c) => <th key={String(c)}>{String(c)}</th>)}</tr></thead>
      <tbody>{rows.map((r, i) => <tr key={i}>{columns.map((c) => <td key={String(c)}>{String(r[c] ?? "")}</td>)}</tr>)}</tbody>
    </table>
  );
}
