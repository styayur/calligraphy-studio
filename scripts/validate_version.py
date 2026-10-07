"""One release version and stable schema across every application surface."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate():
    release=json.loads((ROOT/'release/version.json').read_text(encoding='utf-8'))
    version=release['version']
    for folder in ['apps/web','apps/desktop']:
        for file in ['package.json','package-lock.json']:
            data=json.loads((ROOT/folder/file).read_text(encoding='utf-8'))
            assert data['version']==version,(folder,file)
            if file.endswith('lock.json'): assert data['packages']['']['version']==version
    for file,pattern in [('apps/api/pyproject.toml',r'version\s*=\s*"([^"]+)"'),('apps/api/app/main.py',r'version="([^"]+)"'),('apps/web/android/app/build.gradle',r'versionName "([^"]+)"')]:
        assert re.search(pattern,(ROOT/file).read_text(encoding='utf-8')).group(1)==version,file
    gradle=(ROOT/'apps/web/android/app/build.gradle').read_text(encoding='utf-8')
    assert int(re.search(r'versionCode (\d+)',gradle).group(1))==release['android_version_code']
    assert f'applicationId "{release["application_id"]}"' in gradle
    for file in ['samples/asset-manifest.json','apps/web/public/fonts/asset-manifest.json']:
        manifest=json.loads((ROOT/file).read_text(encoding='utf-8'))
        assert manifest['release']==version and manifest['schema_version']==release['schema_version']
    assert f'content="{version}"' in (ROOT/'apps/web/index.html').read_text(encoding='utf-8')
    assert version in (ROOT/'release/RELEASE_NOTES_0.7.0.md').read_text(encoding='utf-8')
    workflow=(ROOT/'.github/workflows/release-all.yml').read_text(encoding='utf-8')
    # Dispatch selects a Git tag ref now; validate the concrete package/note names.
    assert set(re.findall(r'CalligraphyStudio-(?:Setup|Portable)-(\d+\.\d+\.\d+)-x64\.exe',workflow))=={version}
    assert f'RELEASE_NOTES_{version}.md' in workflow
    assert 'SCHEMA_VERSION = 2' in (ROOT/'apps/api/app/domain.py').read_text(encoding='utf-8')
    assert 'SCHEMA_VERSION = 2' in (ROOT/'apps/web/src/lib/identity.ts').read_text(encoding='utf-8')
    assert 'APP_VERSION' in (ROOT/'apps/web/src/components/editor/Toolbar.tsx').read_text(encoding='utf-8')
    assert "'import.meta.env.VITE_APP_VERSION'" in (ROOT/'apps/web/vite.config.ts').read_text(encoding='utf-8')
    print(f'PASS: canonical version {version}, schema {release["schema_version"]}, Android code {release["android_version_code"]}')
if __name__=='__main__': validate()
