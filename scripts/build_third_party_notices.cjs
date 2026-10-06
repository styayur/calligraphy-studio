/** Canonical machine-readable notices, derived from asset receipts and locked npm packages. */
const fs = require('node:fs')
const path = require('node:path')
const crypto = require('node:crypto')
const root = path.resolve(__dirname,'..'), publicDir = path.join(root,'apps/web/public')
const check = process.argv.includes('--check')
const readJson = (file) => JSON.parse(fs.readFileSync(path.join(root,file),'utf8'))
const hash = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex')
const components = [], requiredFiles = new Map()
function license(source,target) {
  // Preserve licence wording while making receipts stable across LF/CRLF checkouts.
  const bytes=Buffer.from(fs.readFileSync(path.join(root,source),'utf8').replace(/\r\n/g,'\n'))
  requiredFiles.set(target,bytes)
  return { path:target,sha256:hash(bytes) }
}
function add(id,name,category,version,source,licenseId,sourceText,target,notes='') {
  components.push({id,name,category,version,source_uri:source,license:licenseId,license_text:license(sourceText,target),notes})
}
add('application','Calligraphy Studio','application',readJson('apps/web/package.json').version,'https://github.com/styayur/calligraphy-studio','MIT','LICENSE','LICENSE','Code licence; third-party assets retain their own licences.')
for (const font of readJson('apps/web/public/fonts/asset-manifest.json').fonts) {
  const catalog=readJson('apps/web/public/fonts/catalog.json').find(f=>f.id===font.id)
  add(font.id,catalog.family,'font',catalog.font_version||null,font.source_uri,font.license,'apps/web/public/'+font.license_text,font.license_text,
      `${catalog.designer}; font provenance, not manuscript originals. ${catalog.attribution||''}`)
}
add('codh','CODH Kuzushiji sample','historical','v2 (2019-11-11)','https://codh.rois.ac.jp/char-shape/','CC-BY-SA-4.0','third_party/japanese/codh/CC-BY-SA-4.0.txt','japanese/licenses/CC-BY-SA-4.0.txt','20 crops and ink-mask derivatives; 日本古典籍くずし字データセット (国文研所蔵／CODH加工), DOI 10.20676/00000340. Changes and original checksums are in japanese/glyphs.json. Not MIT.')
add('nccu','NCCU Cursive Chinese Calligraphy Dataset','historical',null,'https://github.com/nccuviplab/CursiveChineseCalligraphyDataset','MIT','samples/cursive/raw/LICENSE','demo/licenses/nccu-mit.txt','VIPLab, National Chengchi University; bundled Test subset.')
add('arphic','Hanzi Writer / Make Me A Hanzi / Arphic','structural',null,'https://github.com/chanind/hanzi-writer-data','ARPHIC-PUBLIC-LICENSE','third_party/hanzi-writer/ARPHICPL.TXT','demo/licenses/arphic-public-license.txt','Modified structural SVGs retain Arphic licence/notice obligations; fallback provenance.')
add('demo','Synthetic demonstration glyphs','fixture',null,'https://github.com/styayur/calligraphy-studio','CC0-1.0','third_party/CC0-1.0.txt','demo/licenses/CC0-1.0.txt','Synthetic examples, not historical manuscripts.')
add('harfbuzz','HarfBuzz WASM engine','software','863d3f7787c6df18d20e4535c5906bf3eb803bd5','https://github.com/harfbuzz/harfbuzz','Old-MIT','third_party/harfbuzz/HarfBuzz-COPYING.txt','licenses/HarfBuzz-COPYING.txt')
add('android-native','AndroidX / Kotlin / Cordova native dependencies','native',null,'https://source.android.com/docs/setup/about/licenses','Apache-2.0','third_party/native-APACHE-2.0.txt','licenses/android-native-Apache-2.0.txt','AndroidX copyright The Android Open Source Project; Kotlin copyright JetBrains; Cordova copyright The Apache Software Foundation. Exact resolved native versions are recorded in the Android build dependency report. Capacitor MIT licences are included below.')
const apacheNative=components.at(-1)
apacheNative.additional_notices=[license('third_party/Cordova-NOTICE.txt','licenses/Cordova-NOTICE.txt')]
apacheNative.resolved_dependencies=[]
const nativeCoordinates=fs.readFileSync(path.join(root,'apps/web/android/app/gradle.lockfile'),'utf8').split(/\r?\n/).filter(l=>l.endsWith('=releaseRuntimeClasspath')).map(l=>l.split('=')[0])
for(const coordinate of nativeCoordinates) {
  if(coordinate.startsWith('io.ionic.libs:ionfilesystem-android:')) {
    add('ionic-native','Ionic Android filesystem','native',coordinate.split(':')[2],'https://github.com/ionic-team/ion-android-filesystem','MIT','third_party/Ionic-filesystem-MIT.txt','licenses/Ionic-filesystem-MIT.txt','Copyright 2025 Ionic. Licence verified against the official repository and resolved Maven POM.')
    components.at(-1).resolved_dependencies=[coordinate]
  } else {
    if(!/^(androidx\.|org\.jetbrains(?:\.|:)|org\.apache\.cordova:|org\.jspecify:|com\.google\.guava:listenablefuture:)/.test(coordinate)) throw Error('Unreviewed native dependency: '+coordinate)
    apacheNative.resolved_dependencies.push(coordinate)
  }
}
apacheNative.notes+=' Locked coordinates: '+apacheNative.resolved_dependencies.join(', ')+'. Cordova NOTICE is preserved separately.'
const lock=readJson('apps/web/package-lock.json')
for (const [relative,entry] of Object.entries(lock.packages).sort()) {
  if (!relative || entry.dev) continue
  const dir=path.join(root,'apps/web',relative), name=entry.name || relative.split('node_modules/').at(-1)
  const texts=fs.readdirSync(dir).filter(f=>/^(licen[sc]e|copying|notice)([.-]|$)/i.test(f) && fs.statSync(path.join(dir,f)).isFile()).sort()
  if (!texts.length) throw Error(`Missing licence text for ${name}`)
  const files=texts.map(f=>license(`apps/web/${relative}/${f}`,`licenses/npm/${name.replace(/[^\w.-]/g,'_')}/${f}`))
  components.push({id:'npm:'+name,name,category:'locked-production-dependency',version:entry.version,source_uri:'https://www.npmjs.com/package/'+name,license:entry.license,license_text:files[0],additional_notices:files.slice(1),notes:'Includes installed production dependency notices; some type-only entries are not emitted in renderer code.'})
}
const manifest={schema_version:1,version:readJson('apps/web/package.json').version,components}
const manifestText=JSON.stringify(manifest,null,2)+'\n'
const notice=['# Third-party notices','', 'Generated by `scripts/build_third_party_notices.cjs` from canonical asset receipts and locked dependency licence texts. Do not edit generated copies.','',
  'The application code is MIT. Fonts, historical crops, structural data and software below retain independent licences. Font glyphs are not manuscripts; CODH adaptations remain CC BY-SA 4.0. Unknown period/author/language is not inferred.','',
  ...components.flatMap(c=>[`## ${c.name}${c.version?' · '+c.version:''}`,'',`Licence: **${c.license}**. Source: ${c.source_uri}.`,``,`Bundled text: \`${c.license_text.path}\` (SHA-256 \`${c.license_text.sha256}\`).`,c.notes,'']),
  'Electron distributions additionally retain LICENSE.electron.txt and LICENSES.chromium.html alongside the executable. The optional Python API obtains dependency notices through its installed distributions. No non-commercial font, MCCD, full CODH corpus, KMNIST or unofficial mirror is bundled.',''].map(line=>line.trimEnd()).join('\n')
