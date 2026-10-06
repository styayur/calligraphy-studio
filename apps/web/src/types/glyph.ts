export type VariantType = 'modern' | 'traditional' | 'simplified' | 'shinjitai' | 'kyujitai' | 'hentaigana' | 'historical' | 'regional' | 'font-alternate'
export interface CharacterIdentity {
  text: string
  codepoints: string[]
  script?: string | null
  language?: string | null
  locale?: string | null
  canonical?: string | null
}
export interface GlyphVariant {
  type?: VariantType | null
  id?: string | null
  glyph_name?: string | null
  font_glyph_id?: number | null
}
export interface ScriptMetadata {
  language?: string | null
  locale?: string | null
  script?: string | null
  writing_tradition?: string | null
  orthography?: string | null
  period?: string | null
  region?: string | null
  source_collection?: string | null
}
export interface RightsRecord {
  commercial_use: boolean | null
  derivatives_allowed: boolean | null
  redistribution_allowed: boolean | null
  research_use: boolean | null
  attribution_required: boolean | null
  font_license: boolean | null
  share_alike_required: boolean | null
}
export interface GlyphSource extends ScriptMetadata {
  dataset: string
  calligrapher?: string | null
  style?: string | null
  dynasty?: string | null
  work?: string | null
  license?: string | null
  license_url?: string | null
  rights?: Record<string, boolean | null>
  source_uri?: string | null
  attribution?: string | null
  designer?: string | null
  dataset_version?: string | null
  source_checksum?: string | null
  license_text?: string | null
}

export interface GlyphAsset {
  processing?: 'ink-mask'
  type: 'raster' | 'svg' | 'generated'
  url: string
  width: number
  height: number
  bbox: [number, number, number, number]
  checksum?: string | null
}

export interface GlyphTransform {
  x: number
  y: number
  scaleX: number
  scaleY: number
  rotation: number
  skewX: number
  skewY: number
}

export interface GlyphAppearance {
  opacity: number
  blendMode: string
}

export interface GlyphProvenance {
  type: 'original' | 'font' | 'fallback' | 'generated'
  confidence?: number | null
}

export interface Glyph {
  id: string
  character: string
  source: GlyphSource
  asset: GlyphAsset
  transform: GlyphTransform
  appearance: GlyphAppearance
  provenance: GlyphProvenance
  identity?: CharacterIdentity
  variant?: GlyphVariant
  metadata?: Record<string, unknown>
}

export interface GlyphInstance extends Glyph {
  glyph_id: string
}
