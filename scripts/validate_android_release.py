"""Check actual APK identity/signature; preview acceptance must be explicit."""
import argparse,json,os,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def validate(apk,sdk,allow_preview=False):
    folders=sorted((sdk/'build-tools').iterdir(),key=lambda p:tuple(int(x) for x in p.name.split('.') if x.isdigit()))
    tools=folders[-1]
    def command(name,*args):
        exe=tools/(name+('.bat' if name=='apksigner' and os.name=='nt' else '.exe' if os.name=='nt' else ''))
        result=subprocess.run([str(exe),*map(str,args)],capture_output=True,text=True,check=True)
        return result.stdout
    signature=command('apksigner','verify','--verbose','--print-certs',apk)
    badging=command('aapt','dump','badging',apk)
    info=re.search(r"package: name='([^']+)' versionCode='(\d+)' versionName='([^']+)'",badging)
    expected=json.loads((ROOT/'release/version.json').read_text(encoding='utf-8'))
    assert info and info.groups()==(expected['application_id'],str(expected['android_version_code']),expected['version']),'APK identity/version mismatch'
    dn=re.search(r'Signer #1 certificate DN: (.+)',signature).group(1)
    fingerprint=re.search(r'Signer #1 certificate SHA-256 digest: ([0-9a-f]+)',signature).group(1)
    preview='android debug' in dn.lower()
    if preview and not allow_preview: raise ValueError('Debug-signed preview APK cannot be a production release')
    pinned=os.environ.get('CALLIGRAPHY_ANDROID_CERT_SHA256')
    if pinned and fingerprint!=pinned.lower().replace(':',''):raise ValueError('APK signing certificate fingerprint differs from approved certificate')
    status={'version':expected['version'],'version_code':expected['android_version_code'],'package_id':info.group(1),'signing':'debug-signed-preview' if preview else 'release-signed','certificate_sha256':fingerprint,'production_ready':not preview}
    print(json.dumps(status,indent=2));return status
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk',type=Path,required=True);parser.add_argument('--sdk',type=Path,default=Path(os.environ.get('ANDROID_SDK_ROOT') or os.environ.get('ANDROID_HOME') or '.'))
    parser.add_argument('--allow-preview',action='store_true');parser.add_argument('--output',type=Path)
    args=parser.parse_args();status=validate(args.apk,args.sdk,args.allow_preview)
    if args.output:args.output.write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
