from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, text
from PIL import Image

from app.database import Base, Database
from app.domain import CharacterIdentity, RightsRecord, require_rights, unicode_script
from app.models import Glyph, GlyphSource, Project
from app.providers.base import DatasetProvider, RawGlyphRecord
from app.providers.codh import CODHKuzushijiProvider, validate_archive, safe_local
from app.providers.font_manifest import FontManifestProvider
from app.schemas import ProjectDocument
from app.services.asset_store import AssetStore
from app.services.candidate_policy import CandidatePolicy, candidate_cost
from app.services.font_shaper import FontShaper
from app.services.glyph_importer import GlyphImporter
from app.services.glyph_service import GlyphService
from app.utils.image_meta import inspect_asset_bytes

ROOT = Path(__file__).resolve().parents[3]
JP = ROOT / 'samples/fonts/japanese/manifest.json'
SAMPLE = ROOT / 'samples/japanese/historical/sample/manifest.json'


def test_semantic_identity_and_unknown_rights():
    assert CharacterIdentity(text='か\u3099').codepoints == ['U+304B','U+3099']
    assert CharacterIdentity(text='𛀁').codepoints == ['U+1B001']
    assert unicode_script('𛀀') == 'Katakana'
    assert unicode_script('𛀁') == 'Hiragana'
    assert CharacterIdentity(text='骨').language is None
    with pytest.raises(ValueError):
        CharacterIdentity(text='国',codepoints=['U+570B'])
    assert RightsRecord().commercial_use is None
    assert RightsRecord().share_alike_required is None
    with pytest.raises(ValueError):
        RightsRecord(commercial_use='true')


def test_pinned_japanese_font_provenance_and_hentaigana():
    entries = json.loads(JP.read_text(encoding='utf-8'))['fonts']
    assert len(entries) == 5
    for e in entries:
        assert hashlib.sha256((JP.parent / e['path']).read_bytes()).hexdigest() == e['sha256']
        assert e['upstream_commit'] == 'efec977b14b57c19eb85d468edcfbbad13139e67'
        assert e['font_version'] == 'Version 3.002'
        assert e['rights']['redistribution_allowed'] is True
    records = list(FontManifestProvider(JP, characters={'あ'}).iter_records())
    assert len(records) == 5
    assert len({r.variant['id'] for r in records}) == 5
    assert all(r.identity['text'] == 'あ' and r.identity['locale'] == 'ja-JP' for r in records)
    historical_kana = [r for r in records if r.variant['type'] == 'hentaigana']
    assert len(historical_kana) == 2
    assert all(r.provenance_type == 'font' for r in records)
    assert all(r.metadata['shaping']['font_glyph_ids'] for r in records)


def test_deterministic_harfbuzz_and_vertical_japanese():
    shaper = FontShaper(JP.parent / 'yuji/YujiMai-Regular.ttf')
    for sequence in ['日本', 'か\u3099', 'カ', '。', '「', 'ー', '骨']:
        a = shaper.render(sequence,locale='ja-JP',vertical=True)
        b = shaper.render(sequence,locale='ja-JP',vertical=True)
        assert a and a == b
        assert a[1]['features']['vert'] == 1
        assert a[1]['direction'] == 'ttb'
        assert Image.open(io.BytesIO(a[0])).getchannel('A').getbbox()
    horizontal = shaper.shape('「',locale='ja-JP')[1]
    vertical = shaper.shape('「',locale='ja-JP',vertical=True)[1]
    assert horizontal['font_glyph_ids'] != vertical['font_glyph_ids']
    assert shaper.shape('😀',locale='ja-JP') is None


def test_regional_filtering_and_explicit_cross_tradition():
    zh = SimpleNamespace(writing_tradition='Chinese',locale='zh-Hant',script='Han',period=None,variant_type='regional',source=SimpleNamespace(work='Chinese font'))
    ja = SimpleNamespace(writing_tradition='Japanese',locale='ja-JP',script='Han',period=None,variant_type='regional',source=SimpleNamespace(work='Yuji'))
    unknown = SimpleNamespace(**{**vars(zh),'writing_tradition':None,'locale':None})
    strict = CandidatePolicy(tradition='Japanese',locale='ja-JP')
    assert strict.accepts(ja)
    assert not strict.accepts(zh) and not strict.accepts(unknown)
    assert not CandidatePolicy(tradition='Japanese',mode='related').accepts(zh)
    assert CandidatePolicy(tradition='Japanese',mode='cross-tradition').accepts(zh)
    assert candidate_cost(zh,0,strict) == float('inf')
    cross = CandidatePolicy(tradition='Japanese',locale='ja-JP',mode='cross-tradition')
    assert candidate_cost(ja,.2,cross) < candidate_cost(zh,.2,cross)
    with pytest.raises(ValueError):
        candidate_cost(ja,0,cross,weights={'visual':-1})


