let exporter: (() => string) | null = null

export function registerStageExporter(next: (() => string) | null) {
  exporter = next
}

export function exportStagePng(): string {
  if (!exporter) throw new Error('Canvas is not ready')
  return exporter()
}