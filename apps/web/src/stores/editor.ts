import { create } from 'zustand'
import type {
  Glyph,
  GlyphAppearance,
  GlyphInstance,
  GlyphTransform,
  ProjectDocument,
} from '../types'

const HISTORY_LIMIT = 60

const emptyProject = (): ProjectDocument => ({
  version: 1,
  canvas: { width: 1200, height: 800, background: '#f8f4ea' },
  glyphs: [],
})

const cloneProject = (project: ProjectDocument): ProjectDocument => structuredClone(project)

interface PatchOptions {
  recordHistory?: boolean
}

interface EditorState {
  projectId: string | null
  projectName: string
  project: ProjectDocument
  selectedId: string | null
  past: ProjectDocument[]
  future: ProjectDocument[]
  dirty: boolean
  batchOpen: boolean
  setProjectName: (name: string) => void
  selectGlyph: (id: string | null) => void
  addGlyph: (glyph: Glyph, x?: number, y?: number) => string
  addGlyphs: (glyphs: GlyphInstance[]) => void
  removeGlyph: (id: string) => void
  setGlyphTransform: (id: string, patch: Partial<GlyphTransform>, options?: PatchOptions) => void
  setGlyphAppearance: (
    id: string,
    patch: Partial<GlyphAppearance>,
    options?: PatchOptions,
  ) => void
  reorderGlyph: (id: string, direction: 'forward' | 'backward') => void
  beginHistory: () => void
  undo: () => void
  redo: () => void
  newProject: () => void
  loadProject: (name: string, document: ProjectDocument, id?: string | null) => void
  markSaved: (id?: string) => void
  setBatchOpen: (open: boolean) => void
}

function pushHistory(state: EditorState, project: ProjectDocument) {
  return {
    past: [...state.past, cloneProject(state.project)].slice(-HISTORY_LIMIT),
    future: [],
    project,
    dirty: true,
  }
}

export const useEditorStore = create<EditorState>((set, get) => ({
  projectId: null,
  projectName: '未命名集字',
  project: emptyProject(),
  selectedId: null,
  past: [],
  future: [],
  dirty: false,
  batchOpen: false,

  setProjectName: (name) => set({ projectName: name, dirty: true }),
  selectGlyph: (id) => set({ selectedId: id }),

  addGlyph: (glyph, x, y) => {
    const instanceId = crypto.randomUUID()
    set((state) => {
      const count = state.project.glyphs.length
      const instance: GlyphInstance = {
        ...structuredClone(glyph),
        id: instanceId,
        glyph_id: glyph.id,
        transform: {
          ...glyph.transform,
          x: x ?? state.project.canvas.width / 2 + (count % 3) * 26,
          y: y ?? state.project.canvas.height / 2 + (count % 3) * 22,
        },
      }
      const next = {
        ...state.project,
        glyphs: [...state.project.glyphs, instance],
      }
      return { ...pushHistory(state, next), selectedId: instanceId }
    })
    return instanceId
  },

  addGlyphs: (glyphs) =>
    set((state) => {
      if (glyphs.length === 0) return state
      const next = {
        ...state.project,
        glyphs: [...state.project.glyphs, ...glyphs],
      }
      return {
        ...pushHistory(state, next),
        selectedId: glyphs.at(-1)?.id ?? state.selectedId,
      }
    }),

  removeGlyph: (id) =>
    set((state) => {
      const next = {
        ...state.project,
        glyphs: state.project.glyphs.filter((glyph) => glyph.id !== id),
      }
      return {
        ...pushHistory(state, next),
        selectedId: state.selectedId === id ? null : state.selectedId,
      }
    }),

  setGlyphTransform: (id, patch, options = {}) =>
    set((state) => {
      const next = {
        ...state.project,
        glyphs: state.project.glyphs.map((glyph) =>
          glyph.id === id
            ? { ...glyph, transform: { ...glyph.transform, ...patch } }
            : glyph,
        ),
      }
      if (options.recordHistory === false) return { project: next, dirty: true }
      return pushHistory(state, next)
    }),

  setGlyphAppearance: (id, patch, options = {}) =>
    set((state) => {
      const next = {
        ...state.project,
        glyphs: state.project.glyphs.map((glyph) =>
          glyph.id === id
            ? { ...glyph, appearance: { ...glyph.appearance, ...patch } }
            : glyph,
        ),
      }
      if (options.recordHistory === false) return { project: next, dirty: true }
      return pushHistory(state, next)
    }),

  reorderGlyph: (id, direction) =>
    set((state) => {
      const glyphs = [...state.project.glyphs]
      const index = glyphs.findIndex((glyph) => glyph.id === id)
      if (index < 0) return state
      const target = direction === 'forward' ? Math.min(glyphs.length - 1, index + 1) : Math.max(0, index - 1)
      if (target === index) return state
      const [item] = glyphs.splice(index, 1)
      glyphs.splice(target, 0, item)
      return pushHistory(state, { ...state.project, glyphs })
    }),

  beginHistory: () =>
    set((state) => ({
      past: [...state.past, cloneProject(state.project)].slice(-HISTORY_LIMIT),
      future: [],
    })),

  undo: () =>
    set((state) => {
      const previous = state.past.at(-1)
      if (!previous) return state
      return {
        project: previous,
        past: state.past.slice(0, -1),
        future: [cloneProject(state.project), ...state.future].slice(0, HISTORY_LIMIT),
        dirty: true,
        selectedId: previous.glyphs.some((glyph) => glyph.id === state.selectedId)
          ? state.selectedId
          : null,
      }
    }),

  redo: () =>
    set((state) => {
      const next = state.future[0]
      if (!next) return state
      return {
        project: next,
        past: [...state.past, cloneProject(state.project)].slice(-HISTORY_LIMIT),
        future: state.future.slice(1),
        dirty: true,
      }
    }),

  newProject: () =>
    set({
      projectId: null,
      projectName: '未命名集字',
      project: emptyProject(),
      selectedId: null,
      past: [],
      future: [],
      dirty: false,
    }),

  loadProject: (name, document, id = null) =>
    set({
      projectId: id,
      projectName: name,
      project: cloneProject(document),
      selectedId: null,
      past: [],
      future: [],
      dirty: false,
    }),

  markSaved: (id) => set({ projectId: id ?? get().projectId, dirty: false }),
  setBatchOpen: (open) => set({ batchOpen: open }),
}))