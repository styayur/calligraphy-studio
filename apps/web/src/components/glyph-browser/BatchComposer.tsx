import { LayoutGrid, Rows3, WandSparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { composeBatch, getMetadata } from '../../api/client'
import { useEditorStore } from '../../stores/editor'
import type { BatchLayout, MetadataResponse } from '../../types'
import { Button, cn } from '../ui'

const DEFAULT_TEXT = '春眠不觉晓\n处处闻啼鸟'

export function BatchComposer() {
  const [text, setText] = useState(DEFAULT_TEXT)
  const [layout, setLayout] = useState<BatchLayout>('grid')
  const [columns, setColumns] = useState(5)
  const [cellSize, setCellSize] = useState(170)
  const [gap, setGap] = useState(4)
  const [style, setStyle] = useState('草书')
  const [dataset, setDataset] = useState('')
  const [calligrapher, setCalligrapher] = useState('')
  const [useFallback, setUseFallback] = useState(true)
  const [meta, setMeta] = useState<MetadataResponse | null>(null)
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(false)
  const addGlyphs = useEditorStore((state) => state.addGlyphs)

  useEffect(() => {
    getMetadata().then((payload) => {
      setMeta(payload)
      const cursiveDataset = payload.datasets.find((item) => item.includes('Cursive'))
      if (cursiveDataset) setDataset(cursiveDataset)
    }).catch(() => undefined)
  }, [])

  const createLayout = async () => {
    setLoading(true)
    setStatus('')
    try {
      const response = await composeBatch({
        text,
        layout,
        columns,
        cell_width: cellSize,
        cell_height: cellSize,
        gap_x: gap,
        gap_y: gap,
        start_x: 80,
        start_y: 80,
        calligrapher: calligrapher || undefined,
        style: style || undefined,
        dataset: dataset || undefined,
        use_structural_fallback: useFallback,
      })
      addGlyphs(response.placements.map((placement) => placement.glyph))
      setStatus(
        response.missing.length
          ? `已排入 ${response.resolved_characters}/${response.total_characters} 字；缺字：${response.missing.join(' ')}`
          : `已将 ${response.resolved_characters} 字排入画布`,
      )
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '批量排版失败')
    } finally {
      setLoading(false)
    }
  }

  const layoutOptions: Array<{ value: BatchLayout; label: string; icon: typeof LayoutGrid }> = [
    { value: 'grid', label: '顺序网格', icon: LayoutGrid },
    { value: 'horizontal-ltr', label: '横排', icon: Rows3 },
    { value: 'vertical-rtl', label: '竖排右起', icon: Rows3 },
  ]

  return (
    <div className="space-y-4 p-4">
      <div>
        <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-cinnabar">Batch Typesetting</p>
        <h2 className="font-display text-2xl">批量文本集字</h2>
        <p className="mt-1 text-xs leading-5 text-ink/50">每行可独立成句；竖排按右起列方向排列。</p>
      </div>

      <textarea
        value={text}
        onChange={(event) => setText(event.target.value)}
        rows={7}
        placeholder="输入或粘贴文本，每个汉字将成为一个 Glyph 图层"
        className="w-full resize-none rounded-lg border border-black/10 bg-white/75 p-3 text-sm leading-6 outline-none ring-cinnabar/15 focus:ring-2"
      />

      <div className="grid grid-cols-3 gap-2">
        {layoutOptions.map((option) => {
          const Icon = option.icon
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => setLayout(option.value)}
              className={cn(
                'rounded-lg border px-2 py-2 text-[11px] transition',
                layout === option.value ? 'border-cinnabar/45 bg-cinnabar/5 text-cinnabar' : 'border-black/10 bg-white/55 text-ink/60',
              )}
            >
              <Icon className="mx-auto mb-1 h-4 w-4" />
              {option.label}
            </button>
          )
        })}
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs text-ink/60">
        <label>
          <span className="mb-1 block">列数</span>
          <input type="number" min={1} max={30} value={columns} onChange={(event) => setColumns(Number(event.target.value))} className="h-8 w-full rounded-md border border-black/10 bg-white/75 px-2" />
        </label>
        <label>
          <span className="mb-1 block">字格</span>
          <input type="number" min={60} max={500} value={cellSize} onChange={(event) => setCellSize(Number(event.target.value))} className="h-8 w-full rounded-md border border-black/10 bg-white/75 px-2" />
        </label>
        <label>
          <span className="mb-1 block">间距</span>
          <input type="number" min={-20} max={100} value={gap} onChange={(event) => setGap(Number(event.target.value))} className="h-8 w-full rounded-md border border-black/10 bg-white/75 px-2" />
        </label>
        <label>
          <span className="mb-1 block">书体</span>
          <select value={style} onChange={(event) => setStyle(event.target.value)} className="h-8 w-full rounded-md border border-black/10 bg-white/75 px-2">
            <option value="">自动</option>
            {meta?.styles.map((item) => <option key={item.id}>{item.name}</option>)}
          </select>
        </label>
        <label className="col-span-2">
          <span className="mb-1 block">数据源</span>
          <select value={dataset} onChange={(event) => setDataset(event.target.value)} className="h-8 w-full rounded-md border border-black/10 bg-white/75 px-2">
            <option value="">全部、优先草书</option>
            {meta?.datasets.map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
        <label className="col-span-2">
          <span className="mb-1 block">书家</span>
          <select value={calligrapher} onChange={(event) => setCalligrapher(event.target.value)} className="h-8 w-full rounded-md border border-black/10 bg-white/75 px-2">
            <option value="">不限</option>
            {meta?.calligraphers.map((item) => <option key={item.id}>{item.name}</option>)}
          </select>
        </label>
      </div>

      <label className="flex items-start gap-2 rounded-lg border border-black/10 bg-white/45 p-3 text-xs text-ink/60">
        <input type="checkbox" checked={useFallback} onChange={(event) => setUseFallback(event.target.checked)} className="mt-0.5" />
        <span><strong className="font-medium text-ink/75">缺字结构替补</strong><br />真实字形缺失时使用 Hanzi Writer，并明确标记为 fallback。</span>
      </label>

      <Button className="w-full" onClick={createLayout} disabled={loading || !text.trim()}>
        <WandSparkles className="h-4 w-4" />
        {loading ? '正在排版…' : '生成到画布'}
      </Button>
      {status && <p className="rounded-md bg-black/5 p-2 text-[11px] leading-5 text-ink/60">{status}</p>}
    </div>
  )
}
