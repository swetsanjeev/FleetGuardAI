import { PgVectorClient } from "../vector/PgVectorClient";
import { embedText } from "../vector/Embeddings";
import { PROMPTS } from "./promptTemplates";

export class CopilotService {
  constructor(private vector: PgVectorClient) {}
  async ask(question: string): Promise<string> {
    const embedding = await embedText(question);
    const docs = await this.vector.search(embedding);
    // TODO: call LLM with PROMPTS.SYSTEM + retrieved docs
    return `Answer draft using ${docs.length} context chunks.`;
  }
}