function output(file,bytes) {
  const target=path.join(root,file)
  if(check) { if(!fs.existsSync(target)||!fs.readFileSync(target).equals(Buffer.from(bytes))) throw Error(`Stale generated notice: ${file}`) }
  else { fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,bytes) }
}
for(const [file,bytes] of requiredFiles) output('apps/web/public/'+file,bytes)
output('third_party/manifest.json',manifestText)
output('apps/web/public/third-party-manifest.json',manifestText)
output('third_party/NOTICE.md',notice)
output('apps/web/public/THIRD_PARTY_NOTICE.md',notice)
// Plain HTML makes licence texts accessible inside app:// and Capacitor, without external navigation.
const escape=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')
const uniqueTexts=new Map([...requiredFiles].map(([file,bytes])=>[hash(bytes),{file,bytes}]))
output('apps/web/public/third-party-licenses.html','<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Third-party licences · Calligraphy Studio</title><style>body{font:16px system-ui;margin:2rem;max-width:70rem}pre{white-space:pre-wrap}summary{cursor:pointer}</style></head><body><h1>Third-party licences</h1><p>MIT application code does not relicense fonts or historical assets.</p>'+components.map(c=>`<details><summary>${escape(c.name)} · ${escape(c.license)}</summary><p>${escape(c.notes)}</p><p>${[c.license_text,...(c.additional_notices||[])].map(f=>`<a href="#license-${f.sha256}">${escape(f.path)}</a>`).join(' · ')}</p></details>`).join('')+[...uniqueTexts].map(([sha,{file,bytes}])=>`<section id="license-${sha}"><h2>${escape(file)}</h2><pre>${escape(bytes.toString())}</pre></section>`).join('')+'</body></html>\n')
console.log(`PASS: ${components.length} canonical components, ${requiredFiles.size} licence files; ${check?'generated notices checked':'notices generated'}`)
