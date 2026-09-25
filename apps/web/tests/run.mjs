import { build } from 'esbuild'
import { mkdir } from 'node:fs/promises'
await mkdir('../../work', { recursive: true })
await build({
  entryPoints: ['tests/visual.test.ts'],
  bundle: true,
  platform: 'node',
  format: 'esm',
  outfile: '../../work/visual.test.mjs',
})
await import('../../../work/visual.test.mjs')
