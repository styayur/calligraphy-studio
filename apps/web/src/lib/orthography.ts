import metadata from '../../../../samples/japanese/orthography.json'
import type { VariantType } from '../types/glyph'
import { unicodeScript } from './identity'

/** Discovery relationships do not alter the semantic Unicode sequence. */
export function japaneseVariant(text: string, configuredType?: VariantType): { type?: VariantType; canonical?: string } {
  if (configuredType === 'hentaigana') return { type:unicodeScript(text) === 'Hiragana' ? 'hentaigana' : 'font-alternate' }
  for (const [modern,old] of Object.entries(metadata.pairs)) {
    if (modern === old) continue
    if (text === modern) return { type:'shinjitai',canonical:modern }
    if (text === old) return { type:'kyujitai',canonical:modern }
  }
  return { type:configuredType }
}
