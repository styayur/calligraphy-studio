import type { BatchLayout, Glyph, GlyphInstance } from '../types'

export interface LayoutOptions {
  layout: BatchLayout
  columns: number
  size: number
  gap: number
  margin: number
  punctuation: boolean
}
export function textLines(text: string, punctuation: boolean): string[][] {
  return text
    .replace(/\r\n?/g, '\n')
    .split('\n')
    .map((line) =>
      [...line].filter((char) => !/\s/u.test(char) && (punctuation || !/\p{P}/u.test(char))),
    )
    .filter((line) => line.length)
}
export function layoutText(text: string, options: LayoutOptions) {
  const { layout, columns, size, gap, margin } = options
  if (
    ![columns, size, gap, margin].every(Number.isFinite) ||
    !Number.isInteger(columns) ||
    columns < 1 ||
    columns > 30 ||
    size < 40 ||
    size > 400 ||
    gap < 0 ||
    gap > 160 ||
    margin < 0 ||
    margin > 300
  )
    throw new Error('请填写有效的排版数值')
  const lines = textLines(text, options.punctuation)
  const count = lines.flat().length
  if (!count) throw new Error('请先输入需要集字的文字')
  if (count > 200) throw new Error('单幅作品最多支持 200 字，请分幅集字')
  const chunks: string[][] = []
  if (layout === 'grid') {
    const chars = lines.flat()
    for (let index = 0; index < chars.length; index += columns)
      chunks.push(chars.slice(index, index + columns))
  } else {
    for (const line of lines)
      for (let index = 0; index < line.length; index += columns)
        chunks.push(line.slice(index, index + columns))
  }
  const vertical = layout === 'vertical-rtl'
  const across = vertical ? chunks.length : Math.max(...chunks.map((line) => line.length))
  const down = vertical ? Math.max(...chunks.map((line) => line.length)) : chunks.length
  const width = margin * 2 + across * size + (across - 1) * gap
  const height = margin * 2 + down * size + (down - 1) * gap
  if (width > 8000 || height > 8000 || width * height > 20_000_000)
    throw new Error('纸面过大，请减小字格、间距或每行字数')
  const positions = chunks.flatMap((line, row) =>
    line.map((character, column) => ({
      character,
      x: margin + (vertical ? across - row - 1 : column) * (size + gap) + size / 2,
      y: margin + (vertical ? column : row) * (size + gap) + size / 2,
    })),
  )
  return { positions, width, height }
}

export function placeGlyph(glyph: Glyph, x: number, y: number, size: number): GlyphInstance {
  const scale = (size / Math.max(glyph.asset.width, glyph.asset.height)) * 0.86
  return {
    ...structuredClone(glyph),
    id: crypto.randomUUID(),
    glyph_id: glyph.id,
    transform: { ...glyph.transform, x, y, scaleX: scale, scaleY: scale },
  }
}
