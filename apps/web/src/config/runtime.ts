export const STATIC_MODE = import.meta.env.VITE_STATIC_MODE === 'true'

export function staticAssetUrl(url: string): string {
  if (!STATIC_MODE || /^(https?:|data:|blob:)/.test(url)) return url
  return `${import.meta.env.BASE_URL}${url.replace(/^\//, '')}`
}
