const BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function request(method: string, path: string, body?: unknown) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json();
}

export const apiClient = {
  get: (p: string) => request("GET", p),
  post: (p: string, b: unknown) => request("POST", p, b),
  put: (p: string, b: unknown) => request("PUT", p, b),
  delete: (p: string) => request("DELETE", p),
};
