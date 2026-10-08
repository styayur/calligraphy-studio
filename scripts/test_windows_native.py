"""Actual packaged Electron renderer smoke test, isolated from the user's drafts.

Requires Windows and Playwright Chromium. This launches the supplied executable
(unpacked or portable) with an explicit hidden test switch and local CDP port.
Installer wizard / installed shortcuts remain human checks, not simulated results.
"""
import argparse,json,os,socket,subprocess,time
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if os.name!='nt':parser.error('Native Windows smoke requires Windows')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    workspace=(ROOT/'work/native-smoke'/args.exe.stem/f'run-{time.time_ns()}').resolve();workspace.mkdir(parents=True,exist_ok=True)
    assert workspace.is_relative_to((ROOT/'work').resolve())
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    env=dict(os.environ);env.pop('ELECTRON_RUN_AS_NODE',None)
    checks=[];errors=[]
    with (workspace/'process.log').open('wb') as log:
        process=subprocess.Popen([str(args.exe.resolve()),'--release-smoke-test',f'--remote-debugging-port={port}',f'--user-data-dir={workspace/"profile"}'],env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
        browser=None
        try:
            with sync_playwright() as playwright:
                deadline=time.monotonic()+60
                while time.monotonic()<deadline:
                    try:browser=playwright.chromium.connect_over_cdp(f'http://127.0.0.1:{port}',timeout=1000);break
                    except Exception:time.sleep(.2)
                assert browser,'Native Electron CDP endpoint did not start; inspect process.log'
                context=browser.contexts[0]
                page=context.pages[0] if context.pages else context.new_page()
                page.wait_for_url('app://bundle/index.html',timeout=60000)
                page.wait_for_load_state('networkidle');page.on('pageerror',lambda error:errors.append(str(error)))
                page.on('dialog',lambda dialog:dialog.accept())
                checks.append('native executable launch and app:// packaged renderer')
                # No network is needed by the packaged workbench.
                page.route('https://**',lambda route:route.abort());page.route('http://**',lambda route:route.abort())
                page.get_by_label('项目菜单').click()
                expect(page.get_by_test_id('app-version')).to_have_text('0.7.1')
                page.get_by_role('button',name='第三方许可 / Third-party licences',exact=True).click()
                frame=page.frame_locator('iframe[title="Bundled third-party licence texts"]')
                notice_count=len(json.loads((ROOT/'third_party/manifest.json').read_text(encoding='utf-8'))['components'])
                expect(frame.locator('details')).to_have_count(notice_count)
                expect(frame.locator('body')).to_contain_text('CODH Kuzushiji')
                page.get_by_label('关闭第三方许可').click();page.get_by_label('项目菜单').click()
                checks.append(f'version 0.7.1 and offline {notice_count}-component licence viewer')
                composer=page.locator('.composer')
                composer.get_by_label('字形来源',exact=True).select_option('fonts')
                def compose(text,count):
                    composer.get_by_label('集字内容',exact=True).fill(text)
                    page.get_by_role('button',name='生成作品',exact=True).click()
                    expect(composer.locator('.feedback')).to_contain_text(f'已排入 {count} 字',timeout=120000)
                def save(name):
                    with page.expect_download(timeout=60000) as event:page.get_by_role('button',name='保存项目',exact=True).click()
                    file=workspace/name;event.value.save_as(file);return json.loads(file.read_text(encoding='utf-8'))
                compose('明月',2);assert all(g['source']['writing_tradition']=='Chinese' for g in save('chinese.json')['glyphs'])
                checks.append('bundled Chinese fonts compose/save')
                for name in ['legacy-v1-chinese','v2-japanese-modern']:
                    fixture=ROOT/f'tests/fixtures/projects/{name}.json'
                    original=json.loads(fixture.read_text(encoding='utf-8'))
                    page.locator('input[type=file]').set_input_files(fixture)
                    expect(page.locator('.character-strip button')).to_have_count(len(original['glyphs']))
                    saved=save(name+'.json');assert saved['version']==2
                    assert [g['character'] for g in saved['glyphs']]==[g['character'] for g in original['glyphs']]
                    page.locator('input[type=file]').set_input_files(workspace/(name+'.json'))
                    reloaded=save(name+'-reloaded.json');assert reloaded['glyphs']==saved['glyphs']
                checks.append('legacy Chinese/Japanese fixture load/save/reopen semantic integrity')
                composer.get_by_label('Tradition',exact=True).select_option('Japanese')
                compose('骨あカ',3)
                modern=save('japanese.json');assert all(g['metadata']['shaping']['engine']=='harfbuzz-wasm' for g in modern['glyphs'])
                page.get_by_role('button',name='选择第1字骨',exact=True).click()
                expect(page.locator('.variant-grid')).to_contain_text('Yuji Boku',timeout=60000)
                expect(page.locator('.variant-grid')).to_contain_text('Yuji Mai')
                expect(page.locator('.variant-grid')).to_contain_text('Yuji Syuku')
                expect(page.locator('.variant-grid')).to_contain_text('Klee One')
                page.get_by_label('关闭字形调整').click()
                checks.append('Yuji and Klee candidates / HarfBuzz glyph IDs')
                compose('㐆',1)
                rare=save('japanese-coverage.json')['glyphs'][0]
                assert rare['source']['source_role']=='coverage-fallback' and rare['source']['locale']=='ja-JP'
                assert rare['source']['license']=='OFL-1.1' and rare['metadata']['shaping']['direction']=='ttb'
                checks.append('Japanese-only rare kanji coverage fallback')
                composer.locator('summary').filter(has_text='字形与跨传统探索').click()
                composer.get_by_label('Variant type').select_option('hentaigana');compose('ああ',2)
                assert all(g['variant']['type']=='hentaigana' for g in save('hentaigana.json')['glyphs'])
                page.get_by_role('button',name='选择第1字あ',exact=True).click()
                expect(page.locator('.variant-grid')).to_contain_text('Yuji Akari',timeout=60000)
                expect(page.locator('.variant-grid')).to_contain_text('Yuji Akebono')
                page.get_by_label('关闭字形调整').click();composer.get_by_label('Variant type').select_option('')
                checks.append('Akari/Akebono identity and font variants')
                compose('日本あカ',4)
                page.get_by_role('button',name='导出作品',exact=True).click()
                with page.expect_download(timeout=60000) as event:page.get_by_role('button',name='下载 PNG',exact=True).click()
                png=workspace/'artwork.png';event.value.save_as(png)
                with Image.open(png) as image:assert image.width>100 and image.height>100
                checks.append('native PNG download and project JSON export')
                composer.get_by_label('字形来源',exact=True).select_option('original');compose('は',1)
                historical=save('historical.json');assert historical['glyphs'][0]['source']['license']=='CC-BY-SA-4.0'
                page.get_by_role('button',name='选择第1字は',exact=True).click()
                page.locator('.provenance-details summary').click()
                expect(page.locator('.provenance-details')).to_contain_text('10.20676/00000340')
                # Hidden native windows do not present a compositor surface for screenshots.
                # Preserve the inspected DOM/metadata as evidence; visible UI acceptance is manual.
                (workspace/'native-provenance.html').write_text(page.content(),encoding='utf-8')
                checks.append('historical sample / DOI / rights provenance inspector')
                assert not errors,errors
                browser.close()
                browser=None
        finally:
            if process.poll() is None:
                try:process.wait(timeout=8)
                except subprocess.TimeoutExpired:subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],capture_output=True)
    result={'executable':args.exe.name,'evidence_directory':str(workspace),'status':'PASS','checks':checks,'errors':errors,'installer_wizard':'NOT EXECUTED — human native test required','physical_android':'NOT EXECUTED — requires physical device'}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
