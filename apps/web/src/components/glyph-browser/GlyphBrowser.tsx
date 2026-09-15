import { Search, SlidersHorizontal } from 'lucide-react'
import { FormEvent, useEffect, useMemo, useState } from 'react'
import { getMetadata, searchGlyphs } from '../../api/client'
import { useEditorStore } from '../../stores/editor'
import type { Glyph, MetadataResponse } from '../../types'
import { Button, cn } from '../ui'

export const GLYPH_DRAG_TYPE = 'application/x-calligraphy-glyph'

function ProvenanceBadge({ glyph }: { glyph: Glyph }) {
  const labels = glyph.source.dataset === 'Demo'
    ? { original: '演示字形', font: '演示字形', fallback: '演示字形', generated: '演示字形' }
    : { original: '真实字形', font: '字体字形', fallback: '结构替补', generated: 'AI 生成' }
  return (
    <span
      className={cn(
        'rounded-full px-2 py-0.5 text-[10px] font-semibold',
        glyph.provenance.type === 'original' && 'bg-emerald-900/10 text-emerald-900',
        glyph.provenance.type === 'font' && 'bg-sky-900/10 text-sky-900',
        glyph.provenance.type === 'fallback' && 'bg-amber-900/10 text-amber-900',
        glyph.provenance.type === 'generated' && 'bg-cinnabar/10 text-cinnabar',
      )}
    >
      {labels[glyph.provenance.type]}
    </span>
  )
}

function GlyphCard({ glyph }: { glyph: Glyph }) {
  const addGlyph = useEditorStore((state) => state.addGlyph)
  return (
    <button
      type="button"
      draggable
      onClick={() => addGlyph(glyph)}
      onDragStart={(event) => {
        event.dataTransfer.effectAllowed = 'copy'
        event.dataTransfer.setData(GLYPH_DRAG_TYPE, JSON.stringify(glyph))
      }}
      className="group min-w-0 rounded-lg border border-black/10 bg-white/75 p-2 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-cinnabar/35 hover:shadow-md"
      title="点击加入画布，或拖到画布指定位置"
    >
      <div className="flex aspect-square items-center justify-center overflow-hidden rounded-md bg-[#f6f1e7]">
        <img
          src={glyph.asset.url}
          alt={glyph.character}
          draggable={false}
          className="glyph-thumbnail h-full w-full object-contain p-3 mix-blend-multiply"
        />
      </div>
      <div className="mt-2 flex items-center justify-between gap-2">
        <span className="font-display text-3xl leading-none">{glyph.character}</span>
        <ProvenanceBadge glyph={glyph} />
      </div>
      <p className="mt-1 truncate text-xs font-medium text-ink/75">
        {[glyph.source.calligrapher, glyph.source.style].filter(Boolean).join(' · ') || '未标注'}
      </p>
      <p className="truncate text-[10px] text-ink/45">
        {[glyph.source.dynasty, glyph.source.work, glyph.source.dataset].filter(Boolean).join(' / ')}
      </p>
    </button>
  )
}

export function GlyphBrowser() {
  const [query, setQuery] = useState('山')
  const [calligrapher, setCalligrapher] = useState('')
  const [style, setStyle] = useState('')
  const [dynasty, setDynasty] = useState('')
  const [dataset, setDataset] = useState('')
  const [results, setResults] = useState<Glyph[]>([])
  const [meta, setMeta] = useState<MetadataResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const runSearch = async (term = query) => {
    setLoading(true)
    setError(null)
    try {
      const response = await searchGlyphs({ q: term, calligrapher, style, dynasty, dataset, limit: 60 })
      setResults(response.items)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : '搜索失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    getMetadata()
      .then(setMeta)
      .catch(() => undefined)
    void runSearch('山')
    // Initial request intentionally ignores later filter dependencies.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const activeFilterCount = useMemo(
    () => [calligrapher, style, dynasty, dataset].filter(Boolean).length,
    [calligrapher, style, dynasty, dataset],
  )

  const submit = (event: FormEvent) => {
    event.preventDefault()
    void runSearch()
  }

  return (
    <aside className="flex h-full min-h-0 w-[300px] shrink-0 flex-col border-r border-black/10 bg-[#ece7dc]/90">
      <div className="border-b border-black/10 p-4">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-cinnabar">Glyph Store</p>
            <h2 className="font-display text-2xl">集字簿</h2>
          </div>
          <span className="rounded-full bg-black/5 px-2 py-1 text-[10px] text-ink/55">
            {results.length} 项
          </span>
        </div>
        <form onSubmit={submit} className="flex gap-2">
          <div className="relative min-w-0 flex-1">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-ink/40" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="输入汉字、书家或作品"
              className="h-9 w-full rounded-md border border-black/10 bg-white/80 pl-8 pr-2 text-sm outline-none ring-cinnabar/20 transition focus:ring-2"
            />
          </div>
          <Button size="icon" aria-label="搜索">
            <Search className="h-4 w-4" />
          </Button>
        </form>
      </div>

      <div className="border-b border-black/10 px-4 py-3">
        <div className="mb-2 flex items-center gap-2 text-xs font-medium text-ink/60">
          <SlidersHorizontal className="h-3.5 w-3.5" />
          筛选
          {activeFilterCount > 0 && (
            <span className="rounded-full bg-cinnabar px-1.5 text-[10px] text-white">
              {activeFilterCount}
            </span>
          )}
        </div>
        <div className="grid grid-cols-1 gap-2">
          <select value={calligrapher} onChange={(event) => setCalligrapher(event.target.value)} className="h-8 rounded-md border border-black/10 bg-white/70 px-2 text-xs">
            <option value="">全部书家</option>
            {meta?.calligraphers.map((item) => <option key={item.id}>{item.name}</option>)}
          </select>
          <select value={dataset} onChange={(event) => setDataset(event.target.value)} className="h-8 min-w-0 rounded-md border border-black/10 bg-white/70 px-2 text-xs">
            <option value="">全部数据源</option>
            {meta?.datasets.map((item) => <option key={item}>{item}</option>)}
          </select>
          <div className="grid grid-cols-2 gap-2">
            <select value={style} onChange={(event) => setStyle(event.target.value)} className="h-8 min-w-0 rounded-md border border-black/10 bg-white/70 px-2 text-xs">
              <option value="">全部书体</option>
              {meta?.styles.map((item) => <option key={item.id}>{item.name}</option>)}
            </select>
            <select value={dynasty} onChange={(event) => setDynasty(event.target.value)} className="h-8 min-w-0 rounded-md border border-black/10 bg-white/70 px-2 text-xs">
              <option value="">全部朝代</option>
              {meta?.dynasties.map((item) => <option key={item.id}>{item.name}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="panel-scroll min-h-0 flex-1 overflow-y-auto p-3">
        {loading && <div className="py-10 text-center text-sm text-ink/45">检索字形…</div>}
        {error && (
          <div className="rounded-lg border border-cinnabar/20 bg-cinnabar/5 p-3 text-xs text-cinnabar">
            <p className="font-semibold">无法连接 Glyph API</p>
            <p className="mt-1 text-cinnabar/75">{error}</p>
          </div>
        )}
        {!loading && !error && results.length === 0 && (
          <div className="py-10 text-center text-sm text-ink/45">暂无匹配字形</div>
        )}
        <div className="grid grid-cols-2 gap-3">
          {results.map((glyph) => <GlyphCard key={glyph.id} glyph={glyph} />)}
        </div>
      </div>
    </aside>
  )
}