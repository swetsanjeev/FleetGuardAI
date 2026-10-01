export async function embedText(text: string): Promise<number[]> {
  // TODO: call embedding provider (e.g. 1536-dim)
  return Array.from({ length: 8 }, () => Math.random());
}
