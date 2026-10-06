"""Retain reviewed dev alerts visibly; fail new or production npm vulnerabilities."""
import datetime,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def audit(folder,production=False):
    cmd=['npm.cmd' if __import__('os').name=='nt' else 'npm','audit','--json']+(['--omit=dev'] if production else [])
    result=subprocess.run(cmd,cwd=ROOT/folder,capture_output=True,text=True)
    data=json.loads(result.stdout)
    assert result.returncode in [0,1] and 'metadata' in data,'Audit unavailable; do not interpret an error as zero vulnerabilities'
    return data
def main():
    policy=json.loads((ROOT/'release/dependency-policy.json').read_text(encoding='utf-8'))
    if datetime.date.today()>datetime.date.fromisoformat(policy['review_before']):raise ValueError('Development advisory review expired; review upstream patch/exposure before releasing')
    report={}
    for folder,production in [('apps/web',True),('apps/web',False),('apps/desktop',False)]:
        data=audit(folder,production);key=folder+(':production' if production else ':full')
        report[key]=data
        if production or folder=='apps/desktop':assert data['metadata']['vulnerabilities']['total']==0,f'Unreviewed production/desktop vulnerabilities in {key}'
        else:
            for name,alert in data['vulnerabilities'].items():
                assert name in policy['affected_tooling'],f'New development alert: {name}'
                for cause in alert['via']:
                    if isinstance(cause,dict):assert cause['url'] in policy['development_only_advisories'],'New underlying advisory'
        print(key, json.dumps(data['metadata']['vulnerabilities']))
    target=ROOT/'work/dependency-audit-rc.json';target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps({'review_policy':policy,'audits':report},indent=2)+'\n',encoding='utf-8')
    print('Reviewed high development alerts remain visible. This is not a zero-vulnerability full-tree claim.')
if __name__=='__main__':main()
