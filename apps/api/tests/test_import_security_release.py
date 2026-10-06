import hashlib,io,json,stat,struct,zipfile,zlib
from pathlib import Path
import pytest
from PIL import Image
from sqlalchemy import func,select
from app.database import Database
from app.models import Glyph
from app.providers.base import DatasetProvider,RawGlyphRecord
from app.providers.codh import CODHKuzushijiProvider,validate_archive,safe_local
from app.services.asset_store import AssetStore
from app.services.glyph_importer import GlyphImporter
from app.utils.image_meta import inspect_asset_bytes

ROOT=Path(__file__).resolve().parents[3]

@pytest.mark.parametrize('path',['../','../../escape.png','/absolute.png','C:/absolute.png','D:relative.png','//server/share/a.png','a/../../escape.png','..\\escape.png'])
def test_hostile_archive_paths(path,tmp_path):
    with pytest.raises(ValueError): safe_local(tmp_path,path)
    data=io.BytesIO()
    info=zipfile.ZipInfo('placeholder.png'); info.filename=path
    with zipfile.ZipFile(data,'w') as archive: archive.writestr(info,b'x')
    with zipfile.ZipFile(data) as archive:
        with pytest.raises(ValueError): validate_archive(archive)

@pytest.mark.parametrize('attack',['symlink','encrypted','oversize','ratio','duplicate'])
def test_archive_member_security(attack):
    data=io.BytesIO()
    with zipfile.ZipFile(data,'w') as archive:
        archive.writestr('a.png',b'x')
        if attack=='duplicate': archive.writestr('A.png',b'y')
    with zipfile.ZipFile(data) as archive:
        item=archive.infolist()[0]
        if attack=='symlink': item.external_attr=(stat.S_IFLNK|0o777)<<16
        if attack=='encrypted': item.flag_bits|=1
        if attack=='oversize': item.file_size=41*1024*1024
        if attack=='ratio': item.file_size=1001;item.compress_size=1
        with pytest.raises(ValueError): validate_archive(archive)

@pytest.mark.parametrize('manifest',[{'schema_version':2,'archives':[{'file':'a.zip','sha256':'invalid'}]}, {'schema_version':2,'assets':[{'file':'a.png','sha256':'0'*64}]}, {'schema_version':2,'archives':[{'file':'a.zip','sha256':'0'*64,'books':{'x':[]}}]}, {'schema_version':2,'assets':[{'file':'a.bmp','sha256':'0'*64,'variant_id':'x','character':'あ'}]}])
def test_malformed_corpus_receipts(tmp_path,manifest):
    path=tmp_path/'manifest.json';path.write_text(json.dumps(manifest),encoding='utf-8')
    with pytest.raises(ValueError): CODHKuzushijiProvider(path)

def test_image_dimension_bomb_before_decode():
    out=io.BytesIO();Image.new('RGBA',(1,1),'black').save(out,format='PNG')
    data=bytearray(out.getvalue());data[16:24]=struct.pack('>II',10000,10000)
    data[29:33]=struct.pack('>I',zlib.crc32(data[12:29]))
    with pytest.raises(ValueError): inspect_asset_bytes(bytes(data))

def test_checksum_mismatch_and_disguised_image(tmp_path):
    original=json.loads((ROOT/'samples/japanese/historical/sample/manifest.json').read_text(encoding='utf-8'))['assets'][0]
    out=io.BytesIO();Image.new('RGB',(2,2)).save(out,format='BMP')
    (tmp_path/'crop.jpg').write_bytes(out.getvalue())
    item={**original,'file':'crop.jpg','sha256':hashlib.sha256(out.getvalue()).hexdigest()}
    path=tmp_path/'manifest.json';path.write_text(json.dumps({'schema_version':2,'assets':[item]}),encoding='utf-8')
    with pytest.raises(ValueError,match='JPEG or PNG'):list(CODHKuzushijiProvider(path).iter_records())
    item['sha256']='0'*64;path.write_text(json.dumps({'schema_version':2,'assets':[item]}),encoding='utf-8')
    with pytest.raises(ValueError,match='checksum'):list(CODHKuzushijiProvider(path).iter_records())

def test_cancelled_checkpoint_and_checksum_deduplication(tmp_path):
    out=io.BytesIO();Image.new('RGBA',(8,8),'black').save(out,format='PNG')
    class Records(DatasetProvider):
        name='checkpoint-test'
        def __init__(self,cancelled=False):self.cancelled=cancelled
        def iter_records(self):
            for i in range(105):
                if self.cancelled and i==102:raise InterruptedError('cancelled')
                yield RawGlyphRecord(character='あ',dataset='checkpoint',asset_bytes=out.getvalue(),original_filename='a.png',variant={'type':'historical','id':str(i)})
    database=Database(f'sqlite:///{(tmp_path/"test.db").as_posix()}');database.create_schema()
    importer=GlyphImporter(AssetStore(tmp_path/'assets'),database)
    with pytest.raises(InterruptedError):importer.import_provider(Records(True))
    with database.session() as session:assert session.scalar(select(func.count(Glyph.id)))==100
    result=importer.import_provider(Records())
    assert (result.imported,result.skipped,result.failed)==(5,100,0)
    assert importer.import_provider(Records()).skipped==105
    assert len(list((tmp_path/'assets').rglob('*.png')))==1
