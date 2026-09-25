/** Versioned, deterministic descriptors on a 64×64, alpha-composited ink field.
 * Coordinates are normalized to the source image, not a tight crop. */
export const FEATURE_VERSION = 'visual-1'
export const RESOLUTION = 64
export interface VisualProfile {
  version: string
  empty: boolean
  bbox: number[]
  aspectRatio: number
  inkDensity: number
  centroid: number[]
  moments: number[]
  hu: number[]
  horizontal: number[]
  vertical: number[]
  quadrants: number[]
  whitespace: number[]
  distance: number[]
  skeleton: { length: number; branches: number; endpoints: number }
  orientation: number[]
  topology: { components: number; holes: number; euler: number }
  persistence: number[][]
}
const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / Math.max(1, xs.length)
const normalize = (xs: number[]) => {
  const sum = xs.reduce((a, b) => a + b, 0)
  return xs.map((x) => x / (sum || 1))
}

function components(mask: Uint8Array, n: number, foreground: boolean, eight = false) {
  const seen = new Uint8Array(mask.length)
  let count = 0,
    enclosed = 0
  for (let i = 0; i < mask.length; i++) {
    if (seen[i] || Boolean(mask[i]) !== foreground) continue
    count++
    const stack = [i]
    seen[i] = 1
    let border = false
    while (stack.length) {
      const p = stack.pop()!,
        x = p % n,
        y = Math.floor(p / n)
      if (!x || !y || x === n - 1 || y === n - 1) border = true
      for (let dy = -1; dy <= 1; dy++)
        for (let dx = -1; dx <= 1; dx++) {
          if ((!dx && !dy) || (!eight && Math.abs(dx) + Math.abs(dy) !== 1)) continue
          const xx = x + dx,
            yy = y + dy,
            q = yy * n + xx
          if (
            xx < 0 ||
            yy < 0 ||
            xx >= n ||
            yy >= n ||
            seen[q] ||
            Boolean(mask[q]) !== foreground
          )
            continue
          seen[q] = 1
          stack.push(q)
        }
    }
    if (!border) enclosed++
  }
  return { count, enclosed }
}

/** H0 lower-star persistence of 1−ink, 8-connected cubical pixel adjacency.
 * Elder rule; omit zero-duration bars; cap the one essential bar at filtration 1. */
export function persistenceH0(ink: Float32Array, n: number): number[][] {
  const order = Array.from(ink.keys()).sort((a, b) => ink[b] - ink[a] || a - b)
  const parent = new Int32Array(ink.length).fill(-1),
    birth = new Float64Array(ink.length)
  const root = (p: number): number => {
    while (parent[p] !== p) {
      parent[p] = parent[parent[p]]
      p = parent[p]
    }
    return p
  }
  const bars: number[][] = []
  for (const p of order) {
    const level = 1 - ink[p]
    parent[p] = p
    birth[p] = level
    const x = p % n,
      y = Math.floor(p / n)
    for (let dy = -1; dy <= 1; dy++)
      for (let dx = -1; dx <= 1; dx++) {
        const xx = x + dx,
          yy = y + dy,
          q = yy * n + xx
        if (xx < 0 || yy < 0 || xx >= n || yy >= n || parent[q] < 0) continue
        let a = root(p),
          b = root(q)
        if (a === b) continue
        if (birth[a] > birth[b] || (birth[a] === birth[b] && a > b)) [a, b] = [b, a]
        if (level - birth[b] > 1e-6) bars.push([birth[b], level])
        parent[b] = a
      }
  }
  if (ink.length) bars.push([birth[root(0)], 1])
  return bars.sort((a, b) => b[1] - b[0] - (a[1] - a[0]))
}

