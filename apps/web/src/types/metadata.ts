export interface MetadataItem {
  id: number
  name: string
}

export interface MetadataResponse {
  calligraphers: MetadataItem[]
  styles: MetadataItem[]
  dynasties: MetadataItem[]
  datasets: string[]
}