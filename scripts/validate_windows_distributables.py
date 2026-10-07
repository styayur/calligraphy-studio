"""Inspect the installer/portable payload themselves without running an installer."""
import argparse,json,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate(executable,seven_zip):
    workspace=(ROOT/'work').resolve();workspace.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='package-audit-',dir=workspace) as temp:
        target=Path(temp).resolve()
        assert target.is_relative_to(workspace)
        def extract(source,destination):
            result=subprocess.run([str(seven_zip),'x','-y',f'-o{destination}',str(source)],capture_output=True,text=True)
            assert result.returncode in [0,1],result.stderr
        extract(executable.resolve(),target)
        asars=list(target.rglob('app.asar'))
        if not asars:
            payloads=list(target.rglob('app-64.7z'))
            assert len(payloads)==1,'Missing installer payload'
            extract(payloads[0],target/'payload')
            asars=list((target/'payload').rglob('app.asar'))
        assert len(asars)==1,'Unexpected ASAR payload count'
        subprocess.run(['node',str(ROOT/'scripts/validate_desktop_package.cjs'),str(asars[0])],check=True)
        count=len(json.loads((ROOT/'third_party/manifest.json').read_text(encoding='utf-8'))['components'])
        print(f'PASS: final {executable.name} actual embedded payload/{count} licence components/Electron/Chromium notices')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seven-zip',type=Path)
    parser.add_argument('packages',nargs='+',type=Path)
    args=parser.parse_args()
    if not args.seven_zip:
        cache=Path(os.environ.get('LOCALAPPDATA',''))/'electron-builder/Cache'
        matches=list(cache.glob('7zip@*/*/bin/7za.exe'))
        if not matches:parser.error('Specify --seven-zip PATH to the electron-builder cached 7za binary')
        args.seven_zip=matches[-1]
    for package in args.packages:validate(package,args.seven_zip)
