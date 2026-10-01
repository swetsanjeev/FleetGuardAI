export async function writeTelemetryPartition(date: string, rows: unknown[]): Promise<Buffer> {
  // TODO: use parquetjs to serialize rows to a partition file
  console.log(`[datalake] writing ${rows.length} rows for ${date}`);
  return Buffer.from([]);
}
