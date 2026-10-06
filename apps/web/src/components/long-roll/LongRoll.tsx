import { useEffect, useRef, useState } from 'react'
import {
  initialCandidates,
  resolveCharacters,
  type CandidateSource,
} from '../../api/candidates'
import { getVisualProfile } from '../../lib/featureCache'
import { selectSequence, type ProfileCandidate } from '../../lib/beam'
import {
  FEATURE_VERSION,
  harmonyScore,
  profileCost,
  type VisualProfile,
} from '../../lib/visual'
import {
  paginateRoll,
  renderRollPage,
  zipFiles,
  type RollOptions,
  type RollPage,
} from '../../lib/longRoll'
import { textLines } from '../../lib/composition'
import { saveFile } from '../../lib/download'
import { useEditorStore } from '../../stores/editor'
import type { Glyph } from '../../types'
import { DEFAULT_POLICY, type CandidatePolicy } from '../../lib/candidatePolicy'
import { SourcePolicyControls } from '../glyph-browser/SourcePolicyControls'
import { assertExportRights, attributionFiles } from '../../lib/rights'

interface RollResult {
  pages: RollPage[]
  options: RollOptions
  text: string
  missing: { character: string; positions: number[] }[]
  warnings: string[]
  score: number | null
  singleVariants: number
  source: CandidateSource
  style: string
  beam: number
  variation: number
  policy: CandidatePolicy
}
function PagePreview({
  page,
  options,
  number,
}: {
  page: RollPage
  options: RollOptions
  number: number
}) {
  const canvas = useRef<HTMLCanvasElement>(null),
    [error, setError] = useState('')
  useEffect(() => {
    const controller = new AbortController()
    setError('')
    if (canvas.current)
      void renderRollPage(page, options, canvas.current, 1, controller.signal).catch((e) => {
        if (!controller.signal.aborted) setError(String(e))
      })
    return () => controller.abort()
  }, [page, options])
  return (
    <figure className="roll-page">
      <canvas ref={canvas} aria-label={`长卷第 ${number} 页`} />
      <figcaption>
        第 {number} 页 · {page.slots.length} 字{error && ` · ${error}`}
      </figcaption>
    </figure>
  )
}
export function LongRoll({ active }: { active: boolean }) {
  const [policy, setPolicy] = useState<CandidatePolicy>(() => useEditorStore.getState().project.composition?.policy || DEFAULT_POLICY)
  const [text, setText] = useState(
    () => useEditorStore.getState().project.text || '明月松间照\n清泉石上流',
  )
  const [rows, setRows] = useState(12),
    [columns, setColumns] = useState(8),
    [vertical, setVertical] = useState(true),
    [punctuation, setPunctuation] = useState(false)
  const [style, setStyle] = useState(''),
    [source, setSource] = useState<CandidateSource>('fonts'),
    [beam, setBeam] = useState(8),
    [variation, setVariation] = useState(0.2)
  const [result, setResult] = useState<RollResult | null>(null),
    [status, setStatus] = useState(''),
    [busy, setBusy] = useState(false),
    [scroll, setScroll] = useState(0),
    [viewport, setViewport] = useState(800)
  const controller = useRef<AbortController | null>(null),
    scroller = useRef<HTMLDivElement>(null)
  useEffect(() => () => controller.current?.abort(), [])
  useEffect(() => {
    if (!active || !scroller.current) return
    const observer = new ResizeObserver(([entry]) => setViewport(entry.contentRect.height))
    observer.observe(scroller.current)
    return () => observer.disconnect()
  }, [active, result])
  const count = textLines(text, punctuation).flat().length
  const generate = async () => {
    const abort = new AbortController()
    controller.current = abort
    setBusy(true)
    try {
      const options = { rows, columns, vertical, punctuation },
        pages = paginateRoll(text, options),
        characters = pages.flatMap((p) => p.slots.map((s) => s.character))
      const warnings = new Set<string>(),
        byId = new Map<string, Glyph>(),
        profileById = new Map<string, VisualProfile>()
      const candidates = await resolveCharacters(
        characters,
        async (character) => {
          const page = await initialCandidates(character, source, policy.writing_tradition === 'Japanese' ? '' : style, 8, abort.signal, { ...policy, vertical })
          if (page.warning) warnings.add(page.warning)
          const items: ProfileCandidate[] = []
          for (const g of page.items.slice(0, 8)) {
            abort.signal.throwIfAborted()
            try {
              const profile = await getVisualProfile(g)
              if (profile.empty) continue
              byId.set(g.id, g)
              profileById.set(g.id, profile)
              items.push({ id: g.id, character, profile, glyph: g })
            } catch {
              warnings.add(`「${character}」部分候选无法分析`)
            }
          }
          return items
        },
        (done, total) => setStatus(`准备字形与特征 ${done}/${total} 个不同字`),
        abort.signal,
      )
      if (!byId.size) throw new Error('未找到可用字形，请更换字库或书体。')
      // Fixed representative context, independent of beam paths, deterministic across runs.
      const context = [...candidates.values()]
        .filter((c) => c.length)
        .slice(0, 24)
        .map((c) => c[0].profile)
      const chosen = await selectSequence(characters, candidates, context, {
        width: beam,
        variation,
        policy,
        signal: abort.signal,
        progress: (done) => setStatus(`自动选字 ${done}/${characters.length}`),
      })
      const missing = new Map<string, number[]>(),
        costs: number[] = []
      for (const page of pages)
        for (const slot of page.slots) {
          const id = chosen[slot.index]
          if (!id) {
            missing.set(slot.character, [
              ...(missing.get(slot.character) || []),
              slot.index + 1,
            ])
            continue
          }
          slot.glyph = byId.get(id)!
          const neighbors = chosen
            .slice(Math.max(0, slot.index - 4), slot.index)
            .concat(chosen.slice(slot.index + 1, slot.index + 5))
            .flatMap((n) => (n ? [profileById.get(n)!] : []))
          slot.cost = neighbors.length ? profileCost(profileById.get(id)!, neighbors) : null
          if (slot.cost !== null) costs.push(slot.cost)
        }
      abort.signal.throwIfAborted()
      setResult({
        pages,
        options,
        text,
        source,
        style,
        beam,
        variation,
        policy,
        missing: [...missing].map(([character, positions]) => ({
          character,
          positions,
        })),
        warnings: [...warnings],
        score: costs.length
          ? harmonyScore(costs.reduce((a, b) => a + b, 0) / costs.length)
          : null,
        singleVariants: [...candidates.values()].filter((v) => v.length === 1).length,
      })
      setScroll(0)
      if (scroller.current) scroller.current.scrollTop = 0
      setStatus(
        `已生成 ${characters.length} 字 / ${pages.length} 页；缺字 ${[...missing.values()].reduce((s, p) => s + p.length, 0)} 处。`,
      )
    } catch (e) {
      setStatus(
        abort.signal.aborted
          ? '已取消，保留上次生成结果。'
          : e instanceof Error
            ? e.message
            : String(e),
      )
    } finally {
      setBusy(false)
    }
  }
  const exportAll = async () => {
    if (!result) return
    const abort = new AbortController()
    controller.current = abort
    setBusy(true)
    try {
      const selectedGlyphs = result.pages.flatMap((p) => p.slots.flatMap((s) => s.glyph ? [s.glyph] : []))
      assertExportRights(selectedGlyphs, { commercialOnly: result.policy.commercial_only })
      const files: { name: string; data: Uint8Array }[] = [],
        canvas = document.createElement('canvas'),
        encoder = new TextEncoder()
      for (let i = 0; i < result.pages.length; i++) {
        abort.signal.throwIfAborted()
        setStatus(`导出第 ${i + 1}/${result.pages.length} 页…`)
        await renderRollPage(result.pages[i], result.options, canvas, 1, abort.signal)
        const blob = await new Promise<Blob>((resolve, reject) =>
          canvas.toBlob(
            (b) => (b ? resolve(b) : reject(new Error('页面导出失败'))),
            'image/png',
          ),
        )
        files.push({
          name: `pages/${String(i + 1).padStart(4, '0')}.png`,
          data: new Uint8Array(await blob.arrayBuffer()),
        })
        await new Promise((r) => setTimeout(r, 0))
      }
      const glyphs = Object.fromEntries(
        result.pages.flatMap((p) =>
          p.slots.flatMap((s) => (s.glyph ? [[s.glyph.id, s.glyph]] : [])),
        ),
      )
      const manifest = {
        version: 2,
        featureVersion: FEATURE_VERSION,
        text: result.text,
        options: result.options,
        selection: {
          source: result.source,
          style: result.style,
          beam: result.beam,
          variation: result.variation,
          policy: result.policy,
        },
        score: result.score,
        missing: result.missing,
        warnings: result.warnings,
        glyphs,
        pages: result.pages.map((p) => ({
          slots: p.slots.map((s) => ({ ...s, glyph: s.glyph?.id || null })),
        })),
      }
      files.push(
        {
          name: 'manifest.json',
          data: encoder.encode(JSON.stringify(manifest, null, 2)),
        },
        {
          name: 'missing.csv',
          data: encoder.encode(
            '\ufeffcharacter,positions\n' +
              result.missing
                .map((m) => `"${m.character.replaceAll('"', '""')}","${m.positions.join(' ')}"`)
                .join('\n'),
          ),
        },
      )
      files.push(...await attributionFiles(selectedGlyphs, { commercialOnly: result.policy.commercial_only }))
      abort.signal.throwIfAborted()
      await saveFile('长卷作品.zip', zipFiles(files))
      setStatus('已导出全部页面、缺字列表和字形来源清单。')
    } catch (e) {
      setStatus(abort.signal.aborted ? '导出已取消。' : String(e))
    } finally {
      setBusy(false)
    }
  }
  const first = Math.max(0, Math.floor(scroll / 580) - 1),
    last = Math.min(result?.pages.length || 0, Math.ceil((scroll + viewport) / 580) + 1)
  const anomalies =
    result?.pages.flatMap((p, page) =>
      p.slots.filter((s) => (s.cost ?? 0) > 0.28).map((s) => ({ ...s, page })),
    ) || []
  return (
    <main className={active ? 'long-roll' : 'hidden'} aria-label="长卷模式">
      <aside className="roll-controls panel-scroll">
        <h2>长卷模式</h2>
        <p className="field-hint">
          自动选字、分栏、分页。适合 1000 字以上作品，预览按页浏览，不提供逐字拖动。
        </p>
        <fieldset disabled={busy}>
          <SourcePolicyControls policy={policy} onChange={setPolicy} />
          <label>
            长卷内容 <span>{count} / 20000 字</span>
            <textarea
              aria-label="长卷内容"
              rows={8}
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          </label>
          <button
            className="load-more"
            onClick={() => setText(useEditorStore.getState().project.text || '')}
          >
            从工作台读取文字
          </button>
          <div className="field-grid">
            <label>
              来源 / Source
              <select
                aria-label="长卷字形来源"
                value={source}
                onChange={(e) => setSource(e.target.value as CandidateSource)}
              >
                <option value="fonts">字体 / Font</option>
                <option value="original">原帖 / Original</option>
                <option value="all">全部</option>
              </select>
            </label>
            <label>
              书体
              <select
                aria-label="长卷书体"
                value={style}
                onChange={(e) => setStyle(e.target.value)}
              >
                <option value="">全部书体</option>
                <option>楷书</option>
                <option>行书</option>
                <option>草书</option>
              </select>
            </label>
          </div>
          <div className="field-grid">
            <label>
              每页行数
              <input
                aria-label="长卷每页行数"
                type="number"
                min="2"
                max="24"
                value={rows}
                onChange={(e) => setRows(Number(e.target.value))}
              />
            </label>
            <label>
              每页列数
              <input
                aria-label="长卷每页列数"
                type="number"
                min="2"
                max="24"
                value={columns}
                onChange={(e) => setColumns(Number(e.target.value))}
              />
            </label>
          </div>
          <label className="check-field">
            <input
              type="checkbox"
              checked={vertical}
              onChange={(e) => setVertical(e.target.checked)}
            />
            竖排，从右向左分栏
          </label>
          <label className="check-field">
            <input
              type="checkbox"
              checked={punctuation}
              onChange={(e) => setPunctuation(e.target.checked)}
            />
            保留标点
          </label>
          <label className="slider-field">
            重复字变化 {variation.toFixed(2)}
            <input
              aria-label="重复字变化"
              type="range"
              min="0"
              max="1"
              step=".05"
              value={variation}
              onChange={(e) => setVariation(Number(e.target.value))}
            />
          </label>
          <details className="advanced">
            <summary>自动选字设置</summary>
            <label>
              搜索宽度
              <select value={beam} onChange={(e) => setBeam(Number(e.target.value))}>
                <option value="1">快速（1）</option>
                <option value="4">均衡（4）</option>
                <option value="8">精细（8）</option>
                <option value="16">更精细（16）</option>
              </select>
            </label>
            <p className="field-hint">
              每个不同字最多分析 8 个候选。综合整段参照、相邻字形差异和最近 32
              字的重复情况；只有一个候选时保持原样。
            </p>
          </details>
          <button
            className="roll-primary"
            disabled={busy || !count || count > 20000}
            onClick={generate}
          >
            自动生成长卷
          </button>
        </fieldset>
        {busy && (
          <button className="load-more" onClick={() => controller.current?.abort()}>
            取消当前任务
          </button>
        )}
        <p className="feedback" role="status">
          {status || '输入文字后开始生成。换行会另起一栏或一行。'}
        </p>
        {result && (
          <>
            <button className="roll-primary" disabled={busy} onClick={exportAll}>
              批量导出 ZIP
            </button>
            <p className="field-hint">
              每页 PNG 800 × 1100，附来源与位置清单、缺字 CSV。请导出以保存本次长卷。
            </p>
            <h3>作品协调度 {result.score ?? '—'} / 100</h3>
            <p className="field-hint">
              局部字形相近度，非审美评分。{result.singleVariants} 个不同字只有一种候选。
            </p>
            <details open={result.missing.length > 0}>
              <summary>缺字列表（{result.missing.length} 种）</summary>
              {result.missing.length ? (
                result.missing.map((m) => (
                  <p key={m.character}>
                    {m.character} · {m.positions.length} 处 · 位置{' '}
                    {m.positions.slice(0, 20).join('、')}
                    {m.positions.length > 20 ? '…' : ''}
                  </p>
                ))
              ) : (
                <p>没有缺字。</p>
              )}
            </details>
            <details>
              <summary>异常字检测（{anomalies.length} 处）</summary>
              <p className="field-hint">与前后最多 8 字的平均差异超过 28%；仅供复核。</p>
              {anomalies.slice(0, 100).map((s) => (
                <button
                  className="anomaly-link"
                  key={s.index}
                  onClick={() => {
                    scroller.current?.scrollTo({ top: s.page * 580 })
                    setScroll(s.page * 580)
                  }}
                >
                  第 {s.index + 1} 字「{s.character}」· 第 {s.page + 1} 页 ·{' '}
                  {harmonyScore(s.cost!)} 分
                </button>
              ))}
              {anomalies.length > 100 && <p>这里只显示前 100 处，完整差异在导出清单中。</p>}
            </details>
            {result.warnings.map((w) => (
              <p className="field-hint" key={w}>
                {w}
              </p>
            ))}
          </>
        )}
      </aside>
      <section
        className="roll-preview panel-scroll"
        ref={scroller}
        onScroll={(e) => setScroll(e.currentTarget.scrollTop)}
        aria-label="长卷分页预览"
      >
        {result ? (
          <div style={{ height: result.pages.length * 580, position: 'relative' }}>
            {result.pages.slice(first, last).map((page, i) => (
              <div
                key={first + i}
                style={{
                  position: 'absolute',
                  top: (first + i) * 580,
                  height: 580,
                  width: '100%',
                }}
              >
                <PagePreview page={page} options={result.options} number={first + i + 1} />
              </div>
            ))}
          </div>
        ) : (
          <div className="roll-empty">
            <span>卷</span>
            <h2>让千字成篇</h2>
            <p>分页预览 · 自动选字 · 重复字变化</p>
          </div>
        )}
      </section>
    </main>
  )
}
