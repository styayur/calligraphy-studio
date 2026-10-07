import assert from 'node:assert/strict'
import { readFileSync, writeFileSync } from 'node:fs'
import { validateProject } from '../src/lib/project'
import { attributionManifest } from '../src/lib/rights'
import { candidateCompatible } from '../src/lib/candidatePolicy'
import { zipFiles } from '../src/lib/longRoll'
import { codepoints } from '../src/lib/identity'
import type { Glyph } from '../src/types'

const names = ['legacy-v1-chinese','v2-chinese','v2-japanese-modern','v2-hentaigana','v2-codh-historical','v2-mixed-cjk']
const exports: Record<string, unknown> = {}
let assertions = 0
for (const name of names) {
  const fixture = JSON.parse(readFileSync(`../../tests/fixtures/projects/${name}.json`, 'utf8'))
  const loaded = validateProject(fixture)
  const saved = JSON.stringify(loaded)
  const reloaded = validateProject(JSON.parse(saved))
  assert.deepEqual(reloaded, loaded); assertions++
  assert.equal(reloaded.version, 2); assertions++
  for (let i=0;i<fixture.glyphs.length;i++) {
    const before = fixture.glyphs[i], after = reloaded.glyphs[i]
    // Every original metadata field must survive. Missing legacy fields may be enriched.
    for (const field of ['character','variant','provenance','metadata','asset','transform','appearance','glyph_id']) {
      if (field in before) assert.deepEqual(after[field as keyof typeof after], before[field]); assertions++
    }
    if (before.identity) assert.deepEqual(after.identity, before.identity)
    assert.deepEqual(after.identity?.codepoints, codepoints(before.character)); assertions++
    for (const [key,value] of Object.entries(before.source)) {
      if (key==='rights') for (const [right,permission] of Object.entries(value as object)) assert.equal(after.source.rights?.[right],permission)
      else assert.deepEqual(after.source[key as keyof typeof after.source],value)
      assertions++
    }
  }
  const exported = attributionManifest(reloaded.glyphs)
  const parsed = JSON.parse(JSON.stringify(exported))
  assert.equal(parsed.glyphs.length, reloaded.glyphs.length); assertions++
  for (const glyph of reloaded.glyphs) {
    const record = parsed.glyphs.find((g: Glyph) => g.id===glyph.id)
    for (const field of ['character','identity','variant','provenance','source','metadata']) {
      assert.deepEqual(record[field], glyph[field as keyof typeof glyph] ?? {}); assertions++
    }
    assert.equal(record.asset_checksum, glyph.asset.checksum); assertions++
  }
  // Parse the actual stored ZIP local header, not a mirror of the export function.
  const json = new TextEncoder().encode(JSON.stringify(exported))
  const bytes = new Uint8Array(await zipFiles([{name:'attribution.json', data:json}]).arrayBuffer())
  const header = new DataView(bytes.buffer), offset = 30+header.getUint16(26,true)+header.getUint16(28,true)
  assert.equal(header.getUint32(0,true),0x04034b50); assertions++
  assert.deepEqual(JSON.parse(new TextDecoder().decode(bytes.slice(offset,offset+header.getUint32(18,true)))),parsed); assertions++
  exports[name]=parsed
  if (name==='v2-hentaigana') {
    assert.equal(new Set(reloaded.glyphs.map(g=>g.character)).size,1)
    assert.equal(new Set(reloaded.glyphs.map(g=>g.variant?.id)).size,2)
    assert.ok(reloaded.glyphs.every(g=>g.variant?.type==='hentaigana' && g.provenance.type==='font'))
    assert.deepEqual(reloaded.glyphs.map(g=>g.source.work),['Yuji Akari','Yuji Akebono'])
    assertions+=4
  }
  if (name==='v2-japanese-modern') {
    assert.equal(reloaded.glyphs.find(g=>g.character==='国')?.variant?.type,'shinjitai')
    assert.equal(reloaded.glyphs.find(g=>g.character==='國')?.variant?.type,'kyujitai')
    assert.equal(reloaded.glyphs.find(g=>g.character==='か\u3099')?.identity?.text,'か\u3099'); assertions+=3
  }
  if (name==='v2-mixed-cjk') {
    for (const tradition of ['Chinese','Japanese']) for (const mode of ['strict','related','cross-tradition'] as const) {
      const selected=reloaded.glyphs.filter(g=>candidateCompatible(g,{writing_tradition:tradition,mode}))
      assert.equal(selected.length,mode==='cross-tradition'?6:3)
      if (mode!=='cross-tradition') assert.ok(selected.every(g=>g.source.writing_tradition===tradition))
      assertions++
    }
    assert.equal(new Set(reloaded.glyphs.map(g=>g.character)).size,3); assertions++
  }
}
// Enables an independent Python reader to compare exported semantics across runtimes.
writeFileSync('../../work/release-fixture-attribution.json',JSON.stringify(exports,null,2))
assert.deepEqual(exports,JSON.parse(readFileSync('../../tests/fixtures/projects/expected-attribution.json','utf8')))
console.log(`PASS: 6 frozen release fixtures, load/migrate/save/reload/attribution ZIP; ${assertions} integrity assertions`)
