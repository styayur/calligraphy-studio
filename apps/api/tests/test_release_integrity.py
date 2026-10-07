"""Permanent schema/semantic compatibility gates for the 0.7.0 release."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from app.schemas import ProjectDocument
from app.services.candidate_policy import CandidatePolicy
from app.services.font_shaper import FontShaper
from app.providers.codh import CODHKuzushijiProvider

ROOT=Path(__file__).resolve().parents[3]
FIXTURES=ROOT/'tests/fixtures/projects'
NAMES=['legacy-v1-chinese','v2-chinese','v2-japanese-modern','v2-hentaigana','v2-codh-historical','v2-mixed-cjk']


@pytest.mark.parametrize('name',NAMES)
def test_project_semantic_roundtrip(name):
    raw=json.loads((FIXTURES/f'{name}.json').read_text(encoding='utf-8'))
    loaded=ProjectDocument.model_validate(raw)
    saved=loaded.model_dump_json()
    reloaded=ProjectDocument.model_validate_json(saved)
    assert reloaded==loaded and reloaded.version==2
    for before,after in zip(raw['glyphs'],reloaded.model_dump()['glyphs']):
        for field in ['character','variant','metadata','transform','appearance','glyph_id']:
            if field in before:
                for key,value in before[field].items() if isinstance(before[field],dict) else [(None,before[field])]:
                    assert (after[field][key] if key is not None else after[field])==value
        for field in ['identity','source','asset','provenance']:
            for key,value in before.get(field,{}).items():
                if key=='rights':
                    for right,permission in value.items(): assert after[field][key][right]==permission
                else: assert after[field][key]==value
        assert after['identity']['text']==before['character']
    # Export metadata is independent of visual rendering and remains JSON-parseable.
    metadata=json.loads(json.dumps(reloaded.model_dump()))
    assert ProjectDocument.model_validate(metadata)==reloaded
    if name=='v2-hentaigana':
        assert {g.character for g in reloaded.glyphs}=={'あ'}
        assert len({g.variant.id for g in reloaded.glyphs})==2
        assert all(g.variant.type=='hentaigana' for g in reloaded.glyphs)


def test_frozen_schema_v2():
    assert ProjectDocument.model_json_schema()==json.loads((FIXTURES/'schema-v2.json').read_text(encoding='utf-8'))


def test_api_project_persistence_all_fixtures(client):
    for name in NAMES:
        raw=json.loads((FIXTURES/f'{name}.json').read_text(encoding='utf-8'))
        response=client.post('/api/projects',json={'name':name,'document':raw})
        assert response.status_code==201,response.text
        item=response.json()
        fetched=client.get('/api/projects/'+item['id'])
        assert fetched.status_code==200
        assert fetched.json()['document']==item['document']
        saved=client.put('/api/projects/'+item['id'],json={'document':fetched.json()['document']})
        assert saved.status_code==200 and saved.json()['document']==item['document']


@pytest.mark.parametrize('tradition',['Chinese','Japanese'])
@pytest.mark.parametrize('mode',['strict','related','cross-tradition'])
def test_cjk_candidate_identity(tradition,mode):
    project=ProjectDocument.model_validate_json((FIXTURES/'v2-mixed-cjk.json').read_text(encoding='utf-8'))
    selected=[]
    for g in project.glyphs:
        proxy=SimpleNamespace(writing_tradition=g.source.writing_tradition,locale=g.source.locale,script=g.source.script,variant_type=g.variant.type,orthography=g.source.orthography)
        if CandidatePolicy(tradition=tradition,mode=mode).accepts(proxy): selected.append(g)
    assert len(selected)==(6 if mode=='cross-tradition' else 3)
    if mode!='cross-tradition': assert all(g.source.writing_tradition==tradition for g in selected)


@pytest.mark.parametrize('font',['yuji-syuku','yuji-mai','yuji-boku','yuji-akari','yuji-akebono'])
def test_shaping_plan_determinism(font):
    manifest=ROOT/'samples/fonts/japanese/manifest.json'
    entry=next(e for e in json.loads(manifest.read_text(encoding='utf-8'))['fonts'] if e['id']==font)
    path=manifest.parent/entry['path']
    shaper=FontShaper(path)
    for text in ['あ','か\u3099']:
        for vertical in [False,True]:
            options=dict(locale='ja-JP',script='Hiragana',vertical=vertical,features={'locl':1})
            a=shaper.shape(text,**options)
            b=FontShaper(path).shape(text,**options)
            assert a and b
            assert a[1]==b[1]
            assert a[1]['font_glyph_ids'] and a[1]['glyph_names']
            assert all(i>0 for i in a[1]['font_glyph_ids'])
            assert a[1]['source_sequence']==text
    assert shaper.shape('😀',locale='ja-JP') is None


def test_cross_runtime_export_metadata():
    path=FIXTURES/'expected-attribution.json'
    exported=json.loads(path.read_text(encoding='utf-8'))
    for name in NAMES:
        project=ProjectDocument.model_validate_json((FIXTURES/f'{name}.json').read_text(encoding='utf-8'))
        for glyph,record in zip(project.glyphs,exported[name]['glyphs']):
            assert record['character']==glyph.character
            for field in ['identity','variant','source','provenance']:
                actual=getattr(glyph,field).model_dump()
                for key,value in record[field].items(): assert actual[key]==value
            assert record['asset_checksum']==glyph.asset.checksum
            assert record['metadata']==glyph.metadata
