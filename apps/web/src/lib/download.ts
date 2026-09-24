import { Capacitor } from '@capacitor/core'

/** Android WebView does not implement anchor downloads; use the system share sheet. */
export async function saveFile(name: string, blob: Blob): Promise<'shared' | 'downloaded'> {
  const filename = name.replace(/[<>:"/\\|?*\x00-\x1f]/g, '_')
  if (Capacitor.isNativePlatform()) {
    const [{ Filesystem, Directory }, { Share }] = await Promise.all([
      import('@capacitor/filesystem'),
      import('@capacitor/share'),
    ])
    const data = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(String(reader.result).split(',')[1])
      reader.onerror = () => reject(new Error('无法读取导出文件，请重试'))
      reader.readAsDataURL(blob)
    })
    const file = await Filesystem.writeFile({
      path: `exports/${filename}`,
      data,
      directory: Directory.Cache,
      recursive: true,
    })
    await Share.share({ title: filename, files: [file.uri], dialogTitle: '保存或分享作品' })
    return 'shared'
  }
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
  return 'downloaded'
}
