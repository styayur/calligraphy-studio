export interface GlyphSource {
  dataset: string
  calligrapher?: string | null
  style?: string | null
  dynasty?: string | null
  work?: string | null
  license?: string | null
  license_url?: string | null
  rights?: Record<string, boolean | null>
}

export interface GlyphAsset {
  type: 'raster' | 'svg' | 'generated'
  url: string
  width: number
  height: number
  bbox: [number, number, number, number]
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
}

export interface GlyphInstance extends Glyph {
  glyph_id: string
}