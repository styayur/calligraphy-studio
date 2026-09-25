import time,json
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,channel='msedge')
 page=b.new_page(viewport={'width':1440,'height':1000})
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:5186');page.wait_for_load_state('networkidle')
 chars=page.evaluate("async()=>{const c=await (await fetch('/fonts/catalog.json')).json();return [...c.find(f=>f.style==='行书').characters].filter(c=>/\\p{Script=Han}/u.test(c)).slice(0,1001).join('')}")
 assert len(chars)==1001
 page.get_by_label('集字内容',exact=True).fill(chars[:1000]);start=time.monotonic()
 page.get_by_role('button',name='生成作品',exact=True).click()
 expect(page.locator('.composer .feedback')).to_contain_text('已排入 1000 字',timeout=180000)
 composed=time.monotonic()-start
 page.get_by_role('button',name='作品协调度 分析',exact=True).click();start=time.monotonic()
 expect(page.locator('.work-harmony')).to_contain_text('已分析 1000/1000',timeout=180000)
 analyzed=time.monotonic()-start
 assert '0 字读取失败' in page.locator('.work-harmony').inner_text()
 page.get_by_role('button',name='长卷模式 · 自动成篇',exact=True).click()
 page.get_by_label('长卷内容',exact=True).fill(chars)
 page.locator('.roll-controls').get_by_label('长卷书体',exact=True).select_option('行书')
 start=time.monotonic();page.get_by_role('button',name='自动生成长卷',exact=True).click()
 expect(page.locator('.roll-controls .feedback')).to_contain_text('已生成 1001 字 / 11 页',timeout=180000)
 roll=time.monotonic()-start
 assert not errors,errors
 report={'distinctCharacters':1000,'composeSeconds':round(composed,2),'coldFeatureSeconds':round(analyzed,2),'cachedRoll1001Seconds':round(roll,2),'consoleErrors':errors}
 print(json.dumps(report));Path('work/distinct-benchmark.json').write_text(json.dumps(report,indent=2));b.close()
