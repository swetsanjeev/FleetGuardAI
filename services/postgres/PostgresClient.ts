import { Pool } from "pg";
import { databaseConfig } from "../../config/database.config";

export class PostgresClient {
  private pool = new Pool(databaseConfig as any);
  async query<T>(sql: string, params?: unknown[]): Promise<T[]> {
    const res = await this.pool.query(sql, params as any[]);
    return res.rows as T[];
  }
}
