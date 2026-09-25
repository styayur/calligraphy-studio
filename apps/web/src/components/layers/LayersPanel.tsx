import { useEditorStore } from '../../stores/editor'
import { useEffect, useRef, useState } from 'react'

export function LayersPanel() {
  const { project, selectedId, selectGlyph } = useEditorStore()
  const viewport = useRef<HTMLDivElement>(null)
  const [scroll, setScroll] = useState(0),
    [width, setWidth] = useState(800)
  useEffect(() => {
    if (!viewport.current) return
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width))
    observer.observe(viewport.current)
    return () => observer.disconnect()
  }, [project.glyphs.length > 0])
  useEffect(() => {
    const index = project.glyphs.findIndex((g) => g.id === selectedId)
    if (index < 0 || !viewport.current) return
    const x = index * 52,
      element = viewport.current
    if (x < element.scrollLeft || x + 52 > element.scrollLeft + element.clientWidth)
      element.scrollLeft = x
  }, [selectedId, project.glyphs])
  const virtual = project.glyphs.length > 60
  const start = virtual ? Math.max(0, Math.floor(scroll / 52) - 3) : 0
  const end = virtual
    ? Math.min(project.glyphs.length, Math.ceil((scroll + width) / 52) + 3)
    : project.glyphs.length
  if (!project.glyphs.length)
    return (
      <div className="canvas-footer">
        <span>纸面随文字自动适配</span>
        <span>支持横排、竖排与方格</span>
      </div>
    )
  return (
    <section className="character-strip" aria-label="作品中的字">
      <span className="strip-label">
        选字 <small>{project.glyphs.length}</small>
      </span>
      <div
        className="panel-scroll"
        ref={viewport}
        onScroll={(e) => setScroll(e.currentTarget.scrollLeft)}
      >
        <div
          style={
            virtual
              ? {
                  position: 'relative',
                  width: project.glyphs.length * 52,
                  height: 46,
                  flexShrink: 0,
                }
              : { display: 'flex', gap: 8 }
          }
        >
          {project.glyphs.slice(start, end).map((glyph, localIndex) => {
            const index = start + localIndex
            return (
              <button
                key={glyph.id}
                style={virtual ? { position: 'absolute', left: index * 52 } : undefined}
                aria-label={`选择第${index + 1}字${glyph.character}`}
                aria-pressed={selectedId === glyph.id}
                onClick={() => selectGlyph(glyph.id)}
                title={`${glyph.character} · ${glyph.source.work || glyph.source.dataset}`}
              >
                <img src={glyph.asset.url} alt={glyph.character} />
              </button>
            )
          })}
        </div>
      </div>
    </section>
  )
}