export function extractVisualProfile(ink: Float32Array, n = RESOLUTION): VisualProfile {
  if (ink.length !== n * n || n < 3) throw new Error('Invalid ink field')
  const mask = Uint8Array.from(ink, (x) => (x >= 0.25 ? 1 : 0))
  let left = n,
    right = -1,
    top = n,
    bottom = -1,
    mass = 0,
    mx = 0,
    my = 0,
    count = 0
  const horizontal = Array(n).fill(0),
    vertical = Array(n).fill(0),
    quadrants = [0, 0, 0, 0]
  for (let y = 0; y < n; y++)
    for (let x = 0; x < n; x++) {
      const i = y * n + x,
        w = ink[i]
      mass += w
      mx += (w * (x + 0.5)) / n
      my += (w * (y + 0.5)) / n
      horizontal[y] += w
      vertical[x] += w
      quadrants[(y >= n / 2 ? 2 : 0) + (x >= n / 2 ? 1 : 0)] += w
      if (mask[i]) {
        count++
        left = Math.min(left, x)
        right = Math.max(right, x)
        top = Math.min(top, y)
        bottom = Math.max(bottom, y)
      }
    }
  const empty = !count,
    cx = mx / (mass || 1),
    cy = my / (mass || 1)
  const moment = (p: number, q: number) => {
    let v = 0
    for (let y = 0; y < n; y++)
      for (let x = 0; x < n; x++)
        v += ink[y * n + x] * ((x + 0.5) / n - cx) ** p * ((y + 0.5) / n - cy) ** q
    return v / (mass || 1)
  }
  const moments = [
    moment(2, 0),
    moment(0, 2),
    moment(1, 1),
    moment(3, 0),
    moment(0, 3),
    moment(2, 1),
    moment(1, 2),
  ]
  // Normalized central moments eta_pq = mu_pq / mu_00^(1+(p+q)/2).
  const density = mass / (n * n)
  const [a, b, c, d, e, f, g] = moments.map(
    (v, i) => v / Math.max(1e-12, density ** (i < 3 ? 1 : 1.5)),
  )
  const h = d + g,
    j = f + e,
    k = d - 3 * g,
    l = 3 * f - e
  const hu = [
    a + b,
    (a - b) ** 2 + 4 * c * c,
    k * k + l * l,
    h * h + j * j,
    k * h * (h * h - 3 * j * j) + l * j * (3 * h * h - j * j),
    (a - b) * (h * h - j * j) + 4 * c * h * j,
    l * h * (h * h - 3 * j * j) - k * j * (3 * h * h - j * j),
  ]
  // Exact separable squared Euclidean transform; exterior is background.
  const rowDistance = new Float64Array(n * n)
  for (let y = 0; y < n; y++)
    for (let x = 0; x < n; x++) {
      let best = Math.min((x + 1) ** 2, (n - x) ** 2)
      for (let xx = 0; xx < n; xx++) if (!mask[y * n + xx]) best = Math.min(best, (x - xx) ** 2)
      rowDistance[y * n + x] = best
    }
  const distances: number[] = []
  for (let y = 0; y < n; y++)
    for (let x = 0; x < n; x++)
      if (mask[y * n + x]) {
        let best = Math.min((y + 1) ** 2, (n - y) ** 2)
        for (let yy = 0; yy < n; yy++)
          best = Math.min(best, rowDistance[yy * n + x] + (y - yy) ** 2)
        distances.push(Math.sqrt(best) / n)
      }
  const avg = mean(distances)
  // Zhang–Suen thinning on a zero-padded grid, preserving boundary ink.
  const stride = n + 2,
    sk = new Uint8Array(stride * stride)
  for (let y = 0; y < n; y++)
    for (let x = 0; x < n; x++) sk[(y + 1) * stride + x + 1] = mask[y * n + x]
  const neighbors = (i: number) => [
    sk[i - stride],
    sk[i - stride + 1],
    sk[i + 1],
    sk[i + stride + 1],
    sk[i + stride],
    sk[i + stride - 1],
    sk[i - 1],
    sk[i - stride - 1],
  ]
  let changed = true
  while (changed) {
    changed = false
    for (let step = 0; step < 2; step++) {
      const remove: number[] = []
      for (let y = 1; y <= n; y++)
        for (let x = 1; x <= n; x++) {
          const i = y * stride + x
          if (!sk[i]) continue
          const p = neighbors(i),
            sum = p.reduce((s, v) => s + v, 0)
          const transitions = p.reduce((s, v, k) => s + (!v && p[(k + 1) % 8] ? 1 : 0), 0)
          if (sum < 2 || sum > 6 || transitions !== 1) continue
          if (
            step === 0
              ? p[0] * p[2] * p[4] || p[2] * p[4] * p[6]
              : p[0] * p[2] * p[6] || p[0] * p[4] * p[6]
          )
            continue
          remove.push(i)
        }
      for (const i of remove) sk[i] = 0
      changed ||= remove.length > 0
    }
  }
  let length = 0,
    endpoints = 0
  const junctions = new Uint8Array(n * n)
  for (let y = 1; y <= n; y++)
    for (let x = 1; x <= n; x++) {
      const i = y * stride + x
      if (!sk[i]) continue
      const p = neighbors(i),
        degree = p.reduce((s, v) => s + v, 0)
      if (degree === 1) endpoints++
      const transitions = p.reduce((s, v, k) => s + (!v && p[(k + 1) % 8] ? 1 : 0), 0)
      if (transitions >= 3) junctions[(y - 1) * n + x - 1] = 1
      length += p[2] + p[4] + Math.SQRT2 * (p[3] + p[5])
    }
  const orientation = Array(12).fill(0)
  for (let y = 1; y < n - 1; y++)
    for (let x = 1; x < n - 1; x++) {
      const i = y * n + x,
        gx = ink[i + 1] - ink[i - 1],
        gy = ink[i + n] - ink[i - n]
      const angle = (Math.atan2(gy, gx) + Math.PI * 1.5) % Math.PI
      orientation[Math.min(11, Math.floor((angle / Math.PI) * 12))] += Math.hypot(gx, gy)
    }
  const cc = components(mask, n, true, true).count,
    holes = components(mask, n, false).enclosed
  const bw = empty ? 0 : right - left + 1,
    bh = empty ? 0 : bottom - top + 1
  return {
    version: FEATURE_VERSION,
    empty,
    bbox: empty ? [0, 0, 0, 0] : [left / n, top / n, bw / n, bh / n],
    aspectRatio: bw / (bh || 1),
    inkDensity: density,
    centroid: [cx, cy],
    moments,
    hu,
    horizontal: normalize(horizontal),
    vertical: normalize(vertical),
    quadrants: quadrants.map((v) => v / ((n * n) / 4)),
    whitespace: empty
      ? [1, 1, 1, 1, 1]
      : [left / n, top / n, (n - right - 1) / n, (n - bottom - 1) / n, 1 - count / (bw * bh)],
    distance: [avg, mean(distances.map((v) => (v - avg) ** 2)), Math.max(0, ...distances)],
    skeleton: {
      length: length / n,
      branches: components(junctions, n, true, true).count,
      endpoints,
    },
    orientation: normalize(orientation),
    topology: { components: cc, holes, euler: cc - holes },
    persistence: persistenceH0(ink, n),
  }
}