def test_codh_metadata_and_share_alike(tmp_path):
    provider = CODHKuzushijiProvider(SAMPLE)
    records = list(provider.iter_records())
    assert len(records) == 20
    assert all(r.metadata['source_bbox'] and r.metadata['page'] for r in records)
    assert all(r.culture['language'] is None and r.culture['period'] is None for r in records)
    assert all(r.rights['share_alike_required'] and r.license == 'CC-BY-SA-4.0' for r in records)
    database = Database(f'sqlite:///{(tmp_path / "corpus.db").as_posix()}'); database.create_schema()
    importer = GlyphImporter(AssetStore(tmp_path/'assets'),database)
    result = importer.import_provider(provider)
    assert result.imported == 20 and result.failed == 0
    assert importer.import_provider(provider).skipped == 20
    with database.session() as session:
        page = GlyphService().list(session,writing_tradition='Japanese',provenance_type='original',limit=2)
        assert page.total == 20 and len(page.items) == 2
        glyph = page.items[0]
        assert glyph.identity and glyph.variant.id
        assert glyph.source.rights['share_alike_required'] is True
        assert glyph.source.attribution and '10.20676/00000340' in glyph.source.attribution
        assert glyph.asset.checksum and glyph.source.source_checksum
        assert glyph.metadata['source_bbox']
    with pytest.raises(InterruptedError):
        list(CODHKuzushijiProvider(SAMPLE,cancelled=lambda:True).iter_records())


def test_duplicate_unicode_and_same_image_variants(tmp_path):
    png = io.BytesIO(); Image.new('RGBA',(32,32),'black').save(png,format='PNG')
    class Variants(DatasetProvider):
        name = 'test-variants'
        def iter_records(self):
            for locale,tradition,variant in [('ja-JP','Japanese','a'),('ja-JP','Japanese','b'),('zh-Hant','Chinese','a')]:
                yield RawGlyphRecord(character='骨',dataset='same-source',asset_bytes=png.getvalue(),original_filename='ink.png',
                                     identity={'text':'骨','locale':locale},culture={'locale':locale,'writing_tradition':tradition,'script':'Han'},variant={'id':variant,'type':'regional'})
    database = Database(f'sqlite:///{(tmp_path/"variants.db").as_posix()}'); database.create_schema()
    importer = GlyphImporter(AssetStore(tmp_path/'assets'),database)
    assert importer.import_provider(Variants()).imported == 3
    assert importer.import_provider(Variants()).skipped == 3
    with database.session() as session:
        assert GlyphService().list(session,character='骨',writing_tradition='Japanese').total == 2
        assert GlyphService().list(session,character='骨',writing_tradition='Japanese',mode='cross-tradition').total == 3
        assert GlyphService().list(session,commercial_only=True).total == 0


def test_api_japanese_batch_graphemes_and_vertical_assets(client):
    response = client.post('/api/compose/batch',json={'text':'か\u3099。骨骨\nカあ','layout':'vertical-rtl','writing_tradition':'Japanese','locale':'ja-JP','dataset':'Yuji Japanese Fonts','commercial_only':True})
    assert response.status_code == 200, response.text
    result = response.json()
    assert result['total_characters'] == result['resolved_characters'] == 6 and not result['missing']
    glyphs = [p['glyph'] for p in result['placements']]
    assert glyphs[0]['identity']['text'] == 'か\u3099'
    assert all(g['source']['writing_tradition'] == 'Japanese' and g['metadata']['shaping']['direction'] == 'ttb' for g in glyphs)
    assert glyphs[2]['variant']['id'] == glyphs[3]['variant']['id']
    assert glyphs[2]['asset']['checksum'] == glyphs[3]['asset']['checksum']
    assert glyphs[0]['transform']['x'] > glyphs[4]['transform']['x']
    for g in glyphs:
        assert client.get(g['asset']['url']).status_code == 200
    horizontal = client.post('/api/compose/batch',json={'text':'。','layout':'horizontal-ltr','writing_tradition':'Japanese','dataset':'Yuji Japanese Fonts'}).json()
    assert horizontal['placements'][0]['glyph']['metadata']['shaping']['direction'] == 'ltr'


