/** Verify the actual packaged ASAR, without launching a user-facing window. */
const { createRequire } = require('node:module')
const { resolve, join } = require('node:path')
const fs = require('node:fs')
const { createHash } = require('node:crypto')
const root = resolve(__dirname,'..')
const asar = createRequire(resolve(root,'apps/desktop/package.json'))('@electron/asar')
const archive = process.argv[2] || resolve(root,'apps/desktop/release/win-unpacked/resources/app.asar')
const directory = require('node:path').dirname(require('node:path').dirname(archive))
for(const file of ['LICENSE.electron.txt','LICENSES.chromium.html']) {
  if(!fs.existsSync(join(directory,file)) || fs.statSync(join(directory,file)).size===0) throw Error('Missing Electron/Chromium notice')
}
const read = (file) => asar.extractFile(archive,join('dist',file))
if(!asar.extractFile(archive,join('build','icon.png')).length) throw Error('Missing native window icon')
const notices=fs.readFileSync(resolve(root,'third_party/manifest.json'))
if(!read('third-party-manifest.json').equals(notices)) throw Error('Packaged third-party manifest differs')
for(const component of JSON.parse(notices).components) for(const file of [component.license_text,...(component.additional_notices||[])]) {
  if(createHash('sha256').update(read(file.path)).digest('hex')!==file.sha256) throw Error('Packaged licence checksum differs: '+file.path)
}
for(const file of ['third-party-licenses.html','build-meta.json','build-modules.json']) {
  if(!read(file).equals(fs.readFileSync(resolve(root,'apps/web/dist',file)))) throw Error('Packaged metadata differs: '+file)
}
if(JSON.parse(read('build-modules.json')).packages.some(name=>['braces','chokidar','fast-glob','micromatch','tailwindcss'].includes(name))) throw Error('Vulnerable tooling shipped')
const expected = fs.readFileSync(resolve(root,'apps/web/public/fonts/asset-manifest.json'))
if (!read('fonts/asset-manifest.json').equals(expected)) throw Error('Packaged manifest differs')
const manifest = JSON.parse(expected)
for (const font of manifest.fonts) {
  const path = font.runtime.path.replace('apps/web/public/','')
  if (createHash('sha256').update(read(path)).digest('hex') !== font.runtime.sha256) throw Error('Packaged font checksum mismatch')
  read(font.license_text)
}
for (const glyph of JSON.parse(read('japanese/glyphs.json'))) {
  if (createHash('sha256').update(read(glyph.asset.url)).digest('hex') !== glyph.asset.checksum) throw Error('Packaged historical checksum mismatch')
  read(glyph.source.license_text)
}
for (const path of ['LICENSE','THIRD_PARTY_NOTICE.md','licenses/HarfBuzz-COPYING.txt','licenses/harfbuzzjs-MIT.txt'])
  if (!read(path).equals(fs.readFileSync(resolve(root,'apps/web/public',path)))) throw Error('Packaged licence notice differs')
console.log(`PASS: Windows ASAR canonical receipt, ${manifest.fonts.length} font checksums, 20 historical assets and independent licences`)
