import type { Glyph, GlyphSource, GlyphVariant } from '../types/glyph'

export type ExplorationMode = 'strict' | 'related' | 'cross-tradition'
export interface CandidatePolicy {
  writing_tradition?: string
  language?: string
  locale?: string
  script?: string
  variant_type?: string
  orthography?: string
  period?: string
  work?: string
  designer?: string
  dataset?: string
  provenance_type?: string
  commercial_only?: boolean
  mode?: ExplorationMode
  vertical?: boolean
}
export const DEFAULT_POLICY: CandidatePolicy = { writing_tradition: 'Chinese', mode: 'strict' }
export const CANDIDATE_WEIGHTS = { visual: .55, locale: .12, tradition: .12, script: .08, period: .05, work: .05, repetition: 1 }
export type CandidateWeights = typeof CANDIDATE_WEIGHTS
/** Fail closed for unknown traditions when a tradition is explicitly selected. */
export function compatibleSource(source: GlyphSource, variant: GlyphVariant | undefined, provenance: string, policy: CandidatePolicy): boolean {
  if (policy.mode !== 'cross-tradition') {
    if (policy.writing_tradition && source.writing_tradition !== policy.writing_tradition) return false
    if (policy.locale && source.locale && source.locale !== policy.locale) return false
    if (policy.language && source.language && source.language !== policy.language) return false
  }
  if (policy.script && source.script !== policy.script) return false
  if (policy.variant_type && variant?.type !== policy.variant_type) return false
  // Historical kana is an explicit opt-in; related mode permits exploration within tradition.
  if (policy.mode === 'strict' && !policy.variant_type && variant?.type === 'hentaigana') return false
  if (policy.mode === 'strict' && !policy.variant_type && source.orthography === 'historical-kana') return false
  if (policy.orthography && source.orthography !== policy.orthography) return false
  if (policy.period && source.period !== policy.period) return false
  if (policy.work && source.work !== policy.work) return false
  if (policy.dataset && source.dataset !== policy.dataset) return false
  if (policy.designer && source.designer !== policy.designer && source.calligrapher !== policy.designer) return false
  if (policy.provenance_type && provenance !== policy.provenance_type) return false
  if (policy.commercial_only && source.rights?.commercial_use !== true) return false
  return true
}
export function candidateCompatible(glyph: Glyph, policy: CandidatePolicy): boolean {
  return compatibleSource(glyph.source, glyph.variant, glyph.provenance.type, policy)
}
/** A computational cost, not authenticity or aesthetic merit. Unknown fields add no evidence. */
export function candidateCost(glyph: Glyph, visualCost: number, policy: CandidatePolicy,
  neighbors: Glyph[] = [], repetition = 0, weights: CandidateWeights = CANDIDATE_WEIGHTS): number {
  if (!candidateCompatible(glyph, policy)) return Infinity
  if (Object.values(weights).some((v) => !Number.isFinite(v) || v < 0)) throw new Error('Invalid candidate weights')
  const mismatch = (actual?: string | null, expected?: string | null) => actual && expected && actual !== expected ? 1 : 0
  const work = neighbors.filter((g) => g.source.work && glyph.source.work)
  return weights.visual * visualCost + weights.locale * mismatch(glyph.source.locale, policy.locale) +
    weights.tradition * mismatch(glyph.source.writing_tradition, policy.writing_tradition) +
    weights.script * mismatch(glyph.source.script, policy.script) + weights.period * mismatch(glyph.source.period, policy.period) +
    weights.work * (work.length ? work.filter((g) => g.source.work !== glyph.source.work).length / work.length : 0) +
    weights.repetition * repetition
}
