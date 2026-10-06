"""Generate lightweight licensed runtime crops from the pinned original sample."""
import hashlib
import io
import json
import shutil
import sys
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api"))
from app.providers.codh import CODHKuzushijiProvider
from app.domain import require_rights


def main():
    target = ROOT / "apps/web/public/japanese"
    (target / "assets").mkdir(parents=True, exist_ok=True)
    (target / "licenses").mkdir(exist_ok=True)
    glyphs = []
    for record in CODHKuzushijiProvider(ROOT / "samples/japanese/historical/sample/manifest.json").iter_records():
        require_rights(record.rights, bundle=True, derivative=True)
        with Image.open(io.BytesIO(record.asset_bytes)) as image:
            image = ImageOps.exif_transpose(image).convert("L")
            # Explicit derivative: grayscale inverted to an alpha ink mask.
            alpha = image.point(lambda v: max(0, min(255, round((245-v)*255/245))))
            rgba = Image.new("RGBA", image.size, (23, 27, 26, 255))
            rgba.putalpha(alpha)
            buffer = io.BytesIO()
            rgba.save(buffer, format="PNG", optimize=True)
        data = buffer.getvalue()
        checksum = hashlib.sha256(data).hexdigest()
        filename = f"assets/{checksum}.png"
        (target / filename).write_bytes(data)
        glyphs.append(dict(id=record.variant["id"],character=record.character,identity=record.identity,variant=record.variant,
                           source={**record.culture,"dataset":record.dataset,"work":record.work,"calligrapher":None,
                                   "license":record.license,"license_url":record.license_url,"rights":record.rights,
                                   **{k:record.metadata.get(k) for k in ['source_uri','source_checksum','attribution','dataset_version','license_text']}},
                           asset=dict(type='raster',url='japanese/'+filename,width=rgba.width,height=rgba.height,bbox=[0,0,rgba.width,rgba.height],checksum=checksum,processing='ink-mask'),
                           transform=dict(x=0,y=0,scaleX=.3,scaleY=.3,rotation=0,skewX=0,skewY=0),
                           appearance=dict(opacity=1,blendMode='multiply'),provenance=dict(type='original'),
                           metadata={**record.metadata,"processing":"ink-mask", "derivative_license":record.license,
                                     "changes":"Converted CODH's existing crop to grayscale alpha ink mask; original crop retained in samples.", "original_crop_checksum":hashlib.sha256(record.asset_bytes).hexdigest()}))
    (target / "glyphs.json").write_text(json.dumps(glyphs, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    shutil.copyfile(ROOT / "third_party/japanese/codh/CC-BY-SA-4.0.txt",target / "licenses/CC-BY-SA-4.0.txt")
    print(f"Bundled {len(glyphs)} CODH sample glyphs under CC-BY-SA-4.0")


if __name__ == '__main__':
    main()
