import { useEffect, useMemo, useRef, useState } from 'react'
import { assetToken, getVisualProfile } from '../../lib/featureCache'
import {
  differences,
  experimentalDifference,
  harmonyScore,
  profileCost,
  type VisualProfile as Profile,
} from '../../lib/visual'
import type { Glyph, GlyphInstance } from '../../types'
import { useEditorStore } from '../../stores/editor'

export function nearestNeighbors(glyph: GlyphInstance, glyphs: GlyphInstance[], limit = 8) {
  return glyphs
    .filter((g) => g.id !== glyph.id)
    .map((g) => ({
      g,
      d: (g.transform.x - glyph.transform.x) ** 2 + (g.transform.y - glyph.transform.y) ** 2,
    }))
    .sort((a, b) => a.d - b.d)
    .slice(0, limit)
    .map((v) => v.g)
}
export function useProfiles(glyphs: Glyph[]) {
  const [state, setState] = useState<{
    profiles: Map<string, Profile>
    pending: boolean
    failed: number
  }>({ profiles: new Map(), pending: false, failed: 0 })
  const key = JSON.stringify(glyphs.map((g) => [g.id, assetToken(g)]))
  useEffect(() => {
    let active = true
    setState({ profiles: new Map(), pending: true, failed: 0 })
    const run = async () => {
      const profiles = new Map<string, Profile>()
      let failed = 0
      for (let start = 0; start < glyphs.length && active; start += 12) {
        await Promise.all(
          glyphs.slice(start, start + 12).map(async (g) => {
            try {
              profiles.set(g.id, await getVisualProfile(g))
            } catch {
              failed++
            }
          }),
        )
      }
      if (active) setState({ profiles, pending: false, failed })
    }
    void run()
    return () => {
      active = false
    }
  }, [key])
  return state
}
function Distribution({ values, label }: { values: number[]; label: string }) {
  const max = Math.max(0.001, ...values)
  return (
    <div className="profile-distribution">
      <span>{label}</span>
      <svg
        viewBox={`0 0 ${values.length * 4} 30`}
        role="img"
        aria-label={label}
        preserveAspectRatio="none"
      >
        {values.map((v, i) => (
          <rect
            key={i}
            x={i * 4}
            y={30 - (v / max) * 28}
            width="3"
            height={(v / max) * 28}
            fill="currentColor"
          />
        ))}
      </svg>
    </div>
  )
}
export function ProfileReadout({ glyph, profile }: { glyph: Glyph; profile: Profile }) {
  const [x, y, w, h] = profile.bbox
  return (
    <div className="visual-readout">
      <div className="profile-overlay">
        <img src={glyph.asset.url} alt={`${glyph.character} 特征定位`} />
        <svg viewBox="0 0 100 100" aria-label="包围盒与重心">
          <rect x={x * 100} y={y * 100} width={w * 100} height={h * 100} />
          <path
            d={`M ${profile.centroid[0] * 100 - 4} ${profile.centroid[1] * 100} h 8 M ${profile.centroid[0] * 100} ${profile.centroid[1] * 100 - 4} v 8`}
          />
        </svg>
      </div>
      <dl className="profile-values">
        <dt>宽高比</dt>
        <dd>{profile.aspectRatio.toFixed(2)}</dd>
        <dt>墨量</dt>
        <dd>{(profile.inkDensity * 100).toFixed(1)}%</dd>
        <dt>重心 x / y</dt>
        <dd>{profile.centroid.map((v) => v.toFixed(2)).join(' / ')}</dd>
        <dt>包围盒 x/y/w/h</dt>
        <dd>{profile.bbox.map((v) => v.toFixed(2)).join(' / ')}</dd>
        <dt>骨架长度 / 端点 / 分支</dt>
        <dd>
          {profile.skeleton.length.toFixed(2)} / {profile.skeleton.endpoints} /{' '}
          {profile.skeleton.branches}
        </dd>
        <dt>距离均值 / 方差 / 最大</dt>
        <dd>{profile.distance.map((v) => v.toFixed(4)).join(' / ')}</dd>
        <dt>四象限墨量 ↖ ↗ ↙ ↘</dt>
        <dd>{profile.quadrants.map((v) => (v * 100).toFixed(0) + '%').join(' / ')}</dd>
        <dt>留白 左 / 上 / 右 / 下 / 内</dt>
        <dd>{profile.whitespace.map((v) => (v * 100).toFixed(0) + '%').join(' / ')}</dd>
      </dl>
      <Distribution values={profile.horizontal} label="水平投影（逐行）" />
      <Distribution values={profile.vertical} label="垂直投影（逐列）" />
      <Distribution values={profile.orientation} label="笔画方向 0–180°" />
      <details>
        <summary>图像矩与实验拓扑</summary>
        <p>
          中心矩 μ20, μ02, μ11, μ30, μ03, μ21, μ12：
          {profile.moments.map((v) => v.toExponential(2)).join(' / ')}
        </p>
        <p>Hu 1–7：{profile.hu.map((v) => v.toExponential(2)).join(' / ')}</p>
        <p>
          连通分量 {profile.topology.components} · 孔洞 {profile.topology.holes} · Euler{' '}
          {profile.topology.euler}
        </p>
        <p>H0 持久条码（最长 12 条；本质类截断于 1）</p>
        <svg viewBox="0 0 100 65" className="barcode" aria-label="H0 持久条码">
          {profile.persistence.slice(0, 12).map(([b, d], i) => (
            <line
              key={i}
              x1={b * 100}
              x2={d * 100}
              y1={i * 5 + 3}
              y2={i * 5 + 3}
              stroke="currentColor"
              strokeWidth="2"
            />
          ))}
        </svg>
      </details>
    </div>
  )
}
export function DifferencePanel({
  profile,
  context,
  reference,
}: {
  profile: Profile
  context: Profile[]
  reference?: Profile
}) {
  const rows = differences(profile, context).sort((a, b) => b.cost - a.cost)
  const experimental = reference ? experimentalDifference(profile, reference) : null
  return (
    <div className="difference-panel">
      <h4>可解释差异</h4>
      {rows.length ? (
        <>
          <p>
            上下文协调度 <strong>{harmonyScore(profileCost(profile, context))}</strong> / 100
          </p>
          <p className="field-hint">
            条越长，差异越大。{context.length} 个附近字形等权参照；相近度不代表审美优劣。
          </p>
          <details className="context-profile">
            <summary>Context Profile · 上下文参照</summary>
            <dl className="profile-values">
              <dt>参照宽高比 / 当前候选</dt>
              <dd>
                {(context.reduce((s, p) => s + p.aspectRatio, 0) / context.length).toFixed(2)} /{' '}
                {profile.aspectRatio.toFixed(2)}
              </dd>
              <dt>参照墨量 / 当前候选</dt>
              <dd>
                {(
                  (context.reduce((s, p) => s + p.inkDensity, 0) / context.length) *
                  100
                ).toFixed(1)}
                % / {(profile.inkDensity * 100).toFixed(1)}%
              </dd>
              <dt>参照重心 x / y</dt>
              <dd>
                {[0, 1]
                  .map((i) =>
                    (context.reduce((s, p) => s + p.centroid[i], 0) / context.length).toFixed(
                      2,
                    ),
                  )
                  .join(' / ')}
              </dd>
            </dl>
          </details>
          {rows.map((row) => (
            <div className="difference-row" key={row.label}>
              <span>{row.label}</span>
              <meter min="0" max="1" value={row.cost} />
              <span>{Math.round(row.cost * 100)}%</span>
            </div>
          ))}
        </>
      ) : (
        <p className="field-hint">加入其他字形后显示上下文比较。</p>
      )}
      {experimental && (
        <details>
          <summary>实验：OT / topology / persistent homology</summary>
          <p>
            与当前原字比较：投影 W₁ {experimental.transport.toFixed(4)}
            ；连通/孔洞差 {experimental.topology}；H0 寿命向量差{' '}
            {experimental.persistence.toFixed(4)}。
          </p>
          <p className="field-hint">
            仅横纵投影的 1D Optimal Transport；H0 为灰度过滤的连通分量持久性。未计算 2D OT、H1
            持久性或图间 Wasserstein；实验指标不参与默认排序。
          </p>
        </details>
      )}
    </div>
  )
}
export function WorkHarmony() {
  const glyphs = useEditorStore((s) => s.project.glyphs)
  const [open, setOpen] = useState(false)
  const { profiles, pending, failed } = useProfiles(open ? glyphs : [])
  const geometry = JSON.stringify(glyphs.map((g) => [g.id, g.transform.x, g.transform.y]))
  const neighborIds = useMemo(
    () =>
      new Map(
        open ? glyphs.map((g) => [g.id, nearestNeighbors(g, glyphs).map((n) => n.id)]) : [],
      ),
    [geometry, open],
  )
  const localCache = useRef(
    new Map<string, { profile: Profile; context: Profile[]; cost: number }>(),
  )
  const summary = useMemo(() => {
    const currentIds = new Set(glyphs.map((g) => g.id))
    for (const id of localCache.current.keys())
      if (!currentIds.has(id)) localCache.current.delete(id)
    const costs = glyphs.flatMap((g) => {
      const p = profiles.get(g.id)
      if (!p) return []
      const context = (neighborIds.get(g.id) || []).flatMap((id) => {
        const v = profiles.get(id)
        return v ? [v] : []
      })
      if (!context.length) return []
      const cached = localCache.current.get(g.id)
      const cost =
        cached?.profile === p &&
        cached.context.length === context.length &&
        context.every((v, i) => v === cached.context[i])
          ? cached.cost
          : profileCost(p, context)
      localCache.current.set(g.id, { profile: p, context, cost })
      return [{ g, cost }]
    })
    return {
      score: costs.length
        ? harmonyScore(costs.reduce((s, c) => s + c.cost, 0) / costs.length)
        : null,
      outliers: costs
        .filter((c) => c.cost > 0.28)
        .sort((a, b) => b.cost - a.cost)
        .slice(0, 12),
    }
  }, [glyphs, profiles, neighborIds])
  return (
    <section className="work-harmony">
      <button onClick={() => setOpen(!open)} aria-expanded={open}>
        作品协调度{' '}
        {open && !pending && summary.score !== null
          ? `${summary.score} / 100`
          : open
            ? '收起'
            : '分析'}
      </button>
      {open && (
        <div>
          <p className="field-hint">
            {pending
              ? '按需计算中…'
              : `已分析 ${profiles.size}/${glyphs.length} 字；${failed} 字读取失败。`}{' '}
            基于原始字形与最近 8 字，未计入手动变形和墨色。
          </p>
          {summary.outliers.length > 0 && (
            <p>
              差异较大的字：
              {summary.outliers.map(({ g }) => (
                <button key={g.id} onClick={() => useEditorStore.getState().selectGlyph(g.id)}>
                  {g.character}
                </button>
              ))}
            </p>
          )}
        </div>
      )}
    </section>
  )
}
