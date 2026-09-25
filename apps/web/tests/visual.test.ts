import assert from 'node:assert/strict'
import {
  extractVisualProfile,
  profileCost,
  projectionTransport,
  experimentalDifference,
} from '../src/lib/visual'
import { selectSequence } from '../src/lib/beam'
import { layoutText } from '../src/lib/composition'
import { paginateRoll, zipFiles } from '../src/lib/longRoll'
const n = 64
const field = (test: (x: number, y: number) => boolean) =>
  Float32Array.from({ length: n * n }, (_, i) => (test(i % n, Math.floor(i / n)) ? 1 : 0))
const square = extractVisualProfile(field((x, y) => x >= 16 && x < 48 && y >= 16 && y < 48))
assert.deepEqual(square.bbox, [0.25, 0.25, 0.5, 0.5])
assert.equal(square.aspectRatio, 1)
assert.equal(square.inkDensity, 0.25)
assert.deepEqual(square.centroid, [0.5, 0.5])
assert.equal(square.topology.components, 1)
assert.equal(square.topology.holes, 0)
assert.equal(square.distance[2], 0.25)
assert.equal(profileCost(square, [square]), 0)
const empty = extractVisualProfile(new Float32Array(n * n))
assert.equal(empty.empty, true)
assert.ok(JSON.stringify(empty).includes('null') === false, 'all empty descriptors finite')
const ring = extractVisualProfile(
  field(
    (x, y) =>
      x >= 12 && x < 52 && y >= 12 && y < 52 && !(x >= 20 && x < 44 && y >= 20 && y < 44),
  ),
)
assert.equal(ring.topology.holes, 1)
assert.equal(ring.topology.euler, 0)
const line = extractVisualProfile(field((x, y) => y === 32 && x >= 16 && x <= 48))
assert.equal(line.skeleton.endpoints, 2)
assert.equal(line.skeleton.branches, 0)
assert.equal(line.skeleton.length, 0.5)
const pair = extractVisualProfile(
  field((x, y) => y >= 20 && y < 40 && ((x >= 8 && x < 20) || (x >= 40 && x < 52))),
)
assert.equal(pair.topology.components, 2)
assert.equal(pair.persistence.filter((b) => b[1] - b[0] > 0.9).length, 2)
assert.equal(projectionTransport([1, 0], [0, 1]), 0.5)
assert.deepEqual(experimentalDifference(ring, ring), {
  transport: 0,
  topology: 0,
  persistence: 0,
})
const opts = {
  layout: 'vertical-rtl' as const,
  columns: 5,
  size: 160,
  gap: 12,
  margin: 64,
  punctuation: false,
}
const layout = layoutText('山'.repeat(1000), opts)
assert.equal(layout.positions.length, 1000)
assert.ok(layout.width <= 8000 && layout.width * layout.height <= 20_000_000)
assert.ok(
  layout.positions.every(
    (p) => p.x > 0 && p.x < layout.width && p.y > 0 && p.y < layout.height,
  ),
)
assert.throws(() => layoutText('山'.repeat(1001), opts))
const pages = paginateRoll('山'.repeat(1001), {
  rows: 12,
  columns: 8,
  vertical: true,
  punctuation: false,
})
assert.equal(pages.length, 11)
assert.equal(pages.flatMap((p) => p.slots).length, 1001)
assert.equal(pages[0].slots[0].column, 7)
const multiline = paginateRoll('山水\n明月', {
  rows: 12,
  columns: 8,
  vertical: true,
  punctuation: false,
})
assert.equal(multiline[0].slots[2].column, 6)
const candidates = new Map([
  [
    '山',
    [
      { id: 'a', character: '山', profile: square },
      { id: 'b', character: '山', profile: square },
    ],
  ],
])
const chosen = await selectSequence([...('山'.repeat(1001) + '缺')], candidates, [square], {
  width: 8,
  variation: 0.2,
})
assert.equal(chosen.length, 1002)
assert.equal(chosen.at(-1), null)
assert.ok(chosen.includes('a') && chosen.includes('b'))
const cancel = new AbortController()
cancel.abort()
await assert.rejects(() =>
  selectSequence(['山'], candidates, [square], {
    width: 4,
    variation: 0.2,
    signal: cancel.signal,
  }),
)
const zip = zipFiles([{ name: 'test.txt', data: new TextEncoder().encode('hello') }])
assert.equal(new DataView(await zip.arrayBuffer()).getUint32(0, true), 0x04034b50)
console.log(
  'PASS: geometry, moments, EDT, skeleton, topology, H0, OT, 1000-limit, pagination, 1001-position beam, variation, cancellation, ZIP',
)
