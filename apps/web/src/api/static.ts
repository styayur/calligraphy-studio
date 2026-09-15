import { staticAssetUrl } from '../config/runtime'
import type {
  BatchComposeRequest,
  BatchComposeResponse,
  BatchPlacement,
  Glyph,
  GlyphInstance,
  MetadataResponse,
  SimilarGlyphItem,
  SimilarityResponse,
} from '../types'
import type { GlyphListResponse, GlyphSearchParams } from './client'

interface StaticSimilarityEntry {
  id: string
  score: number
}

type StaticSimilarity = Record<string, StaticSimilarityEntry[]>

let glyphPromise: Promise<Glyph[]> | null = null
let similarityPromise: Promise<StaticSimilarity> | null = null

export async function loadStaticGlyphs(): Promise<Glyph[]> {
  if (!glyphPromise) {
    glyphPromise = fetch(`${import.meta.env.BASE_URL}demo/glyphs.json`)
      .then((response) => {
        if (!response.ok) throw new Error('无法加载静态 Glyph 数据')
        return response.json() as Promise<Glyph[]>
      })
      .then((glyphs) =>
        glyphs.map((glyph) => ({
          ...glyph,
          asset: { ...glyph.asset, url: staticAssetUrl(glyph.asset.url) },
        })),
      )
  }
  return glyphPromise
}

export async function loadStaticSimilarity(): Promise<StaticSimilarity> {
  if (!similarityPromise) {
    similarityPromise = fetch(`${import.meta.env.BASE_URL}demo/similarity.json`)
      .then((response) => {
        if (!response.ok) throw new Error('无法加载静态相似度数据')
        return response.json() as Promise<StaticSimilarity>
      })
  }
  return similarityPromise
}

export async function loadStaticMetadata(): Promise<MetadataResponse> {
  const response = await fetch(`${import.meta.env.BASE_URL}demo/meta.json`)
  if (!response.ok) throw new Error('无法加载静态元数据')
  return response.json() as Promise<MetadataResponse>
}

export async function staticSearch(params: GlyphSearchParams): Promise<GlyphListResponse> {
  const glyphs = await loadStaticGlyphs()
  const query = params.q?.trim()
  const items = glyphs.filter((glyph) => {
    if (params.character && glyph.character !== params.character) return false
    if (params.calligrapher && glyph.source.calligrapher !== params.calligrapher) return false
    if (params.style && glyph.source.style !== params.style) return false
    if (params.dynasty && glyph.source.dynasty !== params.dynasty) return false
    if (params.work && glyph.source.work !== params.work) return false
    if (params.dataset && glyph.source.dataset !== params.dataset) return false
    if (query) {
      if (query.length === 1 && glyph.character !== query) return false
      if (query.length > 1) {
        const haystack = [
          glyph.character,
          glyph.source.calligrapher,
          glyph.source.style,
          glyph.source.dynasty,
          glyph.source.work,
          glyph.source.dataset,
        ].filter(Boolean).join(' ')
        if (!haystack.includes(query)) return false
      }
    }
    return true
  })
  const offset = params.offset ?? 0
  const limit = params.limit ?? 60
  return {
    items: items.slice(offset, offset + limit),
    total: items.length,
    limit,
    offset,
  }
}

export async function staticSimilar(glyphId: string, limit: number): Promise<SimilarityResponse> {
  const [glyphs, similarity] = await Promise.all([loadStaticGlyphs(), loadStaticSimilarity()])
  const byId = new Map(glyphs.map((glyph) => [glyph.id, glyph]))
  const items: SimilarGlyphItem[] = (similarity[glyphId] ?? [])
    .slice(0, limit)
    .map((entry) => ({ glyph: byId.get(entry.id)!, score: entry.score }))
    .filter((entry) => entry.glyph)
  return { target_id: glyphId, model_name: 'visual-geometry-256-v1', items }
}

function staticLines(text: string): string[][] {
  const normalized = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
  const lines = normalized
    .split('\n')
    .map((line) => [...line].filter((character) => !/\s/.test(character)))
    .filter((line) => line.length)
  return lines.length ? lines : [[...normalized].filter((character) => !/\s/.test(character))]
}

function staticPositions(request: BatchComposeRequest, lines: string[][]) {
  const positions: Array<{ character: string; line: number; column: number; x: number; y: number }> = []
  const stepX = request.cell_width + request.gap_x
  const stepY = request.cell_height + request.gap_y
  if (request.layout === 'grid') {
    const flattened = lines.flat()
    flattened.forEach((character, index) => {
      const row = Math.floor(index / request.columns)
      const column = index % request.columns
      positions.push({ character, line: row, column, x: request.start_x + column * stepX + request.cell_width / 2, y: request.start_y + row * stepY + request.cell_height / 2 })
    })
  } else if (request.layout === 'horizontal-ltr') {
    lines.forEach((line, lineIndex) => line.forEach((character, column) => positions.push({ character, line: lineIndex, column, x: request.start_x + column * stepX + request.cell_width / 2, y: request.start_y + lineIndex * stepY + request.cell_height / 2 })))
  } else {
    lines.forEach((line, lineIndex) => line.forEach((character, row) => positions.push({ character, line: lineIndex, column: row, x: request.start_x - lineIndex * stepX + request.cell_width / 2, y: request.start_y + row * stepY + request.cell_height / 2 })))
  }
  return positions
}

export async function staticCompose(request: BatchComposeRequest): Promise<BatchComposeResponse> {
  const glyphs = await loadStaticGlyphs()
  const lines = staticLines(request.text)
  const missing: string[] = []
  const placements: BatchPlacement[] = []
  const cache = new Map<string, Glyph | null>()
  for (const position of staticPositions(request, lines)) {
    if (!cache.has(position.character)) {
      const glyph = glyphs.find((candidate) => {
        if (candidate.character !== position.character) return false
        if (request.calligrapher && candidate.source.calligrapher !== request.calligrapher) return false
        if (request.style && candidate.source.style !== request.style) return false
        if (request.dataset && candidate.source.dataset !== request.dataset) return false
        return true
      }) ?? null
      cache.set(position.character, glyph)
    }
    const glyph = cache.get(position.character)
    if (!glyph) {
      if (!missing.includes(position.character)) missing.push(position.character)
      continue
    }
    const scale = Math.min(request.cell_width / glyph.asset.width, request.cell_height / glyph.asset.height) * 0.86
    const instance: GlyphInstance = {
      ...structuredClone(glyph),
      id: crypto.randomUUID(),
      glyph_id: glyph.id,
      transform: { ...glyph.transform, x: position.x, y: position.y, scaleX: scale, scaleY: scale },
    }
    placements.push({ glyph: instance, line: position.line, column: position.column })
  }
  return {
    placements,
    missing,
    total_characters: lines.reduce((count, line) => count + line.length, 0),
    resolved_characters: placements.length,
  }
}
