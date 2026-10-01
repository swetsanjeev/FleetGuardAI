export interface ApiEnvelope<T> { data: T; meta?: Record<string, unknown>; error?: string }
export interface PageInfo { page: number; pageSize: number; total: number }
