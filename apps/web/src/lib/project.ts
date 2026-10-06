import type { ProjectDocument } from '../types'
import { codepoints, migrateGlyph } from './identity'

export function validateProject(value: unknown): ProjectDocument {
  const p = value as ProjectDocument
  if (!p || ![1,2].includes(p.version) || !p.canvas || !Array.isArray(p.glyphs))
    throw new Error('请选择有效的集字项目文件')
  const { width, height, background } = p.canvas
  if (
    ![width, height].every((n) => Number.isFinite(n) && n >= 100 && n <= 8000) ||
    width * height > 20_000_000 ||
    !/^#[\da-f]{6}$/i.test(background)
  )
    throw new Error('项目纸面尺寸或颜色无效')
  if (p.glyphs.length > 1000) throw new Error('项目字形过多，最多载入 1000 字')
  if (p.text !== undefined && typeof p.text !== 'string') throw new Error('项目文字无效')
  if (p.composition) {
    const c = p.composition
    if (
      !['grid', 'horizontal-ltr', 'vertical-rtl'].includes(c.layout) ||
      !['fonts', 'original', 'all', 'fallback'].includes(c.source) ||
      typeof c.style !== 'string' ||
      typeof c.punctuation !== 'boolean' ||
      ![c.columns, c.size, c.gap, c.margin].every(Number.isFinite) ||
      !Number.isInteger(c.columns) ||
      c.columns < 1 ||
      c.columns > 30 ||
      c.size < 40 ||
      c.size > 400 ||
      c.gap < 0 ||
      c.gap > 160 ||
      c.margin < 0 ||
      c.margin > 300
    )
      throw new Error('项目排版参数无效')
    if (c.policy) {
      const policy=c.policy
      if (typeof policy !== 'object' || Array.isArray(policy) ||
        !['writing_tradition','language','locale','script','variant_type','orthography','period','work','designer','dataset','provenance_type'].every((key) => {const value=policy[key as keyof typeof policy]; return value == null || (typeof value === 'string' && value.length <= 1000)}) ||
        (policy.mode != null && !['strict','related','cross-tradition'].includes(policy.mode)) ||
        (policy.commercial_only != null && typeof policy.commercial_only !== 'boolean') ||
        (policy.vertical != null && typeof policy.vertical !== 'boolean')) throw new Error('项目选择规则无效')
    }
  }
  const ids = new Set<string>()
  for (const g of p.glyphs) {
    if (g?.identity && (g.identity.text !== g.character || JSON.stringify(g.identity.codepoints) !== JSON.stringify(codepoints(g.character)))) throw new Error('项目 Unicode 身份无效')
    if (
      !g ||
      typeof g.id !== 'string' ||
      ids.has(g.id) ||
      typeof g.character !== 'string' ||
      g.character.length < 1 || g.character.length > 64 ||
      !g.source ||
      !g.asset ||
      !g.transform ||
      !g.appearance ||
      !g.provenance ||
      typeof g.glyph_id !== 'string'
    )
      throw new Error('项目包含无效字形')
    ids.add(g.id)
    if (
      typeof g.source.dataset !== 'string' ||
      !['calligrapher', 'style', 'dynasty', 'work', 'license', 'license_url','language','locale','script','writing_tradition','orthography','period','region','source_collection','source_uri','attribution','designer','dataset_version','source_checksum','license_text'].every((key) => {
        const value = g.source[key as keyof typeof g.source]
        return value == null || typeof value === 'string'
      }) ||
      !['font', 'original', 'fallback', 'generated'].includes(g.provenance.type)
    )
      throw new Error('项目字形来源无效')
    if (g.variant && (
      (g.variant.type != null && !['modern','traditional','simplified','shinjitai','kyujitai','hentaigana','historical','regional','font-alternate'].includes(g.variant.type)) ||
      !['id','glyph_name'].every((key) => { const v=g.variant![key as 'id' | 'glyph_name']; return v == null || (typeof v === 'string' && v.length <= 256) }) ||
      (g.variant.font_glyph_id != null && (!Number.isInteger(g.variant.font_glyph_id) || g.variant.font_glyph_id < 0))
    )) throw new Error('项目字形变体无效')
    if (
      !['source-over', 'multiply', 'screen', 'overlay', 'darken', 'lighten'].includes(
        g.appearance.blendMode,
      )
    )
      throw new Error('项目混合模式无效')
    if (
      typeof g.asset.url !== 'string' ||
      !/^(data:image\/(png|jpeg|webp);base64,|https?:\/\/|(?:\.\/|\/)?(?:[\w.-]+\/)*(?:demo|assets)\/)/i.test(
        g.asset.url,
      )
    )
      throw new Error('项目包含不支持的图片地址')
    if (
      ![g.asset.width, g.asset.height].every((n) => Number.isFinite(n) && n > 0 && n <= 16000) ||
      !['x', 'y', 'scaleX', 'scaleY', 'rotation', 'skewX', 'skewY'].every((key) =>
        Number.isFinite(g.transform[key as keyof typeof g.transform]),
      ) ||
      !Number.isFinite(g.appearance.opacity) ||
      g.appearance.opacity < 0 ||
      g.appearance.opacity > 1
    )
      throw new Error('项目字形参数无效')
  }
  return { ...p, version: 2, glyphs: p.glyphs.map(migrateGlyph) }
}

export interface Draft {
  name: string
  document: ProjectDocument
}
function database(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('calligraphy-studio', 1)
    request.onupgradeneeded = () => request.result.createObjectStore('drafts')
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}
export async function readDraft(): Promise<Draft | undefined> {
  const db = await database()
  return new Promise((resolve, reject) => {
    const transaction = db.transaction('drafts')
    const request = transaction.objectStore('drafts').get('current')
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
    transaction.oncomplete = () => db.close()
  })
}
export async function writeDraft(draft: Draft): Promise<void> {
  const db = await database()
  return new Promise((resolve, reject) => {
    const transaction = db.transaction('drafts', 'readwrite')
    transaction.objectStore('drafts').put(draft, 'current')
    transaction.oncomplete = () => {
      db.close()
      resolve()
    }
    transaction.onerror = () => {
      db.close()
      reject(transaction.error)
    }
    transaction.onabort = () => {
      db.close()
      reject(transaction.error)
    }
  })
}
