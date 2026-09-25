import { useEffect, useMemo, useState } from 'react'
import { candidatePage } from '../../api/candidates'
import { useEditorStore } from '../../stores/editor'
import { harmonyScore, profileCost } from '../../lib/visual'
import { DifferencePanel, nearestNeighbors, ProfileReadout, useProfiles } from './VisualProfile'
import type { GlyphInstance, Glyph } from '../../types'

export function SimilarGlyphs({ glyph }: { glyph: GlyphInstance }) {
  const [items, setItems] = useState<Glyph[]>([]),
    [status, setStatus] = useState(''),
    [offset, setOffset] = useState(0)
  const [more, setMore] = useState(false),
    [loading, setLoading] = useState(false),
    [sort, setSort] = useState(false)
  const [preview, setPreview] = useState<Glyph | null>(null)
  const glyphs = useEditorStore((s) => s.project.glyphs),
    replace = useEditorStore((s) => s.replaceGlyph)
  const neighbors = useMemo(() => nearestNeighbors(glyph, glyphs), [glyph, glyphs])
  useEffect(() => {
    setItems([])
    setOffset(0)
    setPreview(null)
  }, [glyph.character])
  useEffect(() => {
    let active = true
    setLoading(true)
    candidatePage(glyph.character, 'all', '', offset)
      .then((page) => {
        if (!active) return
        setItems((previous) =>
          offset
            ? Array.from(new Map([...previous, ...page.items].map((g) => [g.id, g])).values())
            : page.items,
        )
        setMore(page.hasMore)
        setStatus(page.warning || (!page.items.length ? '暂无其他字形' : ''))
      })
      .catch((e) => {
        if (active) setStatus(String(e))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [glyph.character, offset])
  const { profiles, pending, failed } = useProfiles([glyph, ...neighbors, ...items])
  const context = neighbors.flatMap((g) => {
    const p = profiles.get(g.id)
    return p ? [p] : []
  })
  const ranked = sort
    ? [...items].sort((a, b) => {
        const pa = profiles.get(a.id),
          pb = profiles.get(b.id)
        return (
          (pa ? profileCost(pa, context) : Infinity) -
          (pb ? profileCost(pb, context) : Infinity)
        )
      })
    : items
  const shown = preview || glyph,
    profile = profiles.get(shown.id)
  const scene = [glyph, ...neighbors]
  const left = Math.min(
    ...scene.map((g) => g.transform.x - (g.asset.width * Math.abs(g.transform.scaleX)) / 2),
  )
  const top = Math.min(
    ...scene.map((g) => g.transform.y - (g.asset.height * Math.abs(g.transform.scaleY)) / 2),
  )
  const right = Math.max(
    ...scene.map((g) => g.transform.x + (g.asset.width * Math.abs(g.transform.scaleX)) / 2),
  )
  const bottom = Math.max(
    ...scene.map((g) => g.transform.y + (g.asset.height * Math.abs(g.transform.scaleY)) / 2),
  )
  return (
    <section className="variants-section">
      <div className="section-title">
        <h3>换个字形</h3>
        <span>保留位置与大小</span>
      </div>
      <label className="check-field">
        <input type="checkbox" checked={sort} onChange={(e) => setSort(e.target.checked)} />
        按协调度排序
      </label>
      {(status || loading || pending || failed > 0) && (
        <p className="field-hint" role="status">
          {loading ? '正在查找同字字形…' : status}
          {pending ? ' · 计算特征中…' : ''}
          {failed ? ` · ${failed} 字特征不可用` : ''}
        </p>
      )}
      <div className="variant-grid">
        {ranked.map((item) => (
          <button
            key={item.id}
            onMouseEnter={() => setPreview(item)}
            onFocus={() => setPreview(item)}
            onClick={() => replace(glyph.id, item)}
            aria-label={`替换为${item.source.work || item.source.style || item.character}`}
            aria-pressed={item.id === glyph.glyph_id}
            title={`${item.source.work || item.source.dataset} · ${item.source.license || '授权未标注'}`}
          >
            <img loading="lazy" src={item.asset.url} alt={item.character} />
            <span>
              {item.provenance.type === 'original' ? '原帖' : item.source.style || '结构替补'}
            </span>
            {sort && context.length > 0 && profiles.has(item.id) && (
              <small>{harmonyScore(profileCost(profiles.get(item.id)!, context))} / 100</small>
            )}
          </button>
        ))}
      </div>
      {more && (
        <button
          className="load-more"
          disabled={loading}
          onClick={() => setOffset((v) => v + 12)}
        >
          加载下一组候选
        </button>
      )}
      <div className="context-preview">
        <h4>置入作品预览</h4>
        <p className="field-hint">
          悬停或聚焦候选预览，点击替换。当前预览：
          {shown.source.work || shown.character}
        </p>
        <svg
          viewBox={`${left - 12} ${top - 12} ${Math.max(1, right - left) + 24} ${Math.max(1, bottom - top) + 24}`}
          aria-label="上下文预览"
        >
          {scene.map((g) => {
            const image = g.id === glyph.id ? shown : g,
              w = g.asset.width * Math.abs(g.transform.scaleX),
              h = g.asset.height * Math.abs(g.transform.scaleY)
            return (
              <g
                key={g.id}
                transform={`translate(${g.transform.x} ${g.transform.y}) rotate(${g.transform.rotation}) matrix(1 ${g.transform.skewY} ${g.transform.skewX} 1 0 0) scale(${Math.sign(g.transform.scaleX)} ${Math.sign(g.transform.scaleY)})`}
              >
                <image
                  href={image.asset.url}
                  x={-w / 2}
                  y={-h / 2}
                  width={w}
                  height={h}
                  opacity={g.appearance.opacity}
                  preserveAspectRatio="none"
                  style={{
                    mixBlendMode:
                      g.appearance.blendMode === 'source-over'
                        ? 'normal'
                        : (g.appearance.blendMode as 'multiply'),
                  }}
                />
                {g.id === glyph.id && (
                  <rect
                    x={-w / 2}
                    y={-h / 2}
                    width={w}
                    height={h}
                    fill="none"
                    stroke="#547d68"
                    strokeWidth="2"
                  />
                )}
              </g>
            )
          })}
        </svg>
        <button onClick={() => setPreview(null)}>查看当前字</button>
      </div>
      <h3 className="profile-title">Visual Profile</h3>
      <p className="field-hint">64 × 64 原始字形，坐标与长度归一化；不含手动变形。</p>
      {profile ? (
        <>
          <ProfileReadout glyph={shown} profile={profile} />
          <DifferencePanel
            profile={profile}
            context={context}
            reference={profiles.get(glyph.id)}
          />
        </>
      ) : (
        <p className="field-hint">
          {pending ? '正在计算字形特征…' : '特征读取失败，请重新选字。'}
        </p>
      )}
    </section>
  )
}
