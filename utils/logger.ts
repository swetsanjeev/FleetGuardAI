type Level = "debug" | "info" | "warn" | "error";
export function log(level: Level, msg: string, meta?: Record<string, unknown>) {
  console.log(JSON.stringify({ level, msg, meta, ts: new Date().toISOString() }));
}
