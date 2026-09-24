import type { Glyph } from '../types'

const masks = new Map<string, Promise<Glyph>>()
/** NCCU supplies monochrome, white-on-black scans. Keep the source metadata,
 * but produce a transparent ink mask for composition (MIT permits adaptation). */
export async function prepareInk(glyph: Glyph): Promise<Glyph> {
  if (
    !glyph.source.dataset.includes('NCCU') ||
    glyph.asset.type !== 'raster' ||
    glyph.asset.processing === 'ink-mask'
  )
    return glyph
  const key = glyph.asset.url
  if (!masks.has(key))
    masks.set(
      key,
      new Promise<Glyph>((resolve, reject) => {
        const image = new Image()
        image.crossOrigin = 'anonymous'
        image.onerror = () => reject(new Error(`「${glyph.character}」原帖图片加载失败，请重试`))
        image.onload = () => {
          try {
            const canvas = document.createElement('canvas')
            canvas.width = image.naturalWidth
            canvas.height = image.naturalHeight
            const context = canvas.getContext('2d')!
            context.drawImage(image, 0, 0)
            const pixels = context.getImageData(0, 0, canvas.width, canvas.height)
            const { data } = pixels
            const luminance = (index: number) =>
              data[index] * 0.2126 + data[index + 1] * 0.7152 + data[index + 2] * 0.0722
            const corners = [
              0,
              (canvas.width - 1) * 4,
              (canvas.height - 1) * canvas.width * 4,
              data.length - 4,
            ]
            const inverted = corners.reduce((sum, index) => sum + luminance(index), 0) / 4 < 128
            for (let i = 0; i < data.length; i += 4) {
              const ink = inverted ? luminance(i) : 255 - luminance(i)
              data[i + 3] = Math.round(data[i + 3] * Math.max(0, Math.min(1, (ink - 12) / 231)))
              data[i] = 23
              data[i + 1] = 27
              data[i + 2] = 26
            }
            context.putImageData(pixels, 0, 0)
            resolve({
              ...glyph,
              asset: { ...glyph.asset, url: canvas.toDataURL('image/png'), processing: 'ink-mask' },
            })
          } catch {
            reject(new Error(`「${glyph.character}」无法净底，请检查图片来源`))
          }
        }
        image.src = glyph.asset.url
      }).catch((error) => {
        masks.delete(key)
        throw error
      }),
    )
  return masks.get(key)!
}
