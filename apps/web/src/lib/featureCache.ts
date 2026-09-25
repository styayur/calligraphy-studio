import type { Glyph } from '../types'
import { FEATURE_VERSION, RESOLUTION, type VisualProfile } from './visual'

const memory = new Map<string, Promise<VisualProfile>>()
const assetTokens = new Map<string, number>()
let assetSequence = 0
export function assetToken(glyph: Glyph) {
  const key = glyph.asset.url
  if (!assetTokens.has(key)) assetTokens.set(key, ++assetSequence)
  return assetTokens.get(key)!
}
let worker: Worker | undefined,
  sequence = 0
const pending = new Map<
  number,
  {
    resolve: (p: VisualProfile) => void
    reject: (e: Error) => void
    timer: ReturnType<typeof setTimeout>
  }
>()
export const featureStats = { computed: 0, memoryHits: 0, diskHits: 0 }
function compute(ink: Float32Array): Promise<VisualProfile> {
  if (!worker) {
    worker = new Worker(new URL('./visual.worker.ts', import.meta.url), {
      type: 'module',
    })
    worker.onmessage = ({ data }) => {
      const task = pending.get(data.id)
      if (!task) return
      clearTimeout(task.timer)
      pending.delete(data.id)
      if (data.error) task.reject(new Error(data.error))
      else {
        featureStats.computed++
        task.resolve(data.profile)
      }
    }
    worker.onerror = () => {
      for (const task of pending.values()) {
        clearTimeout(task.timer)
        task.reject(new Error('特征线程失败，请重试'))
      }
      pending.clear()
      worker?.terminate()
      worker = undefined
    }
  }
  return new Promise((resolve, reject) => {
    const id = ++sequence
    const timer = setTimeout(() => {
      pending.delete(id)
      reject(new Error('特征计算超时，请重试'))
    }, 30000)
    pending.set(id, { resolve, reject, timer })
    worker!.postMessage({ id, ink }, [ink.buffer])
  })
}
async function disk(key: string, profile?: VisualProfile): Promise<VisualProfile | undefined> {
  return new Promise((resolve) => {
    const request = indexedDB.open('calligraphy-features', 1)
    request.onupgradeneeded = () => request.result.createObjectStore('profiles')
    request.onerror = () => resolve(undefined)
    request.onsuccess = () => {
      const db = request.result,
        tx = db.transaction('profiles', profile ? 'readwrite' : 'readonly'),
        store = tx.objectStore('profiles')
      if (profile) store.put(profile, key)
      else {
        const get = store.get(key)
        get.onsuccess = () => resolve(get.result)
        get.onerror = () => resolve(undefined)
      }
      tx.oncomplete = () => {
        db.close()
        resolve(undefined)
      }
      tx.onerror = tx.onabort = () => {
        db.close()
        resolve(undefined)
      }
    }
  })
}
export function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.crossOrigin = 'anonymous'
    const timer = setTimeout(() => reject(new Error('字形图片加载超时')), 15000)
    image.onload = () => {
      clearTimeout(timer)
      resolve(image)
    }
    image.onerror = () => {
      clearTimeout(timer)
      reject(new Error('无法读取字形图片'))
    }
    image.src = url
  })
}
export function featureKey(glyph: Glyph) {
  return `${FEATURE_VERSION}:${glyph.asset.processing || ''}:${glyph.asset.url}`
}
let running = 0
const queue: (() => void)[] = []
async function limited<T>(action: () => Promise<T>): Promise<T> {
  if (running >= 3) await new Promise<void>((resolve) => queue.push(resolve))
  running++
  try {
    return await action()
  } finally {
    running--
    queue.shift()?.()
  }
}
/** In-flight de-duplication + bounded memory + content-addressed persistent raster cache.
 * A replacement invalidates only its image. Position edits never re-extract source features. */
export function getVisualProfile(glyph: Glyph): Promise<VisualProfile> {
  const key = featureKey(glyph),
    cached = memory.get(key)
  if (cached) {
    featureStats.memoryHits++
    return cached
  }
  const task = limited(async () => {
    const image = await loadImage(glyph.asset.url),
      n = RESOLUTION
    const canvas = document.createElement('canvas')
    canvas.width = canvas.height = n
    const ctx = canvas.getContext('2d', { willReadFrequently: true })!
    // Preserve aspect ratio with a white letterbox, and composite alpha onto white.
    ctx.fillStyle = 'white'
    ctx.fillRect(0, 0, n, n)
    const scale = n / Math.max(image.naturalWidth, image.naturalHeight)
    ctx.drawImage(
      image,
      (n - image.naturalWidth * scale) / 2,
      (n - image.naturalHeight * scale) / 2,
      image.naturalWidth * scale,
      image.naturalHeight * scale,
    )
    const rgba = ctx.getImageData(0, 0, n, n).data
    const ink = new Float32Array(n * n)
    for (let i = 0; i < ink.length; i++)
      ink[i] =
        1 - (rgba[i * 4] * 0.2126 + rgba[i * 4 + 1] * 0.7152 + rgba[i * 4 + 2] * 0.0722) / 255
    const digest = await crypto.subtle.digest('SHA-256', rgba.buffer)
    const hash =
      FEATURE_VERSION +
      ':' +
      Array.from(new Uint8Array(digest), (v) => v.toString(16).padStart(2, '0')).join('')
    const stored = await disk(hash).catch(() => undefined)
    if (stored?.version === FEATURE_VERSION) {
      featureStats.diskHits++
      return stored
    }
    const result = await compute(ink)
    await disk(hash, result).catch(() => undefined)
    return result
  }).catch((error) => {
    memory.delete(key)
    throw error
  })
  memory.set(key, task)
  if (memory.size > 4096) memory.delete(memory.keys().next().value!)
  return task
}