def test_reject_tampered_historical_manifest(tmp_path):
    payload = json.loads(SAMPLE.read_text(encoding='utf-8'))
    payload['assets'] = [{**payload['assets'][0], 'file':'crop.jpg','rights':{'redistribution_allowed':True,'share_alike_required':False}}]
    (tmp_path/'crop.jpg').write_bytes((SAMPLE.parent / json.loads(SAMPLE.read_text(encoding='utf-8'))['assets'][0]['file']).read_bytes())
    manifest = tmp_path/'manifest.json'; manifest.write_text(json.dumps(payload),encoding='utf-8')
    with pytest.raises(ValueError,match='obligations'):
        list(CODHKuzushijiProvider(manifest).iter_records())
    payload['schema_version'] = 3; manifest.write_text(json.dumps(payload),encoding='utf-8')
    with pytest.raises(ValueError): CODHKuzushijiProvider(manifest)


def test_api_rejects_nd_adaptation_and_excludes_nc(client):
    png=io.BytesIO(); Image.new('RGBA',(32,32),'black').save(png,format='PNG')
    class Restricted(DatasetProvider):
        name='restricted-test'
        def iter_records(self):
            yield RawGlyphRecord(character='あ',dataset='Restricted',asset_bytes=png.getvalue(),original_filename='crop.png',
                                 culture={'writing_tradition':'Japanese','script':'Hiragana'},license='CC-BY-NC-ND-4.0',
                                 rights={'commercial_use':False,'derivatives_allowed':False,'redistribution_allowed':False})
    settings=client.app.state.settings
    assert GlyphImporter(AssetStore(settings.assets_dir),client.app.state.db).import_provider(Restricted()).imported == 1
    payload={'text':'あ','dataset':'Restricted','writing_tradition':'Japanese','use_structural_fallback':False}
    denied=client.post('/api/compose/batch',json=payload)
    assert denied.status_code == 422 and 'derivatives_allowed' in denied.json()['detail']
    commercial=client.post('/api/compose/batch',json={**payload,'commercial_only':True})
    assert commercial.status_code == 200 and commercial.json()['missing'] == ['あ']


def test_legacy_database_and_project_migration(tmp_path):
    path = tmp_path/'legacy.db'; engine = create_engine(f'sqlite:///{path.as_posix()}')
    Base.metadata.create_all(engine,tables=[t for t in Base.metadata.sorted_tables if t.name not in ['glyphs','glyph_embeddings']])
    with engine.begin() as c:
        c.exec_driver_sql('''CREATE TABLE glyphs (id VARCHAR(36) PRIMARY KEY, character VARCHAR(16) NOT NULL,
            calligrapher_id INTEGER, style_id INTEGER, dynasty_id INTEGER, source_id INTEGER NOT NULL REFERENCES glyph_sources(id),
            asset_url VARCHAR(1000) NOT NULL, asset_type VARCHAR(24) NOT NULL, width INTEGER NOT NULL, height INTEGER NOT NULL,
            bbox JSON NOT NULL, checksum VARCHAR(64) NOT NULL, original_filename VARCHAR(500), provenance_type VARCHAR(24) NOT NULL,
            confidence FLOAT, created_at DATETIME NOT NULL, metadata JSON NOT NULL,
            CONSTRAINT uq_glyph_identity UNIQUE (character,source_id,checksum))''')
        c.exec_driver_sql("INSERT INTO glyph_sources (id,dataset,rights,created_at) VALUES (1,'legacy','{}','2026-01-01')")
        c.exec_driver_sql("INSERT INTO glyph_sources (id,dataset,rights,created_at) VALUES (2,'OFL Calligraphy Fonts','{}','2026-01-01')")
        c.execute(text("INSERT INTO glyphs VALUES ('old','骨',NULL,NULL,NULL,1,'/assets/old.png','raster',32,32,'[0,0,32,32]',:checksum,NULL,'original',NULL,'2026-01-01','{}')"),{'checksum':'a'*64})
        c.execute(text("INSERT INTO glyphs VALUES ('old-font','骨',NULL,NULL,NULL,2,'/assets/old.png','raster',32,32,'[0,0,32,32]',:checksum,NULL,'font',NULL,'2026-01-01','{}')"),{'checksum':'a'*64})
    Base.metadata.tables['glyph_embeddings'].create(engine)
    with engine.begin() as c:
        c.execute(text("INSERT INTO glyph_embeddings (id,glyph_id,model_name,dimension,vector,norm,source_checksum,created_at) VALUES (1,'old','test',1,:vector,1,:checksum,'2026-01-01')"),{'vector':b'\0'*4,'checksum':'a'*64})
    engine.dispose()
    database = Database(f'sqlite:///{path.as_posix()}')
    database.create_schema(); database.create_schema()
    with database.session() as session:
        glyph = GlyphService().get(session,'old')
        assert glyph and glyph.identity.text == '骨' and glyph.identity.locale is None
        assert glyph.source.writing_tradition is None
        known_font = GlyphService().get(session,'old-font')
        assert known_font.source.writing_tradition == 'Chinese' and known_font.identity.language == 'zh'
        assert known_font.source.locale is None
        assert session.execute(text('PRAGMA foreign_key_check')).all() == []
        assert session.scalar(text("SELECT glyph_id FROM glyph_embeddings")) == 'old'
        assert session.scalar(text('SELECT version FROM schema_version')) == 2
        project = ProjectDocument.model_validate({'version':1,'canvas':{'width':400,'height':400},'glyphs':[{**glyph.model_dump(),'glyph_id':'old'}]})
        assert project.version == 2 and project.glyphs[0].identity.codepoints == ['U+9AA8']
        assert ProjectDocument.model_validate(project.model_dump()) == project


