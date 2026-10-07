import type { Glyph } from '../types'
import { migrateGlyph, semanticIdentity } from './identity'

export interface ExportPolicy { commercialOnly?: boolean; derivative?: boolean }
/** Private editing can retain unknown rights; publication cannot override explicit restrictions. */
export function assertExportRights(glyphs: Glyph[], policy: ExportPolicy = {}) {
  for (const g of glyphs) {
    const rights = g.source.rights
    if (policy.commercialOnly && rights?.commercial_use !== true) throw new Error(`「${g.character}」未明确允许商用 / Commercial rights are not confirmed`)
    if (rights?.redistribution_allowed === false) throw new Error(`「${g.character}」不允许再分发 / Redistribution prohibited`)
    if (policy.derivative !== false && rights?.derivatives_allowed === false && !rights.font_license)
      throw new Error(`「${g.character}」不允许改作 / Derivatives prohibited`)
  }
}
export const hasShareAlike = (glyphs: Glyph[]) => glyphs.some((g) => g.source.rights?.share_alike_required === true)

export function attributionManifest(glyphs: Glyph[], policy: ExportPolicy = {}) {
  assertExportRights(glyphs, policy)
  const adaptedLicences = [...new Set(glyphs.filter((g) => g.source.rights?.share_alike_required && !g.source.rights.font_license).map((g) => g.source.license))]
  return { schema_version: 2, artwork_license: adaptedLicences.length === 1 && adaptedLicences[0] === 'CC-BY-SA-4.0' ? 'CC-BY-SA-4.0' : null,
    share_alike_licences:adaptedLicences,
    licence_boundary: 'Third-party source licences do not inherit the MIT application licence. OFL font licences do not automatically apply to artwork.',
    glyphs: Array.from(new Map(glyphs.map((g) => [g.id, g])).values()).map((g) => ({
      id:g.id, character:g.character, identity:semanticIdentity(g), variant:g.variant || {}, provenance:g.provenance,
      source:migrateGlyph(g).source, asset_checksum:g.asset.checksum || null, metadata:g.metadata || {},
      changes:g.asset.processing || (g.provenance.type === 'font' ? 'Font outline rasterisation and composition' : 'Glyph composition'),
    })) }
}
export async function attributionFiles(glyphs: Glyph[], policy: ExportPolicy = {}) {
  const manifest = attributionManifest(glyphs,policy), encoder = new TextEncoder()
  const human = ['Glyph attribution / 字形来源与授权', manifest.licence_boundary,
    manifest.artwork_license ? 'Artwork contains adapted CC-BY-SA-4.0 material. Distribute adapted artwork under CC-BY-SA-4.0; retain attribution and identify changes.' : 'Review each source before publishing; unknown rights remain unknown.',
    ...manifest.glyphs.map((g) => `\n${g.character} (${g.identity.codepoints.join(' ')}) — ${g.source.work || g.source.dataset}\n${g.source.attribution || g.source.designer || g.source.calligrapher || 'Attribution unknown'}\n${g.source.license || 'Licence unknown'} ${g.source.license_url || ''}\n${g.source.source_uri || ''}\nChanges: ${g.changes}\nSource SHA256: ${g.source.source_checksum || 'unknown'}\nAsset SHA256: ${g.asset_checksum || 'unknown'}`)]
  const files = [{ name:'attribution.json', data:encoder.encode(JSON.stringify(manifest,null,2)) }, { name:'ATTRIBUTION.txt', data:encoder.encode(human.join('\n')) }]
  for (const path of new Set(glyphs.map((g) => g.source.license_text).filter((p): p is string => !!p))) {
    // Project imports must not turn licence fetching into arbitrary local/network requests.
    if (!/^(fonts\/licenses\/OFL-[a-z-]+\.txt|japanese\/licenses\/CC-BY-SA-4\.0\.txt|demo\/licenses\/[a-zA-Z0-9.-]+\.txt)$/.test(path)) continue
    const response = await fetch(`${import.meta.env.BASE_URL}${path}`)
    if (!response.ok) throw new Error(`Bundled licence unavailable: ${path}`)
    const data = new Uint8Array(await response.arrayBuffer())
    if (data.length > 100000) throw new Error('Excessive licence text')
    files.push({ name:`licenses/${path.split('/').at(-1)}`, data })
  }
  return files
}
