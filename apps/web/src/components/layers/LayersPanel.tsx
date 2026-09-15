import { ArrowDown, ArrowUp, Layers3, Trash2 } from 'lucide-react'
import { useEditorStore } from '../../stores/editor'
import { Button, cn } from '../ui'

export function LayersPanel() {
  const glyphs = useEditorStore((state) => state.project.glyphs)
  const selectedId = useEditorStore((state) => state.selectedId)
  const selectGlyph = useEditorStore((state) => state.selectGlyph)
  const reorderGlyph = useEditorStore((state) => state.reorderGlyph)
  const removeGlyph = useEditorStore((state) => state.removeGlyph)

  return (
    <section className="flex h-[154px] shrink-0 flex-col border-t border-black/10 bg-[#e7e1d5]">
      <div className="flex h-9 items-center justify-between border-b border-black/10 px-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-ink/65">
          <Layers3 className="h-3.5 w-3.5" /> 图层
          <span className="font-normal text-ink/35">从上到下</span>
        </div>
        <span className="text-[10px] text-ink/35">拖动字形直接改变位置，用箭头调整叠放顺序</span>
      </div>
      <div className="panel-scroll flex min-h-0 flex-1 items-stretch gap-2 overflow-x-auto p-2">
        {glyphs.length === 0 && <div className="grid h-full w-full place-items-center text-xs text-ink/35">暂无图层</div>}
        {[...glyphs].reverse().map((glyph) => {
          const active = glyph.id === selectedId
          return (
            <div
              key={glyph.id}
              role="button"
              tabIndex={0}
              onClick={() => selectGlyph(glyph.id)}
              onKeyDown={(event) => event.key === 'Enter' && selectGlyph(glyph.id)}
              className={cn(
                'group relative flex w-[112px] shrink-0 cursor-pointer items-center gap-2 rounded-lg border bg-white/65 p-2 text-left transition',
                active ? 'border-cinnabar/50 ring-1 ring-cinnabar/20' : 'border-black/10 hover:bg-white',
              )}
            >
              <div className="grid h-12 w-12 shrink-0 place-items-center rounded bg-[#f7f2e8]">
                <img src={glyph.asset.url} alt="" draggable={false} className="h-full w-full object-contain p-1.5 mix-blend-multiply" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-display text-2xl leading-none">{glyph.character}</p>
                <p className="mt-1 truncate text-[10px] text-ink/45">{glyph.source.calligrapher || glyph.source.dataset}</p>
                <p className="text-[9px] text-ink/35">{Math.round(glyph.transform.rotation)}° · {Math.round(glyph.appearance.opacity * 100)}%</p>
              </div>
              <div className="absolute right-1 top-1 hidden items-center gap-0.5 rounded bg-white/95 p-0.5 shadow-sm group-hover:flex">
                <Button variant="ghost" size="icon" className="h-5 w-5" title="上移一层" onClick={(event) => { event.stopPropagation(); reorderGlyph(glyph.id, 'forward') }}><ArrowUp className="h-3 w-3" /></Button>
                <Button variant="ghost" size="icon" className="h-5 w-5" title="下移一层" onClick={(event) => { event.stopPropagation(); reorderGlyph(glyph.id, 'backward') }}><ArrowDown className="h-3 w-3" /></Button>
                <Button variant="ghost" size="icon" className="h-5 w-5 text-cinnabar" title="删除" onClick={(event) => { event.stopPropagation(); removeGlyph(glyph.id) }}><Trash2 className="h-3 w-3" /></Button>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