export const descriptorGroups = [
  ['比例', (p: VisualProfile) => [Math.log(Math.max(0.01, p.aspectRatio))], 1.5],
  ['墨量', (p: VisualProfile) => [p.inkDensity], 0.3],
  ['重心', (p: VisualProfile) => p.centroid, 0.3],
  ['图像矩', (p: VisualProfile) => p.moments, 0.06],
  ['横向投影', (p: VisualProfile) => p.horizontal, 0.04],
  ['纵向投影', (p: VisualProfile) => p.vertical, 0.04],
  ['四象限墨量', (p: VisualProfile) => p.quadrants, 0.4],
  ['留白', (p: VisualProfile) => p.whitespace, 0.5],
  [
    '笔画距离',
    (p: VisualProfile) => [p.distance[0], Math.sqrt(p.distance[1]), p.distance[2]],
    0.08,
  ],
  [
    '骨架',
    (p: VisualProfile) => [
      p.skeleton.length / 12,
      p.skeleton.branches / 40,
      p.skeleton.endpoints / 40,
    ],
    1,
  ],
  ['方向', (p: VisualProfile) => p.orientation, 0.2],
] as const
export interface Difference {
  label: string
  current: number
  target: number
  cost: number
}
export function differences(p: VisualProfile, context: VisualProfile[]): Difference[] {
  const valid = context.filter((v) => !v.empty)
  if (!valid.length) return []
  return descriptorGroups.map(([label, get, scale]) => {
    const v = get(p),
      refs = valid.map(get),
      target = v.map((_, i) => mean(refs.map((r) => r[i])))
    return {
      label,
      current: mean(v),
      target: mean(target),
      cost: Math.min(1, mean(v.map((x, i) => Math.abs(x - target[i]))) / scale),
    }
  })
}
export function profileCost(p: VisualProfile, context: VisualProfile[]) {
  if (p.empty) return 1
  return mean(differences(p, context).map((d) => d.cost))
}
export const harmonyScore = (cost: number) =>
  Math.round(100 * (1 - Math.min(1, Math.max(0, cost))))
/** Exact 1D Wasserstein-1 on normalized projections. This is NOT 2D OT. */
export function projectionTransport(a: number[], b: number[]) {
  let cumulative = 0,
    cost = 0
  for (let i = 0; i < a.length; i++) {
    cumulative += a[i] - b[i]
    cost += Math.abs(cumulative)
  }
  return cost / a.length
}
export function experimentalDifference(a: VisualProfile, b: VisualProfile) {
  const lifetimes = (p: VisualProfile) =>
    p.persistence.map(([birth, death]) => death - birth).sort((x, y) => y - x)
  const x = lifetimes(a),
    y = lifetimes(b),
    count = Math.max(x.length, y.length)
  return {
    transport:
      (projectionTransport(a.horizontal, b.horizontal) +
        projectionTransport(a.vertical, b.vertical)) /
      2,
    topology:
      Math.abs(a.topology.components - b.topology.components) +
      Math.abs(a.topology.holes - b.topology.holes),
    persistence:
      Array.from({ length: count }, (_, i) => Math.abs((x[i] || 0) - (y[i] || 0))).reduce(
        (s, v) => s + v,
        0,
      ) / Math.max(1, count),
  }
}
