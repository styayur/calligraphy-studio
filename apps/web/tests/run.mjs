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
await build({ entryPoints: ['tests/eastAsian.test.ts'], bundle:true, platform:'node',format:'esm',outfile:'../../work/eastAsian.test.mjs' })
await import('../../../work/eastAsian.test.mjs')
await build({ entryPoints:['tests/releaseIntegrity.test.ts'],bundle:true,platform:'node',format:'esm',outfile:'../../work/releaseIntegrity.test.mjs' })
await import('../../../work/releaseIntegrity.test.mjs')
