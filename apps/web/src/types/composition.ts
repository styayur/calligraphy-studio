import type { Glyph, GlyphInstance } from './glyph'

export type BatchLayout = 'grid' | 'vertical-rtl' | 'horizontal-ltr'

export interface BatchComposeRequest {
  text: string
  layout: BatchLayout
  columns: number
  cell_width: number
  cell_height: number
  gap_x: number
  gap_y: number
  start_x: number
  start_y: number
  calligrapher?: string
  style?: string
  dataset?: string
  writing_tradition?: string
  locale?: string
  script?: string
  variant_type?: string
  mode?: 'strict' | 'related' | 'cross-tradition'
  commercial_only?: boolean
  use_structural_fallback: boolean
}

export interface BatchPlacement {
  glyph: GlyphInstance
  line: number
  column: number
}

export interface BatchComposeResponse {
  placements: BatchPlacement[]
  missing: string[]
  total_characters: number
  resolved_characters: number
}

export interface SimilarGlyphItem {
  glyph: Glyph
  score: number
}

export interface SimilarityResponse {
  target_id: string
  model_name: string
  items: SimilarGlyphItem[]
}
