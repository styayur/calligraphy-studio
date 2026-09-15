import { useEffect, useState } from 'react'

export function useHtmlImage(url: string): HTMLImageElement | null {
  const [image, setImage] = useState<HTMLImageElement | null>(null)

  useEffect(() => {
    let active = true
    const next = new window.Image()
    next.crossOrigin = 'anonymous'
    next.onload = () => {
      if (active) setImage(next)
    }
    next.onerror = () => {
      if (active) setImage(null)
    }
    next.src = url
    return () => {
      active = false
    }
  }, [url])

  return image
}