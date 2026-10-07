import assert from 'node:assert/strict'
import { codepoints, migrateGlyph, textCharacters } from '../src/lib/identity'
import { candidateCompatible, candidateCost, CANDIDATE_WEIGHTS } from '../src/lib/candidatePolicy'
import { validateProject } from '../src/lib/project'
import { assertExportRights, attributionManifest } from '../src/lib/rights'
import { layoutText, textLines } from '../src/lib/composition'
import { paginateRoll, zipFiles } from '../src/lib/longRoll'
import type { Glyph, GlyphInstance } from '../src/types'
import { extractVisualProfile } from '../src/lib/visual'
import { selectSequence } from '../src/lib/beam'
import { japaneseVariant } from '../src/lib/orthography'

const glyph = (tradition: string, locale: string, variant = 'regional'): Glyph => ({
  id:`${tradition}:${variant}`,character:'骨',source:{dataset:'test',writing_tradition:tradition,locale,script:'Han',rights:{commercial_use:true,redistribution_allowed:true,derivatives_allowed:true}},
  variant:{id:variant,type:variant as 'regional'},asset:{type:'raster',url:'data:image/png;base64,eA==',width:32,height:32,bbox:[0,0,32,32]},
  transform:{x:0,y:0,scaleX:1,scaleY:1,rotation:0,skewX:0,skewY:0},appearance:{opacity:1,blendMode:'multiply'},provenance:{type:'font'},
})
const ja = glyph('Japanese','ja-JP'), zh = glyph('Chinese','zh-Hant'), policy = { writing_tradition:'Japanese',locale:'ja-JP',mode:'strict' as const }
assert.equal(candidateCompatible(ja,policy),true)
assert.equal(candidateCompatible(zh,policy),false)
assert.equal(candidateCompatible(zh,{ ...policy,mode:'related' }),false)
assert.equal(candidateCompatible(zh,{ ...policy,mode:'cross-tradition' }),true)
assert.equal(candidateCompatible({ ...ja,source:{ ...ja.source,writing_tradition:null } },policy),false)
assert.equal(candidateCost(zh,0,policy),Infinity)
const yuji = { ...ja,id:'yuji',source:{ ...ja.source,work:'Yuji Syuku',source_role:'calligraphy' as const } }
const klee = { ...ja,id:'klee',source:{ ...ja.source,work:'Klee One',source_role:'handwriting' as const } }
const coverage = { ...ja,id:'coverage',source:{ ...ja.source,work:'JP Coverage Serif',source_role:'coverage-fallback' as const,license:'OFL-1.1',source_checksum:'b'.repeat(64) } }
assert.equal(candidateCompatible(coverage,policy),true)
assert.ok(candidateCost(coverage,0,policy) > candidateCost(yuji,1,policy))
assert.ok(candidateCost(coverage,0,policy) > candidateCost(klee,1,policy))
assert.equal(candidateCompatible({...coverage,source:{...coverage.source,writing_tradition:'Chinese'}},policy),false)
const exportedCoverage = attributionManifest([coverage])
assert.equal(exportedCoverage.glyphs[0].source.source_role,'coverage-fallback')
assert.equal(exportedCoverage.glyphs[0].source.license,'OFL-1.1')
assert.ok(candidateCost(ja,.2,{ ...policy,mode:'cross-tradition' }) < candidateCost(zh,.2,{ ...policy,mode:'cross-tradition' }))
assert.throws(() => candidateCost(ja,0,policy,[],0,{ ...CANDIDATE_WEIGHTS,visual:-1 }))
const henta = glyph('Japanese','ja-JP','hentaigana')
assert.equal(candidateCompatible(henta,policy),false)
assert.equal(candidateCompatible(henta,{ ...policy,variant_type:'hentaigana' }),true)
assert.equal(candidateCompatible(henta,{ ...policy,mode:'related' }),true)
assert.equal(japaneseVariant('あ','hentaigana').type,'hentaigana')
assert.equal(japaneseVariant('体','hentaigana').type,'font-alternate')
assert.equal(candidateCompatible({...ja,source:{...ja.source,orthography:'historical-kana'}},policy),false)
assert.deepEqual(codepoints('か\u3099'),['U+304B','U+3099'])
assert.deepEqual(codepoints('𛀁'),['U+1B001'])
assert.deepEqual(textCharacters('か\u3099骨\u{E0100}'),['か\u3099','骨\u{E0100}'])
assert.deepEqual(textLines('「かな」、カナ。',true).flat(),[...'「かな」、カナ。'])
assert.deepEqual(textLines('「かな」、カナ。',false).flat(),[...'かなカナ'])
const options = { layout:'vertical-rtl' as const,columns:3,size:100,gap:0,margin:20,punctuation:true }
const layout = layoutText('日本語\nあいう',options)
assert.equal(layout.positions.length,6)
assert.ok(layout.positions[0].x > layout.positions[3].x)
assert.ok(layout.positions[0].y < layout.positions[1].y)
assert.equal(paginateRoll('かな'.repeat(10000),{rows:12,columns:8,vertical:true,punctuation:true}).flatMap((p) => p.slots).length,20000)
const instance: GlyphInstance = { ...zh,glyph_id:zh.id }
const old = { version:1 as const,canvas:{width:400,height:400,background:'#ffffff'},glyphs:[instance],text:'骨' }
const migrated = validateProject(old)
assert.equal(migrated.version,2)
assert.deepEqual(migrated.glyphs[0].identity?.codepoints,['U+9AA8'])
assert.equal(migrated.glyphs[0].identity?.language,undefined)
assert.deepEqual(validateProject(migrated),migrated)
assert.equal(migrateGlyph(ja).source.rights?.share_alike_required,null)
assert.throws(() => validateProject({ ...old,glyphs:[{ ...instance,identity:{text:'骨',codepoints:['U+570B']} }] }))
assert.throws(() => validateProject({ ...old,glyphs:[{ ...instance,source:{...instance.source,rights:{commercial_use:'true'}} }] }))
const original: Glyph = { ...ja,provenance:{type:'original'},source:{ ...ja.source,rights:{ ...ja.source.rights,font_license:false,derivatives_allowed:false } } }
assert.throws(() => assertExportRights([original]))
const nc = { ...ja,source:{ ...ja.source,rights:{commercial_use:false} } }
assert.throws(() => assertExportRights([nc],{commercialOnly:true}))
assert.equal(candidateCompatible(nc,{commercial_only:true}),false)
assert.throws(() => assertExportRights([{ ...ja,source:{ ...ja.source,rights:{} } }],{commercialOnly:true}))
assert.throws(() => assertExportRights([{ ...ja,source:{ ...ja.source,rights:{redistribution_allowed:false} } }]))
const sa = { ...ja,source:{ ...ja.source,rights:{ ...ja.source.rights,share_alike_required:true },license:'CC-BY-SA-4.0',attribution:'CODH DOI',source_checksum:'a'.repeat(64) } }
const attribution = attributionManifest([sa])
assert.equal(attribution.artwork_license,'CC-BY-SA-4.0')
assert.equal(attribution.glyphs[0].source.rights?.share_alike_required,true)
assert.equal(attribution.glyphs[0].source.attribution,'CODH DOI')
assert.equal(attribution.glyphs[0].source.source_checksum,'a'.repeat(64))
assert.equal(zipFiles([{name:'attribution.json',data:new TextEncoder().encode(JSON.stringify(attribution))}]).type,'application/zip')
const profile = extractVisualProfile(Float32Array.from({length:4096},(_,i) => i%64 > 20 && i%64 < 40 ? 1 : 0))
const choices = new Map([['骨',[{id:zh.id,character:'骨',profile,glyph:zh},{id:ja.id,character:'骨',profile,glyph:ja}]]])
assert.deepEqual(await selectSequence(['骨','骨'],choices,[],{width:4,variation:.2,policy}),[ja.id,ja.id])
console.log('PASS: CJK separation, cross-tradition opt-in, hentaigana, graphemes, migration, Japanese layout, rights, share-alike and policy beam')
