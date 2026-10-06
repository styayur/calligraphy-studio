import type { Font, Blob as HBBlob, Face } from 'harfbuzzjs'
import { unicodeScript } from './identity'

const fonts = new Map<string, Promise<{ font: Font; blob: HBBlob; face: Face }>>()
export async function sha256(bytes: ArrayBuffer): Promise<string> {
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map((v) => v.toString(16).padStart(2, '0')).join('')
}
export interface ShaperFont { id: string; path: string; sha256: string; runtime_sha256: string }
/** Same locale/features/glyph-ID boundary as the Python shaper. WASM is local. */
export async function shapeFontGlyph(entry: ShaperFont, text: string, locale: string, vertical = false) {
  const hb = await import('harfbuzzjs')
  if (!fonts.has(entry.id)) fonts.set(entry.id, (async () => {
    const response = await fetch(`${import.meta.env.BASE_URL}fonts/${entry.path}`)
    if (!response.ok) throw new Error('Japanese font could not be loaded')
    const compressed = await response.arrayBuffer()
    if (await sha256(compressed) !== entry.runtime_sha256) throw new Error('Japanese runtime font checksum mismatch')
    const raw = await new Response(new Blob([compressed]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer()
    if (raw.byteLength > 40 * 1024 * 1024 || await sha256(raw) !== entry.sha256) throw new Error('Japanese source font checksum mismatch')
    const blob = new hb.Blob(raw), face = new hb.Face(blob), font = new hb.Font(face)
    font.setScale(face.upem, face.upem)
    return { font, blob, face }
  })().catch((error) => { fonts.delete(entry.id); throw error }))
  const { font, face } = await fonts.get(entry.id)!
  const buffer = new hb.Buffer()
  buffer.addText(text)
  buffer.guessSegmentProperties()
  buffer.setLanguage(locale)
  const script = unicodeScript(text), tag = { Han: 'Hani', Hiragana: 'Hira', Katakana: 'Kana' }[script || '']
  if (tag) buffer.setScript(tag)
  buffer.setDirection(vertical ? hb.Direction.TTB : hb.Direction.LTR)
  const features = [`locl=1`, `vert=${vertical ? 1 : 0}`, `vrt2=${vertical ? 1 : 0}`]
  hb.shape(font, buffer, features.map((f) => hb.Feature.fromString(f)!))
  const infos = buffer.getGlyphInfos(), positions = buffer.getGlyphPositions()
  if (infos.some((g) => !g.codepoint)) return null
  const paths: { path: Path2D; x: number; y: number }[] = []
  let penX = 0, penY = 0, left = Infinity, top = Infinity, right = -Infinity, bottom = -Infinity
  infos.forEach((g, i) => {
    const p = positions[i], e = font.glyphExtents(g.codepoint), x = penX + p.xOffset, y = penY + p.yOffset
    if (e) {
      left = Math.min(left, x + e.xBearing)
      top = Math.min(top, -y - e.yBearing)
      right = Math.max(right, x + e.xBearing + e.width)
      bottom = Math.max(bottom, -y - e.yBearing - e.height)
    }
    paths.push({ path: new Path2D(font.glyphToPath(g.codepoint)), x, y })
    penX += p.xAdvance; penY += p.yAdvance
  })
  if (![left, top, right, bottom].every(Number.isFinite)) return null
  const width = right - left, height = bottom - top
  const canvas = document.createElement('canvas'); canvas.width = canvas.height = 512
  const ctx = canvas.getContext('2d')!, scale = Math.min(420 / face.upem, 448 / Math.max(1,width), 448 / Math.max(1,height))
  let centerX = 256, centerY = 256
  if (locale === 'ja-JP' && '、。'.includes(text)) {
    centerX = vertical ? 400 : 112; centerY = vertical ? 112 : 400
  }
  ctx.translate(centerX - (left + width/2)*scale, centerY - (top + height/2)*scale)
  ctx.scale(scale, -scale); ctx.fillStyle = '#171b1a'
  for (const p of paths) { ctx.save(); ctx.translate(p.x,p.y); ctx.fill(p.path); ctx.restore() }
  const url = canvas.toDataURL('image/png')
  const checksum = await sha256(await (await fetch(url)).arrayBuffer())
  return { url, checksum, shaping: { engine: 'harfbuzz-wasm', harfbuzz_version: hb.versionString(),
    source_sequence: text, font_glyph_ids: infos.map((g) => g.codepoint), glyph_names: infos.map((g) => font.glyphName(g.codepoint)),
    features, locale, script, direction: vertical ? 'ttb' : 'ltr', font_sha256: entry.sha256,
    rasterizer: 'canvas-outline', normalization: 'em-scale-v1' } }
}
