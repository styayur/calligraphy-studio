import { extractVisualProfile } from './visual'
self.onmessage = (event: MessageEvent<{ id: number; ink: Float32Array }>) => {
  try {
    self.postMessage({
      id: event.data.id,
      profile: extractVisualProfile(event.data.ink),
    })
  } catch (error) {
    self.postMessage({ id: event.data.id, error: String(error) })
  }
}
