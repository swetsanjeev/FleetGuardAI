export const databaseConfig = {
  host: process.env.POSTGRES_HOST ?? "localhost",
  port: Number(process.env.POSTGRES_PORT ?? 5432),
  database: process.env.POSTGRES_DB ?? "fleetguard",
  user: process.env.POSTGRES_USER ?? "fleetguard",
  poolSize: 10,
};
