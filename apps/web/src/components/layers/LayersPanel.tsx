import { useEditorStore } from '../../stores/editor'

export function LayersPanel() {
  const { project, selectedId, selectGlyph } = useEditorStore()
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
      <div className="panel-scroll">
        {project.glyphs.map((glyph, index) => (
          <button
            key={glyph.id}
            aria-label={`选择第${index + 1}字${glyph.character}`}
            aria-pressed={selectedId === glyph.id}
            onClick={() => selectGlyph(glyph.id)}
            title={`${glyph.character} · ${glyph.source.work || glyph.source.dataset}`}
          >
            <img src={glyph.asset.url} alt={glyph.character} />
          </button>
        ))}
      </div>
    </section>
  )
}
