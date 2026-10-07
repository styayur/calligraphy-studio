import { Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import { getMetadata, searchGlyphs } from '../../api/client'
import { fontGlyphs } from '../../api/fonts'
import { useEditorStore } from '../../stores/editor'
import type { Glyph, MetadataResponse } from '../../types'
import { SourcePolicyControls } from './SourcePolicyControls'
import { DEFAULT_POLICY, candidateCompatible, type CandidatePolicy } from '../../lib/candidatePolicy'
import { historicalSample } from '../../api/historical'

export const GLYPH_DRAG_TYPE = 'application/x-calligraphy-glyph'
export function GlyphBrowser() {
  const [query, setQuery] = useState('山')
  const [policy, setPolicy] = useState<CandidatePolicy>(DEFAULT_POLICY)
  const [style, setStyle] = useState('')
  const [dataset, setDataset] = useState('')
  const [calligrapher, setCalligrapher] = useState('')
  const [results, setResults] = useState<Glyph[]>([])
  const [meta, setMeta] = useState<MetadataResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [limit, setLimit] = useState(40)
  const [total, setTotal] = useState(0)
  const [retry, setRetry] = useState(0)
  const addGlyph = useEditorStore((s) => s.addGlyph)
  useEffect(() => {
    getMetadata(policy.mode === 'cross-tradition' ? '*' : policy.writing_tradition)
      .then(setMeta)
      .catch(() => undefined)
  }, [policy.writing_tradition, policy.mode])
  useEffect(() => {
    let active = true
    setLoading(true)
    const timer = setTimeout(async () => {
      const term = query.trim()
      const effectiveStyle = policy.writing_tradition === 'Japanese' ? '' : style
      const [library, fonts, historical] = await Promise.allSettled([
        searchGlyphs({ q: term, style: effectiveStyle, dataset, calligrapher, limit, ...policy, writing_tradition: policy.mode === 'cross-tradition' ? undefined : policy.writing_tradition }),
        [...term].length === 1 && (!dataset || dataset === 'OFL Calligraphy Fonts' || dataset === 'Yuji Japanese Fonts')
          ? fontGlyphs(term, effectiveStyle, calligrapher, policy)
          : Promise.resolve([]),
        historicalSample().then((items) => items.filter((g) => (!term || g.character === term || g.source.work?.includes(term)) && (!dataset || g.source.dataset === dataset) && candidateCompatible(g, policy))),
      ])
      if (!active) return
      const generated = fonts.status === 'fulfilled' ? fonts.value : []
      const stored = [...(library.status === 'fulfilled' ? library.value.items : []), ...(historical.status === 'fulfilled' ? historical.value : [])]
      const items = [
        ...generated,
        ...stored.filter(
          (g) =>
            !generated.some((f) => f.character === g.character && f.source.work === g.source.work),
        ),
      ]
      setResults(Array.from(new Map(items.filter((g) => candidateCompatible(g, policy)).map((g) => [g.variant?.id || g.id,g])).values()))
      setTotal(library.status === 'fulfilled' ? library.value.total : 0)
      setMessage(
        library.status === 'rejected'
          ? generated.length
            ? '原帖字库未连接，当前显示内置字体。'
            : '字库未连接，请检查服务，或输入单个汉字查询内置字体。'
          : fonts.status === 'rejected'
            ? '内置字体加载失败，请重试。'
            : '',
      )
      setLoading(false)
    }, 200)
    return () => {
      active = false
      clearTimeout(timer)
    }
  }, [query, style, dataset, calligrapher, limit, retry, policy])
  return (
    <div className="glyph-browser panel-scroll">
      <div className="section-title">
        <h2>查找字形</h2>
        <span>{results.length} 个结果</span>
      </div>
      <div className="search-field">
        <Search size={16} />
        <input
          aria-label="搜索字形"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value)
            setLimit(40)
          }}
          placeholder="汉字、书家或作品"
        />
      </div>
      <div className="field-grid">
        <label>来源类型 / Source type<select aria-label="Source type" value={policy.provenance_type || ''} onChange={(e) => setPolicy({ ...policy, provenance_type: e.target.value || undefined })}><option value="">全部 / All</option><option value="font">字体 / Font</option><option value="original">原帖 / Historical original</option><option value="fallback">结构 / Structural fallback</option></select></label>
      </div>
      <SourcePolicyControls policy={policy} onChange={(value) => { setPolicy(value); setLimit(40) }} />
      <div className="field-grid">
        <label>
          书体
          <select aria-label="书体" value={style} onChange={(e) => setStyle(e.target.value)}>
            <option value="">全部书体</option>
            <option>楷书</option>
            <option>行书</option>
            <option>草书</option>
          </select>
        </label>
        <label>
          来源
          <select
            aria-label="字库来源"
            value={dataset}
            onChange={(e) => setDataset(e.target.value)}
          >
            <option value="">全部字库</option>
            {[...new Set([...(meta?.datasets || ['OFL Calligraphy Fonts']), 'Yuji Japanese Fonts', 'CODH Kuzushiji'])].map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
      </div>
      <details className="advanced">
        <summary>筛选书家</summary>
        <select
          aria-label="书家筛选"
          value={calligrapher}
          onChange={(e) => setCalligrapher(e.target.value)}
        >
          <option value="">全部书家</option>
          {meta?.calligraphers.map((item) => (
            <option key={item.id}>{item.name}</option>
          ))}
        </select>
      </details>
      <p className="field-hint">点击加入作品，或拖到纸面指定位置。</p>
      {loading ? (
        <p className="feedback" role="status">
          正在查字…
        </p>
      ) : (
        <>
          {message && (
            <div className="feedback" role="status">
              {message}
              <button onClick={() => setRetry(retry + 1)}>重试</button>
            </div>
          )}
          {!results.length && !message && (
            <p className="feedback">未找到字形。试试输入单个汉字，或清除筛选条件。</p>
          )}
          <div className="glyph-grid">
            {results.map((glyph) => (
              <button
                key={glyph.id}
                className="glyph-card"
                draggable
                onClick={() => addGlyph(glyph)}
                onDragStart={(e) => {
                  e.dataTransfer.effectAllowed = 'copy'
                  e.dataTransfer.setData(GLYPH_DRAG_TYPE, JSON.stringify(glyph))
                }}
                title={`${glyph.character} · ${glyph.source.work || glyph.source.dataset}`}
              >
                <img loading="lazy" src={glyph.asset.url} alt={glyph.character} draggable={false} />
                <div>
                  <strong>{glyph.character}</strong>
                  <span>{glyph.source.style}</span>
                </div>
                <small>{glyph.source.work || glyph.source.dataset}</small>
                <small className="glyph-kind">
                  {glyph.source.writing_tradition || 'Unknown tradition'} ·{' '}
                  {glyph.source.dataset === 'Demo'
                    ? '演示字形'
                    : { font: '字体', original: '原帖', fallback: '结构替补', generated: '生成' }[
                        glyph.provenance.type
                      ]}{' '}
                  · {glyph.source.license || '授权未标注'}
                </small>
              </button>
            ))}
          </div>
          {total > limit && (
            <button className="load-more" onClick={() => setLimit(limit + 40)}>
              加载更多（共 {total} 个）
            </button>
          )}
        </>
      )}
    </div>
  )
}
