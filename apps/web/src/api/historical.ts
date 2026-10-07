import type { Glyph } from '../types'
import { migrateGlyph } from '../lib/identity'
import { candidateCompatible, type CandidatePolicy } from '../lib/candidatePolicy'

let sample: Promise<Glyph[]> | undefined
/** Only metadata loads upfront. Individual sample pictures load on selection. */
export function historicalSample(): Promise<Glyph[]> {
  if (!sample) sample = fetch(`${import.meta.env.BASE_URL}japanese/glyphs.json`).then(async (r) => {
    if (!r.ok) throw new Error('CODH sample could not be loaded')
    return (await r.json() as Glyph[]).map((g) => migrateGlyph({ ...g, asset: { ...g.asset, url: `${import.meta.env.BASE_URL}${g.asset.url}` } }))
  }).catch((error) => { sample = undefined; throw error })
  return sample
}
export async function historicalGlyphs(character: string, policy: CandidatePolicy = {}): Promise<Glyph[]> {
  return (await historicalSample()).filter((g) => g.character === character && candidateCompatible(g,policy))
}
