import { useEffect, useState } from 'react'
import { GlyphCanvas } from './canvas/GlyphCanvas'
import { Toolbar } from './components/editor/Toolbar'
import { BatchComposer } from './components/glyph-browser/BatchComposer'
import { GlyphBrowser } from './components/glyph-browser/GlyphBrowser'
import { Inspector } from './components/inspector/Inspector'
import { WorkHarmony } from './components/inspector/VisualProfile'
import { LongRoll } from './components/long-roll/LongRoll'
import { LayersPanel } from './components/layers/LayersPanel'
import { useEditorStore } from './stores/editor'
import { readDraft, validateProject, writeDraft } from './lib/project'
import type { Draft } from './lib/project'

export default function App() {
  const [mode, setMode] = useState<'studio' | 'roll'>('studio')
  const [rollVisited, setRollVisited] = useState(false)
  const [tab, setTab] = useState('compose')
  const [searchVisited, setSearchVisited] = useState(false)
  const [ready, setReady] = useState(false)
  const [mobilePanel, setMobilePanel] = useState('edit')
  const canvas = useEditorStore((s) => s.project.canvas)
  const glyphCount = useEditorStore((s) => s.project.glyphs.length)
  const selectedId = useEditorStore((s) => s.selectedId)
  const setCanvas = useEditorStore((s) => s.setCanvas)

  useEffect(() => {
    let active = true
    readDraft()
      .then((draft) => {
        if (!active) return
        if (draft)
          useEditorStore.getState().loadProject(draft.name, validateProject(draft.document))
        useEditorStore
          .getState()
          .setLocalStatus(draft ? '已恢复本机草稿' : '草稿自动保存在本机')
      })
      .catch(() => {
        if (active) useEditorStore.getState().setLocalStatus('草稿恢复失败，请从项目文件载入')
      })
      .finally(() => {
        if (active) setReady(true)
      })
    return () => {
      active = false
    }
  }, [])
  useEffect(() => {
    if (!ready) return
    let pending: Draft | null = null
    let writing = false
    const save = async () => {
      if (writing) return
      writing = true
      while (pending) {
        const draft = pending
        pending = null
        try {
          await writeDraft(draft)
          const latest = useEditorStore.getState()
          if (latest.project === draft.document && latest.projectName === draft.name)
            latest.setLocalStatus('草稿已保存到本机')
        } catch {
          useEditorStore.getState().setLocalStatus('本机保存失败，请下载项目备份')
        }
      }
      writing = false
    }
    return useEditorStore.subscribe((state, previous) => {
      if (state.project === previous.project && state.projectName === previous.projectName)
        return
      pending = { name: state.projectName, document: state.project }
      state.setLocalStatus('正在保存草稿…')
      void save()
    })
  }, [ready])
  useEffect(() => {
    const keyboard = (e: KeyboardEvent) => {
      if (mode !== 'studio') return
      const target = e.target as HTMLElement
      if (target.closest('input, textarea, select, [contenteditable="true"], [role="dialog"]'))
        return
      const state = useEditorStore.getState()
      const modifier = e.ctrlKey || e.metaKey
      if (modifier && e.key.toLowerCase() === 'z') {
        e.preventDefault()
        e.shiftKey ? state.redo() : state.undo()
        return
      }
      if (modifier && e.key.toLowerCase() === 'y') {
        e.preventDefault()
        state.redo()
        return
      }
      if (e.key === 'Escape') state.selectGlyph(null)
      if (!state.selectedId) return
      if (e.key === 'Delete' || e.key === 'Backspace') {
        e.preventDefault()
        state.removeGlyph(state.selectedId)
      }
      if (modifier && e.key.toLowerCase() === 'd') {
        e.preventDefault()
        state.duplicateGlyph(state.selectedId)
      }
      const glyph = state.project.glyphs.find((g) => g.id === state.selectedId)
      if (glyph && ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.key)) {
        e.preventDefault()
        const step = e.shiftKey ? 10 : 1
        if (!e.repeat) state.beginHistory()
        state.setGlyphTransform(
          glyph.id,
          {
            x:
              glyph.transform.x +
              (e.key === 'ArrowLeft' ? -step : e.key === 'ArrowRight' ? step : 0),
            y:
              glyph.transform.y +
              (e.key === 'ArrowUp' ? -step : e.key === 'ArrowDown' ? step : 0),
          },
          { recordHistory: false },
        )
      }
    }
    window.addEventListener('keydown', keyboard)
    return () => window.removeEventListener('keydown', keyboard)
  }, [mode])

  return (
    <div className="studio-shell">
      {mode === 'studio' && <Toolbar />}
      <nav className="mode-switch" aria-label="创作模式">
        <button aria-pressed={mode === 'studio'} onClick={() => setMode('studio')}>
          集字工作台 · 1000 字
        </button>
        <button
          aria-pressed={mode === 'roll'}
          onClick={() => {
            setRollVisited(true)
            setMode('roll')
          }}
        >
          长卷模式 · 自动成篇
        </button>
      </nav>
      <nav className={mode === 'studio' ? 'mobile-nav' : 'hidden'} aria-label="工作区">
        <button aria-pressed={mobilePanel === 'edit'} onClick={() => setMobilePanel('edit')}>
          文字与字库
        </button>
        <button
          aria-pressed={mobilePanel === 'canvas'}
          onClick={() => setMobilePanel('canvas')}
        >
          作品预览 {glyphCount > 0 && `(${glyphCount})`}
        </button>
      </nav>
      {ready ? (
        <main
          className={
            mode === 'studio'
              ? `workspace mobile-${mobilePanel} ${selectedId ? 'has-selection' : ''}`
              : 'hidden'
          }
        >
          <aside className="library-panel">
            <div className="panel-tabs">
              <button aria-pressed={tab === 'compose'} onClick={() => setTab('compose')}>
                集字
              </button>
              <button
                aria-pressed={tab === 'search'}
                onClick={() => {
                  setSearchVisited(true)
                  setTab('search')
                }}
              >
                查字
              </button>
            </div>
            <div className={tab === 'compose' ? 'panel-scroll composition-body' : 'hidden'}>
              <BatchComposer />
            </div>
            <div className={tab === 'search' ? 'search-body' : 'hidden'}>
              {searchVisited && <GlyphBrowser />}
            </div>
            <footer className="library-footer">
              集字工作台 <span>写一句，成一幅。</span>
            </footer>
          </aside>
          <section className="canvas-column">
            <div className="canvas-toolbar">
              <span>
                纸面{' '}
                <span className="dimension">
                  {canvas.width} × {canvas.height}
                </span>
              </span>
              <div className="paper-swatches" aria-label="纸色">
                {[
                  ['#ffffff', '白纸'],
                  ['#f5f0e4', '米纸'],
                  ['#e7ebe4', '青纸'],
                ].map(([color, label]) => (
                  <button
                    key={color}
                    aria-label={label}
                    aria-pressed={canvas.background === color}
                    style={{ background: color }}
                    onClick={() => setCanvas({ background: color })}
                  />
                ))}
              </div>
              <span className="canvas-help">点击选字 · 拖动调整</span>
            </div>
            <WorkHarmony />
            <GlyphCanvas />
            <LayersPanel />
          </section>
          <Inspector />
        </main>
      ) : (
        <div className="loading-workspace">正在恢复工作台…</div>
      )}
      {rollVisited && <LongRoll active={mode === 'roll'} />}
    </div>
  )
}