@pytest.mark.parametrize('rights,policy',[({'redistribution_allowed':False},{'bundle':True}), ({'redistribution_allowed':None},{'bundle':True}), ({'commercial_use':False},{'commercial':True}), ({'commercial_use':None},{'commercial':True}), ({'derivatives_allowed':False},{'derivative':True})])
def test_rights_enforcement(rights,policy):
    with pytest.raises(ValueError): require_rights(rights,**policy)


@pytest.mark.parametrize('filename',['../escape.jpg','/escape.jpg','C:/escape.jpg','a\\b.jpg'])
def test_archive_path_security(tmp_path,filename):
    with pytest.raises(ValueError): safe_local(tmp_path,filename)
    b=io.BytesIO()
    info = zipfile.ZipInfo('placeholder.jpg')
    info.filename = filename  # Do not let Windows' ZipInfo constructor normalise the hostile path.
    with zipfile.ZipFile(b,'w') as archive: archive.writestr(info,b'x')
    with zipfile.ZipFile(b) as archive:
        with pytest.raises(ValueError): validate_archive(archive)


def test_untrusted_svg_and_bad_images():
    for data in [b'<svg viewBox="0 0 1 1"><script/></svg>',b'<svg viewBox="0 0 1 1"><path onclick="evil()"/></svg>',b'not an image']:
        with pytest.raises(ValueError): inspect_asset_bytes(data)


def test_future_database_schema_rejected(tmp_path):
    database = Database(f'sqlite:///{(tmp_path/"future.db").as_posix()}'); database.create_schema()
    with database.engine.begin() as c: c.exec_driver_sql('UPDATE schema_version SET version=3')
    with pytest.raises(ValueError,match='newer'): database.create_schema()


def test_actual_archive_provider_metadata(tmp_path):
    item=json.loads(SAMPLE.read_text(encoding='utf-8'))['assets'][0]
    x,y,w,h=item['bbox']; cp=item['identity']['codepoints'][0]; book=item['book_id']; page=item['page']
    crop=f'{book}/characters/{cp}/{cp}_{page}_X{x:04d}_Y{y:04d}.jpg'
    archive=tmp_path/'book.zip'
    with zipfile.ZipFile(archive,'w') as z:
        z.writestr(crop,(SAMPLE.parent/item['file']).read_bytes())
        z.writestr(f'{book}/{book}_coordinate.csv',f'Unicode,Image,X,Y,Width,Height,Char ID\n{cp},{page},{x},{y},{w},{h},C0003\n')
    manifest=tmp_path/'receipt.json'
    manifest.write_text(json.dumps({'schema_version':2,'archives':[{'file':'book.zip','sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'books':{book:{'work':item['work']}}}]}),encoding='utf-8')
    record=next(CODHKuzushijiProvider(manifest).iter_records())
    assert record.variant['id'] == item['variant_id']
    assert record.metadata['source_bbox'] == item['bbox'] and record.metadata['page'] == page
    assert record.culture['writing_tradition'] == 'Japanese' and record.culture['language'] is None


def test_font_checksum_and_malformed_font(tmp_path):
    with pytest.raises(Exception): FontShaper(tmp_path/'absent.ttf')
    font=tmp_path/'bad.ttf'; font.write_bytes(b'not an OpenType font')
    with pytest.raises(Exception): FontShaper(font)
    manifest=json.loads(JP.read_text(encoding='utf-8'))
    manifest['fonts']=[{**manifest['fonts'][0],'path':str((JP.parent/manifest['fonts'][0]['path']).resolve()),'sha256':'0'*64}]
    path=tmp_path/'font.json'; path.write_text(json.dumps(manifest),encoding='utf-8')
    with pytest.raises(ValueError,match='checksum'): list(FontManifestProvider(path,characters={'あ'}).iter_records())
    manifest['fonts'][0]['rights']['commercial_use'] = None
    path.write_text(json.dumps(manifest),encoding='utf-8')
    assert list(FontManifestProvider(path,characters={'あ'},include_noncommercial=False).iter_records()) == []
