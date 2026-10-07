"""Generate Windows resources from the existing tracked brand artwork."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
target = ROOT / 'apps/desktop/build'
target.mkdir(parents=True,exist_ok=True)
with Image.open(ROOT / 'apps/web/assets/icon-only.png') as source:
    icon = source.convert('RGBA').resize((512,512),Image.Resampling.LANCZOS)
    icon.save(target/'icon.png')
    icon.save(target/'icon.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print('Built desktop icon from tracked brand artwork')
