import { STATIC_MODE } from '../config/runtime'
import type {
  BatchComposeRequest,
  BatchComposeResponse,
  Glyph,
  MetadataResponse,
  ProjectDocument,
  ProjectListItem,
  ProjectRecord,
  SimilarityResponse,
} from '../types'

const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? ''
export const isStaticMode = STATIC_MODE

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })
  if (!response.ok) {
    let message = response.statusText
    try {
      const payload = (await response.json()) as { detail?: string }
      message = payload.detail ?? message
    } catch {
      // Keep the HTTP status text when the body is not JSON.
    }
    throw new ApiError(message, response.status)
  }
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

export interface GlyphSearchParams {
  q?: string
  character?: string
  calligrapher?: string
  style?: string
  dynasty?: string
  work?: string
  dataset?: string
  limit?: number
  offset?: number
}

export interface GlyphListResponse {
  items: Glyph[]
  total: number
  limit: number
  offset: number
}

export async function searchGlyphs(params: GlyphSearchParams): Promise<GlyphListResponse> {
  if (STATIC_MODE) return (await import('./static')).staticSearch(params)
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') query.set(key, String(value))
  })
  return request<GlyphListResponse>(`/api/search?${query.toString()}`)
}

export async function getMetadata(): Promise<MetadataResponse> {
  if (STATIC_MODE) return (await import('./static')).loadStaticMetadata()
  return request<MetadataResponse>('/api/meta')
}

export async function listProjects(): Promise<ProjectListItem[]> {
  if (STATIC_MODE) return []
  return request<ProjectListItem[]>('/api/projects')
}

export async function createProject(name: string, document: ProjectDocument): Promise<ProjectRecord> {
  if (STATIC_MODE) throw new ApiError('GitHub Pages 静态版不支持服务端保存，请使用“保存 JSON”。', 501)
  return request<ProjectRecord>('/api/projects', {
    method: 'POST',
    body: JSON.stringify({ name, document }),
  })
}

export async function updateProject(
  id: string,
  name: string,
  document: ProjectDocument,
): Promise<ProjectRecord> {
  if (STATIC_MODE) throw new ApiError('GitHub Pages 静态版不支持服务端保存，请使用“保存 JSON”。', 501)
  return request<ProjectRecord>(`/api/projects/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ name, document }),
  })
}
export async function composeBatch(payload: BatchComposeRequest): Promise<BatchComposeResponse> {
  if (STATIC_MODE) return (await import('./static')).staticCompose(payload)
  return request<BatchComposeResponse>('/api/compose/batch', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getSimilarGlyphs(
  glyphId: string,
  options: { limit?: number; sameStyle?: boolean; sameDataset?: boolean } = {},
): Promise<SimilarityResponse> {
  if (STATIC_MODE) return (await import('./static')).staticSimilar(glyphId, options.limit ?? 12)
  const query = new URLSearchParams({
    limit: String(options.limit ?? 12),
    same_style: String(options.sameStyle ?? true),
    same_dataset: String(options.sameDataset ?? false),
  })
  return request<SimilarityResponse>(`/api/similarity/${glyphId}?${query.toString()}`)
}
