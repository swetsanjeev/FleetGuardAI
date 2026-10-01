import { PostgresClient } from "../postgres/PostgresClient";

export class PgVectorClient {
  constructor(private db: PostgresClient) {}
  async upsertChunk(source: string, content: string, embedding: number[]) {
    return this.db.query(
      "INSERT INTO knowledge_chunks (source, content, embedding) VALUES ($1, $2, $3)",
      [source, content, `[${embedding.join(",")}]`]
    );
  }
  async search(embedding: number[], limit = 5) {
    return this.db.query(
      "SELECT source, content FROM knowledge_chunks ORDER BY embedding <-> $1 LIMIT $2",
      [`[${embedding.join(",")}]`, limit]
    );
  }
}
