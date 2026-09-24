export interface ExportOptions {
  scale: number
  transparent: boolean
}
let exporter: ((options: ExportOptions) => string) | null = null

export function registerStageExporter(next: ((options: ExportOptions) => string) | null) {
  exporter = next
}

export function exportStagePng(options: ExportOptions = { scale: 1, transparent: false }): string {
  if (!exporter) throw new Error('画布尚未准备好，请稍后重试')
  return exporter(options)
}
