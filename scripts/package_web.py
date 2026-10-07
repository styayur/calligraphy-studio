"""Deterministic offline ZIP: sorted files, fixed timestamp/mode, no host metadata."""
import argparse,datetime,os,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def package(dist,output,epoch):
    date=datetime.datetime.fromtimestamp(max(epoch,315532800),datetime.timezone.utc).timetuple()[:6]
    output.parent.mkdir(parents=True,exist_ok=True)
    files={p.relative_to(dist).as_posix():p.read_bytes() for p in sorted(dist.rglob('*')) if p.is_file()}
    files['README.md']=(ROOT/'release/WEB_README.md').read_text(encoding='utf-8').replace('\r\n','\n').encode()
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for name,content in sorted(files.items()):
            info=zipfile.ZipInfo(name,date);info.compress_type=zipfile.ZIP_DEFLATED
            info.create_system=3;info.external_attr=0o100644<<16
            archive.writestr(info,content,compresslevel=9)
    print('Packaged',output,output.stat().st_size,'bytes')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dist',type=Path,default=ROOT/'apps/web/dist')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--epoch',type=int,default=int(os.environ.get('SOURCE_DATE_EPOCH') or subprocess.check_output(['git','show','-s','--format=%ct','HEAD'],cwd=ROOT,text=True).strip()))
    args=parser.parse_args();package(args.dist,args.output,args.epoch)
