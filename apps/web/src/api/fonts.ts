import type { Glyph } from '../types'

interface FontEntry {
  id: string
  family: string
  designer: string
  style: string
  characters: string
  license: string
  license_url: string
  rights: Record<string, boolean>
}
let catalog: Promise<FontEntry[]> | undefined
const faces = new Map<string, Promise<FontFace>>()
const glyphCache = new Map<string, Glyph>()

export function fontCatalog(): Promise<FontEntry[]> {
  if (!catalog)
    catalog = fetch(`${import.meta.env.BASE_URL}fonts/catalog.json`)
      .then(async (response) => {
        if (!response.ok) throw new Error('内置字库加载失败，请刷新重试')
        return response.json()
      })
      .catch((error) => {
        catalog = undefined
        throw error
      })
  return catalog
}

export async function fontGlyphs(character: string, style = '', designer = ''): Promise<Glyph[]> {
  const entries = (await fontCatalog()).filter(
    (font) =>
      font.characters.includes(character) &&
      (!style || font.style === style) &&
      (!designer || font.designer === designer),
  )
  return Promise.all(
    entries.map(async (font) => {
      const id = `font:${font.id}:${character}`
      const cached = glyphCache.get(id)
      if (cached) return cached
      if (!faces.has(font.id)) {
        const face = new FontFace(
          font.id,
          `url("${import.meta.env.BASE_URL}fonts/${font.id}.woff2")`,
        )
        faces.set(
          font.id,
          face
            .load()
            .then((loaded) => {
              document.fonts.add(loaded)
              return loaded
            })
            .catch((error) => {
              faces.delete(font.id)
              throw error
            }),
        )
      }
      await faces.get(font.id)
      const canvas = document.createElement('canvas')
      canvas.width = canvas.height = 512
      const context = canvas.getContext('2d')!
      context.font = `400px "${font.id}"`
      const metrics = context.measureText(character)
      const width = metrics.actualBoundingBoxLeft + metrics.actualBoundingBoxRight
      const height = metrics.actualBoundingBoxAscent + metrics.actualBoundingBoxDescent
      const scale = Math.min(448 / Math.max(width, 1), 448 / Math.max(height, 1))
      context.translate(256, 256)
      context.scale(scale, scale)
      context.fillStyle = '#171b1a'
      context.fillText(
        character,
        (metrics.actualBoundingBoxLeft - metrics.actualBoundingBoxRight) / 2,
        (metrics.actualBoundingBoxAscent - metrics.actualBoundingBoxDescent) / 2,
      )
      const glyph: Glyph = {
        id,
        character,
        source: {
          dataset: 'OFL Calligraphy Fonts',
          calligrapher: font.designer,
          style: font.style,
          dynasty: '当代',
          work: font.family,
          license: font.license,
          license_url: font.license_url,
          rights: font.rights,
        },
        asset: {
          type: 'raster',
          url: canvas.toDataURL('image/png'),
          width: 512,
          height: 512,
          bbox: [0, 0, 512, 512],
        },
        transform: { x: 0, y: 0, scaleX: 0.3, scaleY: 0.3, rotation: 0, skewX: 0, skewY: 0 },
        appearance: { opacity: 1, blendMode: 'multiply' },
        provenance: { type: 'font' },
      }
      glyphCache.set(id, glyph)
      return glyph
    }),
  )
}
