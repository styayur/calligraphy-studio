import { profileCost, type VisualProfile } from './visual'
export interface ProfileCandidate {
  id: string
  character: string
  profile: VisualProfile
}
export interface BeamOptions {
  width: number
  variation: number
  signal?: AbortSignal
  progress?: (done: number) => void
}
interface State {
  cost: number
  candidate: ProfileCandidate | null
  parent: State | null
  recent: ProfileCandidate[]
}
/** Back-pointers; O(N·B·K) expansion; last 32 glyphs constrain repetition. */
export async function selectSequence(
  characters: string[],
  candidates: Map<string, ProfileCandidate[]>,
  context: VisualProfile[],
  options: BeamOptions,
): Promise<(string | null)[]> {
  if (
    !Number.isInteger(options.width) ||
    options.width < 1 ||
    options.width > 32 ||
    !Number.isFinite(options.variation) ||
    options.variation < 0 ||
    options.variation > 1
  )
    throw new Error('Invalid beam options')
  const unary = new Map<string, number>(),
    pair = new Map<string, number>()
  for (const items of candidates.values())
    for (const item of items) unary.set(item.id, profileCost(item.profile, context))
  let beam: State[] = [{ cost: 0, candidate: null, parent: null, recent: [] }]
  for (let i = 0; i < characters.length; i++) {
    options.signal?.throwIfAborted()
    const choices = candidates.get(characters[i]) || [],
      next: State[] = []
    for (const state of beam) {
      if (!choices.length) {
        next.push({
          cost: state.cost,
          candidate: null,
          parent: state,
          recent: state.recent,
        })
        continue
      }
      for (const candidate of choices) {
        let adjacent = 0
        if (state.candidate) {
          const key = JSON.stringify([candidate.id, state.candidate.id])
          if (!pair.has(key))
            pair.set(key, profileCost(candidate.profile, [state.candidate.profile]))
          adjacent = pair.get(key)!
        }
        const repeats = state.recent.filter((c) => c.character === candidate.character)
        const repeatCost =
          choices.length > 1 && repeats.length
            ? repeats.filter((c) => c.id === candidate.id).length / repeats.length
            : 0
        next.push({
          cost:
            state.cost +
            0.65 * unary.get(candidate.id)! +
            0.35 * adjacent +
            options.variation * repeatCost,
          candidate,
          parent: state,
          recent: [...state.recent, candidate].slice(-32),
        })
      }
    }
    next.sort(
      (a, b) => a.cost - b.cost || (a.candidate?.id || '').localeCompare(b.candidate?.id || ''),
    )
    beam = next.slice(0, options.width)
    if (i % 32 === 0) {
      options.progress?.(i + 1)
      await new Promise((r) => setTimeout(r, 0))
    }
  }
  const chosen: (string | null)[] = []
  let node: State | null = beam[0]
  while (node?.parent) {
    chosen.push(node.candidate?.id || null)
    node = node.parent
  }
  options.progress?.(characters.length)
  return chosen.reverse()
}
