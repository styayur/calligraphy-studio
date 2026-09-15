import { X } from 'lucide-react'
import { GlyphCanvas } from './canvas/GlyphCanvas'
import { Toolbar } from './components/editor/Toolbar'
import { BatchComposer } from './components/glyph-browser/BatchComposer'
import { GlyphBrowser } from './components/glyph-browser/GlyphBrowser'
import { Inspector } from './components/inspector/Inspector'
import { LayersPanel } from './components/layers/LayersPanel'
import { useEditorStore } from './stores/editor'
import { Button } from './components/ui'

export default function App() {
  const batchOpen = useEditorStore((state) => state.batchOpen)
  const setBatchOpen = useEditorStore((state) => state.setBatchOpen)

  return (
    <div className="flex h-full min-h-0 flex-col bg-paper text-ink">
      <Toolbar />
      <main className="relative flex min-h-0 flex-1">
        <GlyphBrowser />
        <section className="flex min-h-0 min-w-0 flex-1 flex-col">
          <GlyphCanvas />
          <LayersPanel />
        </section>
        <Inspector />
        {batchOpen && (
          <div className="absolute inset-0 z-50 bg-ink/15 backdrop-blur-[1px]" onMouseDown={() => setBatchOpen(false)}>
            <aside
              className="panel-scroll absolute bottom-3 left-[316px] top-3 w-[420px] overflow-y-auto rounded-xl border border-black/10 bg-[#f4efe5] shadow-2xl"
              onMouseDown={(event) => event.stopPropagation()}
            >
              <div className="flex items-center justify-between border-b border-black/10 px-4 py-3">
                <span className="text-xs font-semibold text-ink/55">批量排版</span>
                <Button variant="ghost" size="icon" onClick={() => setBatchOpen(false)} aria-label="关闭批量集字">
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <BatchComposer />
            </aside>
          </div>
        )}
      </main>
    </div>
  )
}
