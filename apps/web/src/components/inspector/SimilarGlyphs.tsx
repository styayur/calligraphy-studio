import { useEffect, useState } from 'react'
import { fontGlyphs } from '../../api/fonts'
import { searchGlyphs } from '../../api/client'
import { useEditorStore } from '../../stores/editor'
import type { GlyphInstance, Glyph } from '../../types'

export function SimilarGlyphs({ glyph }: { glyph: GlyphInstance }) {
  const [items, setItems] = useState<Glyph[]>([])
  const [status, setStatus] = useState('')
  const replace = useEditorStore((s) => s.replaceGlyph)
  useEffect(() => {
    let active = true
    setItems([])
    setStatus('正在查找同字字形…')
    Promise.allSettled([
      fontGlyphs(glyph.character),
      searchGlyphs({ character: glyph.character, limit: 60 }),
    ]).then(([fonts, library]) => {
      if (!active) return
      const results = [
        ...(fonts.status === 'fulfilled' ? fonts.value : []),
        ...(library.status === 'fulfilled'
          ? library.value.items.filter(
              (g) => g.provenance.type !== 'font' && g.source.dataset !== 'Demo',
            )
          : []),
      ]
      setItems(results)
      setStatus(
        results.length
          ? library.status === 'rejected'
            ? '原帖字库未连接，显示内置字体。'
            : ''
          : '暂无其他字形，请检查字库连接。',
      )
    })
    return () => {
      active = false
    }
  }, [glyph.character])
  return (
    <section className="variants-section">
      <div className="section-title">
        <h3>换个字形</h3>
        <span>保留位置与大小</span>
      </div>
      {status && (
        <p className="field-hint" role="status">
          {status}
        </p>
      )}
      <div className="variant-grid">
        {items.map((item) => (
          <button
            key={item.id}
            onClick={() => replace(glyph.id, item)}
            aria-label={`替换为${item.source.work || item.source.style || item.character}`}
            aria-pressed={item.id === glyph.glyph_id}
            title={`${item.source.work || item.source.dataset} · ${item.source.license || '授权未标注'}`}
          >
            <img src={item.asset.url} alt={item.character} />
            <span>
              {item.provenance.type === 'original' ? '原帖' : item.source.style || '结构替补'}
            </span>
          </button>
        ))}
      </div>
    </section>
  )
}
