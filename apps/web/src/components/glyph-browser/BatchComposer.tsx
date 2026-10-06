import { useEffect, useRef, useState } from 'react'
import { ArrowRight, Loader2 } from 'lucide-react'
import { initialCandidates, resolveCharacters, type CandidateSource } from '../../api/candidates'
import { SourcePolicyControls } from './SourcePolicyControls'
import { DEFAULT_POLICY, type CandidatePolicy } from '../../lib/candidatePolicy'
import { layoutText, placeGlyph, textLines } from '../../lib/composition'
import { useEditorStore } from '../../stores/editor'
import type { BatchLayout, Glyph } from '../../types'
import { Button } from '../ui'

export function BatchComposer() {
  const projectText = useEditorStore((s) => s.project.text)
  const settings = useEditorStore((s) => s.project.composition)
  const [text, setText] = useState(() => {
    try {
      const draft = JSON.parse(localStorage.getItem('calligraphy-input') || 'null')
      if (draft?.projectText === (projectText ?? null) && typeof draft.text === 'string')
        return draft.text as string
    } catch {
      /* A blocked browser store should not prevent editing. */
    }
    return projectText ?? '明月松间照\n清泉石上流'
  })
  const previousText = useRef(projectText)
  const [layout, setLayout] = useState<BatchLayout>('vertical-rtl')
  const [columns, setColumns] = useState(5)
  const [size, setSize] = useState(160)
  const [gap, setGap] = useState(12)
  const [margin, setMargin] = useState(64)
  const [style, setStyle] = useState('行书')
  const [source, setSource] = useState<CandidateSource>('fonts')
  const [policy, setPolicy] = useState<CandidatePolicy>(DEFAULT_POLICY)
  const [punctuation, setPunctuation] = useState(false)
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(false)
  const compose = useEditorStore((s) => s.compose)
  useEffect(() => {
    if (previousText.current !== projectText) setText(projectText ?? '')
    previousText.current = projectText
  }, [projectText])
  useEffect(() => {
    try {
      localStorage.setItem(
        'calligraphy-input',
        JSON.stringify({ projectText: projectText ?? null, text }),
      )
    } catch {
      setStatus('输入文字未能保存到本机，请及时生成并下载项目。')
    }
  }, [text, projectText])
  useEffect(() => {
    if (!settings) return
    setLayout(settings.layout)
    setColumns(settings.columns)
    setSize(settings.size)
    setGap(settings.gap)
    setMargin(settings.margin)
    setPunctuation(settings.punctuation)
    setStyle(settings.style)
    setSource(settings.source)
    setPolicy(settings.policy || DEFAULT_POLICY)
  }, [settings])
  const count = textLines(text, punctuation).flat().length

  const create = async () => {
    const previousProject = useEditorStore.getState().project
    setLoading(true)
    setStatus('正在加载字库…')
    try {
      const plan = layoutText(text, {
        layout,
        columns,
        size,
        gap,
        margin,
        punctuation,
      })
      const found = await resolveCharacters(
        plan.positions.map((p) => p.character),
        async (character) => {
          // Initial composition fetches a small page; further variants load only on selection.
          const page = await initialCandidates(character, source, policy.writing_tradition === 'Japanese' ? '' : style, 4, undefined, { ...policy, vertical: layout === 'vertical-rtl' })
          return page.items[0]
        },
        (done, total) => setStatus(`正在加载字库 ${done}/${total} 个不同字…`),
      )
      const resolved = new Map<string, Glyph>()
      found.forEach((glyph, character) => {
        if (glyph) resolved.set(character, glyph)
      })
      const missing = [
        ...new Set(
          plan.positions.filter((p) => !resolved.has(p.character)).map((p) => p.character),
        ),
      ]
      if (!resolved.size)
        throw new Error(`未找到可用字形：${missing.join('')}。请切换书体或字形来源。`)
      const glyphs = plan.positions.flatMap((p) => {
        const glyph = resolved.get(p.character)
        return glyph ? [placeGlyph(glyph, p.x, p.y, plan.size)] : []
      })
      if (useEditorStore.getState().project !== previousProject)
        throw new Error('作品已更改，请重新生成以应用这段文字。')
      compose(
        glyphs,
        {
          width: Math.max(100, plan.width),
          height: Math.max(100, plan.height),
          background: previousProject.canvas.background,
        },
        text,
        { layout, columns, size, gap, margin, punctuation, style, source, policy },
      )
      setStatus(
        missing.length
          ? `已排入 ${glyphs.length}/${count} 字，缺字「${missing.join('、')}」已留空位。可换书体重新集字。`
          : `已排入 ${glyphs.length} 字。${plan.fit < 1 ? '纸面已等比缩小；可调整每行或列字数改善阅读。' : ''}点击纸面上的字，可选择其他字形。`,
      )
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '集字失败，请重试')
    } finally {
      setLoading(false)
    }
  }
  return (
    <fieldset className="composer" disabled={loading} aria-label="集字排版">
      <div className="section-title">
        <h2>文字集字</h2>
        <span>{count} / 1000 字</span>
      </div>
      <label className="sr-only" htmlFor="compose-text">
        集字内容
      </label>
      <textarea
        id="compose-text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={5}
        placeholder="输入文字，换行分句"
      />
      <div className="sample-row">
        <span>试一试</span>
        {['明月松间照\n清泉石上流', '春眠不觉晓\n处处闻啼鸟', '山水清音'].map((sample, i) => (
          <button key={sample} onClick={() => setText(sample)}>
            {['山居秋暝', '春晓', '四字横幅'][i]}
          </button>
        ))}
      </div>
      <SourcePolicyControls policy={policy} onChange={setPolicy} />
      {policy.writing_tradition === 'Japanese' && <div className="sample-row"><span>日本語</span><button onClick={() => setText('日本の書道\nあいうえお\nアイウエオ')}>漢字とかな</button><button onClick={() => { setText('「春の海」、ゆらり。'); setPunctuation(true) }}>句読点</button></div>}
      <div className="field-grid">
        <label>
          书体
          <select aria-label="书体" value={style} disabled={policy.writing_tradition === 'Japanese'} onChange={(e) => setStyle(e.target.value)}>
            <option>楷书</option>
            <option>行书</option>
            <option>草书</option>
          </select>
        </label>
        <label>
          来源 / Source
          <select
            aria-label="字形来源"
            value={source}
            onChange={(e) => setSource(e.target.value as CandidateSource)}
          >
            <option value="fonts">字体 / Font</option>
            <option value="original">原帖 / Original</option>
            <option value="all">字体与原帖 / Fonts & historical</option>
            <option value="fallback">结构替补 / Structural fallback</option>
          </select>
        </label>
      </div>
      <p className="field-hint">
        {source === 'fonts'
          ? policy.writing_tradition === 'Japanese' ? 'Yuji 字体；変体仮名需明确选择。Font glyphs are not manuscripts.' : '内置三款开源字体，按实际字库覆盖集字。'
          : '使用已收录的原帖图片；缺字会留空并提示。'}
      </p>
      {policy.writing_tradition === 'Japanese' && layout === 'vertical-rtl' && <p className="field-hint">日文字体使用 vert / vrt2 与竖排句读点位置；不支持连绵字、禁则处理或縦中横。Japanese vertical layout is a glyph-cell composition.</p>}
      <div className="segmented" aria-label="排版方向">
        {(
          [
            ['vertical-rtl', '竖排'],
            ['horizontal-ltr', '横排'],
            ['grid', '方格'],
          ] as const
        ).map(([value, label]) => (
          <button key={value} aria-pressed={layout === value} onClick={() => setLayout(value)}>
            {label}
          </button>
        ))}
      </div>
      <div className="field-grid">
        <label>
          {layout === 'vertical-rtl' ? '每列最多' : '每行最多'}
          <div className="unit-input">
            <input
              aria-label="每行或列字数"
              type="number"
              min={1}
              max={30}
              step={1}
              value={columns}
              onChange={(e) => setColumns(Math.floor(Number(e.target.value)))}
            />
            <span>字</span>
          </div>
        </label>
        <label>
          字格大小
          <div className="unit-input">
            <input
              aria-label="字格大小"
              type="number"
              min={40}
              max={400}
              value={size}
              onChange={(e) => setSize(Number(e.target.value))}
            />
            <span>px</span>
          </div>
        </label>
      </div>
      <details className="advanced">
        <summary>间距与留白</summary>
        <div className="field-grid">
          <label>
            字距
            <input
              type="number"
              min={0}
              max={160}
              value={gap}
              onChange={(e) => setGap(Number(e.target.value))}
            />
          </label>
          <label>
            页边距
            <input
              type="number"
              min={0}
              max={300}
              value={margin}
              onChange={(e) => setMargin(Number(e.target.value))}
            />
          </label>
        </div>
        <label className="check-field">
          <input
            type="checkbox"
            checked={punctuation}
            onChange={(e) => setPunctuation(e.target.checked)}
          />
          保留标点
        </label>
      </details>
      <Button
        className="compose-button"
        onClick={create}
        disabled={loading || !count || count > 1000}
      >
        {loading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <ArrowRight className="h-4 w-4" />
        )}
        {loading ? '正在集字…' : '生成作品'}
      </Button>
      <p className="field-hint">自动适配纸面尺寸。重新生成会替换当前排版，可撤销。</p>
      {status && (
        <p className="feedback" role="status">
          {status}
        </p>
      )}
    </fieldset>
  )
}
