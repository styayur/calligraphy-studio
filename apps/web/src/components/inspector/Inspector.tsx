import { Info, Move3D, RotateCw, Scaling, ShieldAlert } from 'lucide-react'
import { useEditorStore } from '../../stores/editor'
import { SimilarGlyphs } from './SimilarGlyphs'
import type { GlyphTransform } from '../../types'

function NumberField({ label, value, step = 1, onChange, onFocus }: {
  label: string
  value: number
  step?: number
  onChange: (value: number) => void
  onFocus: () => void
}) {
  return (
    <label className="grid grid-cols-[52px_1fr] items-center gap-2 text-xs text-ink/60">
      <span>{label}</span>
      <input
        type="number"
        step={step}
        value={Number.isFinite(value) ? Number(value.toFixed(2)) : 0}
        onFocus={onFocus}
        onChange={(event) => onChange(Number(event.target.value))}
        className="h-8 min-w-0 rounded-md border border-black/10 bg-white/75 px-2 text-right text-xs text-ink outline-none focus:border-cinnabar/45"
      />
    </label>
  )
}

export function Inspector() {
  const glyph = useEditorStore((state) => state.project.glyphs.find((item) => item.id === state.selectedId))
  const beginHistory = useEditorStore((state) => state.beginHistory)
  const setGlyphTransform = useEditorStore((state) => state.setGlyphTransform)
  const setGlyphAppearance = useEditorStore((state) => state.setGlyphAppearance)

  if (!glyph) {
    return (
      <aside className="flex h-full w-[288px] shrink-0 flex-col border-l border-black/10 bg-[#ece7dc]/90">
        <div className="border-b border-black/10 p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-cinnabar">Inspector</p>
          <h2 className="font-display text-2xl">属性</h2>
        </div>
        <div className="grid flex-1 place-items-center p-6 text-center">
          <div>
            <Info className="mx-auto h-8 w-8 text-ink/25" />
            <p className="mt-3 text-sm text-ink/55">选择一个字形以编辑几何与合成属性</p>
          </div>
        </div>
      </aside>
    )
  }

  const transformPatch = (patch: Partial<GlyphTransform>) => setGlyphTransform(glyph.id, patch, { recordHistory: false })

  return (
    <aside className="panel-scroll flex h-full w-[288px] shrink-0 flex-col overflow-y-auto border-l border-black/10 bg-[#ece7dc]/90">
      <div className="border-b border-black/10 p-4">
        <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-cinnabar">Inspector</p>
        <div className="mt-1 flex items-end justify-between">
          <div>
            <h2 className="font-display text-4xl leading-none">{glyph.character}</h2>
            <p className="mt-2 text-xs text-ink/55">{[glyph.source.calligrapher, glyph.source.style].filter(Boolean).join(' · ') || '未标注'}</p>
          </div>
          <span className="rounded-full bg-black/5 px-2 py-1 text-[10px] text-ink/55">{glyph.provenance.type}</span>
        </div>
      </div>

      <section className="border-b border-black/10 p-4">
        <h3 className="mb-3 flex items-center gap-2 text-xs font-semibold text-ink/70"><Move3D className="h-3.5 w-3.5" /> 位置</h3>
        <div className="grid gap-2">
          <NumberField label="X" value={glyph.transform.x} onFocus={beginHistory} onChange={(x) => transformPatch({ x })} />
          <NumberField label="Y" value={glyph.transform.y} onFocus={beginHistory} onChange={(y) => transformPatch({ y })} />
        </div>
      </section>

      <section className="border-b border-black/10 p-4">
        <h3 className="mb-3 flex items-center gap-2 text-xs font-semibold text-ink/70"><RotateCw className="h-3.5 w-3.5" /> 旋转与倾斜</h3>
        <div className="grid gap-2">
          <NumberField label="旋转" value={glyph.transform.rotation} onFocus={beginHistory} onChange={(rotation) => transformPatch({ rotation })} />
          <NumberField label="倾斜 X" value={glyph.transform.skewX} onFocus={beginHistory} onChange={(skewX) => transformPatch({ skewX })} />
          <NumberField label="倾斜 Y" value={glyph.transform.skewY} onFocus={beginHistory} onChange={(skewY) => transformPatch({ skewY })} />
        </div>
      </section>

      <section className="border-b border-black/10 p-4">
        <h3 className="mb-3 flex items-center gap-2 text-xs font-semibold text-ink/70"><Scaling className="h-3.5 w-3.5" /> 缩放</h3>
        <div className="grid gap-2">
          <NumberField label="X" value={glyph.transform.scaleX} step={0.05} onFocus={beginHistory} onChange={(scaleX) => transformPatch({ scaleX })} />
          <NumberField label="Y" value={glyph.transform.scaleY} step={0.05} onFocus={beginHistory} onChange={(scaleY) => transformPatch({ scaleY })} />
        </div>
      </section>

      <section className="border-b border-black/10 p-4">
        <h3 className="mb-3 text-xs font-semibold text-ink/70">合成</h3>
        <label className="mb-3 block text-xs text-ink/60">
          <div className="mb-2 flex items-center justify-between"><span>不透明度</span><span className="tabular-nums text-ink/80">{Math.round(glyph.appearance.opacity * 100)}%</span></div>
          <input type="range" min="0" max="1" step="0.01" value={glyph.appearance.opacity} onPointerDown={beginHistory} onChange={(event) => setGlyphAppearance(glyph.id, { opacity: Number(event.target.value) }, { recordHistory: false })} className="w-full" />
        </label>
        <label className="grid grid-cols-[70px_1fr] items-center gap-2 text-xs text-ink/60">
          <span>混合模式</span>
          <select value={glyph.appearance.blendMode} onFocus={beginHistory} onChange={(event) => setGlyphAppearance(glyph.id, { blendMode: event.target.value }, { recordHistory: false })} className="h-8 min-w-0 rounded-md border border-black/10 bg-white/75 px-2 text-xs">
            <option value="source-over">Normal</option>
            <option value="multiply">Multiply</option>
            <option value="screen">Screen</option>
            <option value="overlay">Overlay</option>
            <option value="darken">Darken</option>
            <option value="lighten">Lighten</option>
          </select>
        </label>
      </section>

      <SimilarGlyphs glyphId={glyph.glyph_id} />

      <section className="p-4">
        <h3 className="mb-3 text-xs font-semibold text-ink/70">来源与授权</h3>
        <dl className="space-y-2 text-xs">
          <div className="flex justify-between gap-3"><dt className="text-ink/45">数据集</dt><dd className="text-right">{glyph.source.dataset}</dd></div>
          <div className="flex justify-between gap-3"><dt className="text-ink/45">作品</dt><dd className="text-right">{glyph.source.work || '未标注'}</dd></div>
          <div className="flex justify-between gap-3"><dt className="text-ink/45">授权</dt><dd className="text-right">{glyph.source.license || '未标注'}</dd></div>
        </dl>
        {glyph.source.license?.includes('NC') || glyph.source.license?.includes('ND') ? (
          <div className="mt-3 flex gap-2 rounded-lg border border-amber-800/15 bg-amber-900/5 p-2.5 text-[11px] leading-relaxed text-amber-900">
            <ShieldAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            该数据源有非商业或禁止演绎限制。生成式补字与商业发布前需再次核验授权。
          </div>
        ) : null}
      </section>
    </aside>
  )
}