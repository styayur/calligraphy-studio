"""End-to-end feature/cache/1000-character/long-roll regression. Vite desktop mode."""
import argparse
import json
import time
import zipfile
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright, expect
parser=argparse.ArgumentParser()
parser.add_argument('--url',default='http://127.0.0.1:5186')
parser.add_argument('--channel',default=None)
parser.add_argument('--built',action='store_true',help='Test a production bundle without development module imports')
args=parser.parse_args()
out=Path(__file__).resolve().parents[1]/'work'
out.mkdir(exist_ok=True)
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,channel=args.channel)
    page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(args.url);page.wait_for_load_state('networkidle')
    page.get_by_label('集字内容',exact=True).fill('明月松间照清泉石上流')
    page.get_by_role('button',name='生成作品',exact=True).click()
    expect(page.locator('.composer .feedback')).to_contain_text('已排入 10 字',timeout=60000)
    page.get_by_role('button',name='选择第1字明',exact=True).click()
    expect(page.locator('.visual-readout .profile-values')).to_be_visible(timeout=60000)
    page.get_by_label('按协调度排序').check()
    expect(page.locator('.difference-row')).to_have_count(11)
    page.get_by_role('button',name='替换为Ma Shan Zheng',exact=True).hover()
    expect(page.locator('.context-preview')).to_contain_text('Ma Shan Zheng')
    page.screenshot(path=str(out/'visual-profile.png'))
    before=None if args.built else page.evaluate("async()=>({... (await import(performance.getEntriesByType('resource').find(e=>e.name.includes('/src/lib/featureCache.ts')).name)).featureStats})")
    page.get_by_role('button',name='替换为Ma Shan Zheng',exact=True).click()
    expect(page.locator('.visual-readout .profile-values')).to_be_visible()
    after=None if args.built else page.evaluate("async()=>({... (await import(performance.getEntriesByType('resource').find(e=>e.name.includes('/src/lib/featureCache.ts')).name)).featureStats})")
    if not args.built:
        assert before['computed']==after['computed'],'replacement should reuse candidate feature cache'
    page.get_by_role('button',name='关闭字形调整').click()
    page.get_by_role('button',name='作品协调度 分析',exact=True).click()
    expect(page.locator('.work-harmony')).to_contain_text('已分析 10/10',timeout=60000)
    # Source feature disk cache survives reload.
    page.reload();page.wait_for_load_state('networkidle')
    page.get_by_role('button',name='选择第1字明',exact=True).click()
    expect(page.locator('.visual-readout .profile-values')).to_be_visible(timeout=60000)
    disk=None if args.built else page.evaluate("async()=>({... (await import(performance.getEntriesByType('resource').find(e=>e.name.includes('/src/lib/featureCache.ts')).name)).featureStats})")
    if not args.built:
        assert disk['diskHits']>0,disk
    else:
        stored=page.evaluate("() => new Promise((resolve,reject)=>{const r=indexedDB.open('calligraphy-features',1);r.onerror=()=>reject(r.error);r.onsuccess=()=>{const db=r.result;const q=db.transaction('profiles').objectStore('profiles').count();q.onsuccess=()=>{resolve(q.result);db.close()}}})")
        assert stored>0,'production features must persist in IndexedDB'
    page.get_by_role('button',name='关闭字形调整').click()
    page.get_by_label('集字内容',exact=True).fill('明月松间照清泉石上流'*100)
    started=time.monotonic();page.get_by_role('button',name='生成作品',exact=True).click()
    expect(page.locator('.composer .feedback')).to_contain_text('已排入 1000 字',timeout=120000)
    workbench_seconds=time.monotonic()-started
    assert page.locator('.character-strip button').count()<60,'character strip must be virtual'
    page.locator('.character-strip > .panel-scroll').evaluate('(e)=>e.scrollLeft=e.scrollWidth')
    expect(page.get_by_role('button',name='选择第1000字流',exact=True)).to_be_visible()
    page.screenshot(path=str(out/'studio-1000.png'))
    page.get_by_label('集字内容',exact=True).fill('山'*1001)
    expect(page.get_by_role('button',name='生成作品',exact=True)).to_be_disabled()
    page.get_by_role('button',name='长卷模式 · 自动成篇',exact=True).click()
    page.get_by_label('长卷内容',exact=True).fill('明月松间照清泉石上流'*103+'😀')
    started=time.monotonic();page.get_by_role('button',name='自动生成长卷',exact=True).click()
    expect(page.locator('.roll-controls .feedback')).to_contain_text('已生成 1031 字 / 11 页',timeout=120000)
    roll_seconds=time.monotonic()-started
    expect(page.locator('.roll-controls .feedback')).to_contain_text('缺字 1 处')
    assert page.locator('.roll-page').count()<=4
    page.screenshot(path=str(out/'long-roll.png'))
    page.locator('.roll-preview').evaluate('(e)=>e.scrollTop=e.scrollHeight')
    expect(page.get_by_label('长卷第 11 页',exact=True)).to_be_visible()
    assert page.locator('.roll-page').count()<=4
    with page.expect_download(timeout=120000) as download:
        page.get_by_role('button',name='批量导出 ZIP',exact=True).click()
    path=out/'roll-export.zip';download.value.save_as(path)
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert len([n for n in z.namelist() if n.endswith('.png')])==11
        manifest=json.loads(z.read('manifest.json'))
        assert sum(len(p['slots']) for p in manifest['pages'])==1031
        assert manifest['missing']==[{'character':'😀','positions':[1031]}]
        selected=[s['glyph'] for p in manifest['pages'] for s in p['slots'] if s['character']=='明']
        assert len(set(selected))>1,'repeat variation should choose multiple available candidates'
        import io
        im=Image.open(io.BytesIO(z.read('pages/0001.png')))
        assert im.size==(800,1100)
        assert len(im.convert('RGB').getcolors(800*1100))>1,'export must contain actual ink'
    # Cancellation keeps completed result.
    page.get_by_label('长卷内容',exact=True).fill('山'*10000)
    page.get_by_role('button',name='自动生成长卷',exact=True).click()
    page.get_by_role('button',name='取消当前任务').click()
    expect(page.locator('.roll-controls .feedback')).to_contain_text('已取消',timeout=30000)
    expect(page.get_by_role('button',name='批量导出 ZIP')).to_be_enabled()
    page.set_viewport_size({'width':390,'height':844})
    page.screenshot(path=str(out/'long-roll-mobile.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    assert not errors,errors
    report={'workbench1000Seconds':round(workbench_seconds,2),'roll1031Seconds':round(roll_seconds,2),'diskCache':disk,'consoleErrors':errors}
    (out/'visual-test-report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,ensure_ascii=False));browser.close()
