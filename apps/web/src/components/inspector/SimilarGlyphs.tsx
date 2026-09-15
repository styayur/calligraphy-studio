import { ScanSearch } from 'lucide-react'
import { useEffect, useState } from 'react'
import { getSimilarGlyphs } from '../../api/client'
import { useEditorStore } from '../../stores/editor'
import type { SimilarGlyphItem } from '../../types'

export function SimilarGlyphs({ glyphId }: { glyphId: string }) {
  const [items, setItems] = useState<SimilarGlyphItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const addGlyph = useEditorStore((state) => state.addGlyph)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    getSimilarGlyphs(glyphId, { limit: 8, sameStyle: true })
      .then((response) => {
        if (active) setItems(response.items)
      })
      .catch((caught) => {
        if (active) setError(caught instanceof Error ? caught.message : '相似检索失败')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [glyphId])

  return (
    <section className="border-b border-black/10 p-4">
      <h3 className="mb-1 flex items-center gap-2 text-xs font-semibold text-ink/70">
        <ScanSearch className="h-3.5 w-3.5" /> 相似字形
      </h3>
      <p className="mb-3 text-[10px] text-ink/40">visual-geometry-256-v1 · 同书体推荐</p>
      {loading && <p className="text-xs text-ink/40">计算视觉向量…</p>}
      {error && <p className="text-xs text-cinnabar">{error}</p>}
      {!loading && !error && items.length === 0 && <p className="text-xs text-ink/40">暂无相似结果，请先建立 embedding。</p>}
      <div className="grid grid-cols-4 gap-2">
        {items.map((item) => (
          <button
            key={item.glyph.id}
            type="button"
            onClick={() => addGlyph(item.glyph)}
            className="group rounded-lg border border-black/10 bg-white/65 p-1.5 transition hover:border-cinnabar/35 hover:bg-white"
            title={`${item.glyph.character} · 相似度 ${Math.round(item.score * 100)}%`}
          >
            <div className="aspect-square overflow-hidden rounded bg-[#f6f1e7] p-1">
              <img src={item.glyph.asset.url} alt={item.glyph.character} className="h-full w-full object-contain mix-blend-multiply" />
            </div>
            <span className="mt-1 block text-center text-[10px] text-ink/45">{Math.round(item.score * 100)}%</span>
          </button>
        ))}
      </div>
    </section>
  )
}
