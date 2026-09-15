import type { GlyphInstance } from './glyph'

export interface CanvasConfig {
  width: number
  height: number
  background: string
}

export interface ProjectDocument {
  version: 1
  canvas: CanvasConfig
  glyphs: GlyphInstance[]
}

export interface ProjectRecord {
  id: string
  name: string
  document: ProjectDocument
}

export interface ProjectListItem {
  id: string
  name: string
}