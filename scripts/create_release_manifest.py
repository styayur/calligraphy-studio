"""Verify cross-platform commit/locks/receipts, then hash all final release assets."""
import argparse,datetime,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--commit',required=True);parser.add_argument('--allow-dirty',action='store_true')
    parser.add_argument('--without-android',action='store_true',help='Publish Windows/Web only; no APK or Android receipts may be present')
    args=parser.parse_args();version=json.loads((ROOT/'release/version.json').read_text(encoding='utf-8'))['version']
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==args.commit,'Receipt commit differs from checkout'
    platforms=['windows','web'] if args.without_android else ['windows','android','web']
    if args.without_android:
        assert not list(args.directory.glob('*android*')) and not list(args.directory.glob('*.apk')),'Android files must be omitted from a Windows/Web release'
    provenance={platform:json.loads((args.directory/f'{platform}-build-provenance.json').read_text(encoding='utf-8')) for platform in platforms}
    reference=provenance['web']
    def source_hash(file):
        return hashlib.sha256((ROOT/file).read_text(encoding='utf-8').replace('\r\n','\n').encode()).hexdigest()
    assert reference['locks']=={key:source_hash(file) for key,file in {'web':'apps/web/package-lock.json','desktop':'apps/desktop/package-lock.json','python':'apps/api/requirements.txt','android':'apps/web/android/app/gradle.lockfile'}.items()},'Receipts do not describe checkout lockfiles'
    assert reference['asset_manifest_sha256']==source_hash('samples/asset-manifest.json')
    assert reference['third_party_manifest_sha256']==source_hash('third_party/manifest.json')
    for platform,record in provenance.items():
        assert record['commit']==args.commit and record['version']==version,'Different commit/version across platforms'
        for key in ['locks','asset_manifest_sha256','third_party_manifest_sha256','build_timestamp']:
            assert record[key]==reference[key],f'Cross-platform build provenance mismatch: {key}'
        assert args.allow_dirty or not record['working_tree_dirty'],'Dirty source cannot form a formal release'
    assets=[]
    for file in sorted(args.directory.iterdir()):
        if file.suffix not in {'.exe','.apk','.zip'}:continue
        assert version in file.name,'Wrong version in artifact name'
        assets.append({'name':file.name,'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'size':file.stat().st_size,'platform':'windows' if file.suffix=='.exe' else 'android' if file.suffix=='.apk' else 'web'})
    expected={f'CalligraphyStudio-Setup-{version}-x64.exe',f'CalligraphyStudio-Portable-{version}-x64.exe',f'CalligraphyStudio-Web-{version}.zip'}
    if not args.without_android: expected.add(f'CalligraphyStudio-Android-{version}.apk')
    assert {a['name'] for a in assets}==expected,'Unexpected release asset names'
    signing={p:json.loads((args.directory/f'{p}-signing.json').read_text(encoding='utf-8-sig')) for p in platforms if p!='web'}
    if not args.without_android:
        assert args.allow_dirty or signing['android']['production_ready'],'Production release forbids debug-signed Android preview'
        assert signing['android']['version']==version
    else:
        signing['android']={'published':False,'reason':'Production signing unavailable; preview APK excluded'}
    sums=''.join(f"{a['sha256']}  {a['name']}\n" for a in assets)
    manifest={'schema_version':1,'version':version,'commit':args.commit,'local_rc':args.allow_dirty,'build_timestamp':reference['build_timestamp'],'manifest_created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'provenance':provenance,'signing':signing,'assets':assets}
    (args.directory/'SHA256SUMS.txt').write_text(sums,encoding='utf-8')
    (args.directory/'release-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(f'PASS: {len(assets)} assets from one commit/lock/asset receipt; '+('LOCAL DIRTY RC — not a formal tagged release' if args.allow_dirty else 'clean release'))
if __name__=='__main__':main()
