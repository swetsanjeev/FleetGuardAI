export const env = {
  NODE_ENV: process.env.NODE_ENV ?? "development",
  API_PORT: Number(process.env.PORT ?? 8000),
};
