import { Copy, Trash2, X } from 'lucide-react'
import { useEditorStore } from '../../stores/editor'
import { SimilarGlyphs } from './SimilarGlyphs'
import { Button } from '../ui'
import type { GlyphTransform } from '../../types'
import { semanticIdentity } from '../../lib/identity'

export function Inspector() {
  const glyph = useEditorStore((s) => s.project.glyphs.find((g) => g.id === s.selectedId))
  const {
    setGlyphTransform,
    setGlyphAppearance,
    removeGlyph,
    duplicateGlyph,
    selectGlyph,
    beginHistory,
    reorderGlyph,
  } = useEditorStore()
  if (!glyph) return null
  const patch = (value: Partial<GlyphTransform>) =>
    setGlyphTransform(glyph.id, value, { recordHistory: false })
  return (
    <aside className="inspector panel-scroll" aria-label="字形调整">
      <div className="inspector-heading">
        <div>
          <span className="selected-character">{glyph.character}</span>
          <span>{glyph.source.style || '字形调整'}</span>
        </div>
        <Button
          size="icon"
          variant="ghost"
          aria-label="关闭字形调整"
          onClick={() => selectGlyph(null)}
        >
          <X size={16} />
        </Button>
      </div>
      <SimilarGlyphs key={glyph.id} glyph={glyph} />
      <section className="adjust-section">
        <div className="section-title">
          <h3>调整单字</h3>
          <div className="flex">
            <Button
              variant="ghost"
              size="icon"
              title="复制单字"
              aria-label="复制单字"
              onClick={() => duplicateGlyph(glyph.id)}
            >
              <Copy size={15} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              title="删除单字"
              aria-label="删除单字"
              onClick={() => removeGlyph(glyph.id)}
            >
              <Trash2 size={15} />
            </Button>
          </div>
        </div>
        <label className="slider-field">
          <span>
            大小 <output>{Math.round(glyph.asset.width * glyph.transform.scaleX)} px</output>
          </span>
          <input
            aria-label="单字大小"
            type="range"
            min={20}
            max={600}
            value={Math.abs(glyph.asset.width * glyph.transform.scaleX)}
            onPointerDown={beginHistory}
            onKeyDown={(e) => {
              if (!e.repeat) beginHistory()
            }}
            onChange={(e) => {
              const ratio =
                Number(e.target.value) / Math.abs(glyph.asset.width * glyph.transform.scaleX || 1)
              patch({
                scaleX: glyph.transform.scaleX * ratio,
                scaleY: glyph.transform.scaleY * ratio,
              })
            }}
          />
        </label>
        <label className="slider-field">
          <span>
            旋转 <output>{Math.round(glyph.transform.rotation)}°</output>
          </span>
          <input
            aria-label="单字旋转"
            type="range"
            min={-180}
            max={180}
            value={glyph.transform.rotation}
            onPointerDown={beginHistory}
            onKeyDown={(e) => {
              if (!e.repeat) beginHistory()
            }}
            onChange={(e) => patch({ rotation: Number(e.target.value) })}
          />
        </label>
        <label className="slider-field">
          <span>
            墨色 <output>{Math.round(glyph.appearance.opacity * 100)}%</output>
          </span>
          <input
            aria-label="墨色浓度"
            type="range"
            min={0.05}
            max={1}
            step={0.01}
            value={glyph.appearance.opacity}
            onPointerDown={beginHistory}
            onKeyDown={(e) => {
              if (!e.repeat) beginHistory()
            }}
            onChange={(e) =>
              setGlyphAppearance(
                glyph.id,
                { opacity: Number(e.target.value) },
                { recordHistory: false },
              )
            }
          />
        </label>
        <details className="advanced">
          <summary>精细调整</summary>
          <div className="field-grid">
            {(
              [
                ['x', '水平位置'],
                ['y', '垂直位置'],
                ['scaleX', '水平缩放'],
                ['scaleY', '垂直缩放'],
                ['skewX', '水平倾斜'],
                ['skewY', '垂直倾斜'],
              ] as const
            ).map(([key, label]) => (
              <label key={key}>
                {label}
                <input
                  type="number"
                  step={key.startsWith('skew') || key.startsWith('scale') ? 0.05 : 1}
                  value={Number(glyph.transform[key].toFixed(2))}
                  onFocus={beginHistory}
                  onChange={(e) => patch({ [key]: Number(e.target.value) })}
                />
              </label>
            ))}
          </div>
          <label className="check-field">
            混合
            <select
              aria-label="混合模式"
              value={glyph.appearance.blendMode}
              onChange={(e) => setGlyphAppearance(glyph.id, { blendMode: e.target.value })}
            >
              <option value="source-over">正常</option>
              <option value="multiply">正片叠底</option>
              <option value="screen">滤色</option>
              <option value="overlay">叠加</option>
              <option value="darken">变暗</option>
              <option value="lighten">变亮</option>
            </select>
          </label>
          <div className="flex gap-2 mt-3">
            <Button variant="secondary" size="sm" onClick={() => reorderGlyph(glyph.id, 'forward')}>
              上移一层
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => reorderGlyph(glyph.id, 'backward')}
            >
              下移一层
            </Button>
          </div>
        </details>
      </section>
      <section className="source-section">
        <h3>字形来源</h3>
        <p>{glyph.source.work || glyph.source.dataset}</p>
        <p>{glyph.source.calligrapher || '书家未标注'}</p>
        <div className="source-meta">
          <span>
            {
              {
                font: '字体字形',
                original: '原帖字形',
                fallback: '结构替补',
                generated: '生成字形',
              }[glyph.provenance.type]
            }
          </span>
          {glyph.asset.processing === 'ink-mask' && <span>已净底</span>}
          <span>{glyph.source.license || '授权未标注'}</span>
        </div>
        <details className="advanced provenance-details"><summary>来源详情 / Glyph details</summary>
          <dl>
            <dt>Semantic character</dt><dd>{semanticIdentity(glyph).text}</dd>
            <dt>Unicode</dt><dd>{semanticIdentity(glyph).codepoints.join(' ')}</dd>
            <dt>Variant</dt><dd>{glyph.variant?.type || 'Unknown'} · {glyph.variant?.id || 'Unknown'}</dd>
            <dt>Font glyph</dt><dd>{glyph.variant?.font_glyph_id ?? 'Unknown'} · {glyph.variant?.glyph_name || 'Unknown'}</dd>
            <dt>Locale / script</dt><dd>{glyph.source.locale || 'Unknown'} / {glyph.source.script || 'Unknown'}</dd>
            <dt>Tradition / period</dt><dd>{glyph.source.writing_tradition || 'Unknown'} / {glyph.source.period || 'Unknown'}</dd>
            <dt>Collection / work</dt><dd>{glyph.source.source_collection || glyph.source.dataset} / {glyph.source.work || 'Unknown'}</dd>
            <dt>Author / designer</dt><dd>{glyph.source.designer || glyph.source.calligrapher || 'Unknown'}</dd>
            <dt>Licence</dt><dd>{glyph.source.license || 'Unknown'}{glyph.source.license_url && /^https?:\/\//.test(glyph.source.license_url) && <a href={glyph.source.license_url} target="_blank" rel="noreferrer"> · Licence terms</a>}{glyph.source.license_text && /^(fonts\/licenses\/OFL-[a-z-]+\.txt|japanese\/licenses\/CC-BY-SA-4\.0\.txt|demo\/licenses\/[a-zA-Z0-9.-]+\.txt)$/.test(glyph.source.license_text) && <a href={`${import.meta.env.BASE_URL}${glyph.source.license_text}`} target="_blank" rel="noreferrer"> · Bundled licence</a>}</dd>
            <dt>Attribution</dt><dd>{glyph.source.attribution || 'Unknown'}</dd>
            <dt>Source URI</dt><dd>{glyph.source.source_uri && /^https?:\/\//.test(glyph.source.source_uri) ? <a href={glyph.source.source_uri} target="_blank" rel="noreferrer">{glyph.source.source_uri}</a> : 'Unknown'}</dd>
            <dt>Source checksum</dt><dd>{glyph.source.source_checksum || 'Unknown'}</dd>
            <dt>Asset checksum</dt><dd>{glyph.asset.checksum || 'Unknown'}</dd>
            <dt>Page / source bbox</dt><dd>{String(glyph.metadata?.page || 'Unknown')} / {JSON.stringify(glyph.metadata?.source_bbox || null)}</dd>
            <dt>Rights</dt><dd>{Object.entries(glyph.source.rights || {}).map(([key,value]) => <div key={key}>{key}: {value === null ? 'Unknown' : String(value)}</div>)}</dd>
          </dl>
        </details>
      </section>
      <p className="field-hint px-4">方向键微移，Shift 加速；Delete 删除。</p>
    </aside>
  )
}
