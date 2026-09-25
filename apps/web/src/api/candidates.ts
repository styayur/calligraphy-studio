import { searchGlyphs } from './client'
import { fontGlyphs } from './fonts'
import type { Glyph } from '../types'
export type CandidateSource = 'fonts' | 'original' | 'all'
export interface CandidatePage {
  items: Glyph[]
  hasMore: boolean
  warning: string
}
const pages = new Map<string, { time: number; value: Promise<CandidatePage> }>()
/** Short TTL lets newly imported originals become discoverable. */
export function candidatePage(
  character: string,
  source: CandidateSource = 'all',
  style = '',
  offset = 0,
  limit = 12,
): Promise<CandidatePage> {
  const key = JSON.stringify([character, source, style, offset, limit]),
    hit = pages.get(key)
  if (hit && Date.now() - hit.time < 60_000) return hit.value
  const value = (async () => {
    const [fonts, library] = await Promise.allSettled([
      source !== 'original' && offset === 0
        ? fontGlyphs(character, style)
        : Promise.resolve([]),
      source !== 'fonts'
        ? searchGlyphs({ character, style, offset, limit })
        : Promise.resolve({ items: [] as Glyph[], total: 0 }),
    ])
    if (source === 'fonts' && fonts.status === 'rejected') throw fonts.reason
    if (source === 'original' && library.status === 'rejected') throw library.reason
    const items = [
      ...(fonts.status === 'fulfilled' ? fonts.value : []),
      ...(library.status === 'fulfilled'
        ? library.value.items.filter(
            (g) => g.provenance.type === 'original' && g.source.dataset !== 'Demo',
          )
        : []),
    ]
    const warning = [
      fonts.status === 'rejected' ? '内置字体加载失败' : '',
      library.status === 'rejected' ? '原帖字库未连接' : '',
    ]
      .filter(Boolean)
      .join('；')
    return {
      items,
      hasMore: library.status === 'fulfilled' && offset + limit < library.value.total,
      warning,
    }
  })().catch((error) => {
    pages.delete(key)
    throw error
  })
  pages.set(key, { time: Date.now(), value })
  if (pages.size > 4096) pages.delete(pages.keys().next().value!)
  return value
}
/** Skip pages containing only excluded records rather than reporting false missing glyphs. */
export async function initialCandidates(
  character: string,
  source: CandidateSource,
  style: string,
  limit: number,
  signal?: AbortSignal,
) {
  let offset = 0
  while (true) {
    signal?.throwIfAborted()
    const page = await candidatePage(character, source, style, offset, limit)
    if (page.items.length || !page.hasMore) return page
    offset += limit
  }
}
export async function resolveCharacters<T>(
  characters: string[],
  resolve: (character: string) => Promise<T>,
  progress: (done: number, total: number) => void,
  signal?: AbortSignal,
): Promise<Map<string, T>> {
  const unique = [...new Set(characters)],
    result = new Map<string, T>()
  let cursor = 0,
    done = 0,
    stopped = false
  const workers = await Promise.allSettled(
    Array.from({ length: Math.min(4, unique.length) }, async () => {
      try {
        while (cursor < unique.length && !stopped) {
          signal?.throwIfAborted()
          const character = unique[cursor++],
            value = await resolve(character)
          signal?.throwIfAborted()
          result.set(character, value)
          progress(++done, unique.length)
          await new Promise((r) => setTimeout(r, 0))
        }
      } catch (error) {
        stopped = true
        throw error
      }
    }),
  )
  const error = workers.find((w) => w.status === 'rejected')
  if (error?.status === 'rejected') throw error.reason
  return result
}
