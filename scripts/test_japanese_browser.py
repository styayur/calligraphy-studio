"""Production browser regression: Japanese fonts, history, vertical typography and exports."""
import argparse
import base64
import io
import json
import zipfile
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright, expect


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:5178')
    args=parser.parse_args()
    out=Path(__file__).resolve().parents[1]/'work'; out.mkdir(exist_ok=True)
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
        errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
        # Offline means only package-local requests. No CDN, fonts API or mandatory cloud.
        page.route('**/*',lambda route: route.continue_() if route.request.url.startswith(args.url) or route.request.url.startswith('data:') else route.abort())
        page.goto(args.url); page.wait_for_load_state('networkidle')
        composer=page.locator('.composer')
        page.get_by_label('项目菜单').click()
        expect(page.get_by_test_id('app-version')).to_have_text('0.7.0')
        page.get_by_role('button',name='第三方许可 / Third-party licences',exact=True).click()
        notices=json.loads((Path(__file__).resolve().parents[1]/'third_party/manifest.json').read_text(encoding='utf-8'))
        expect(page.frame_locator('iframe').locator('details')).to_have_count(len(notices['components']))
        page.get_by_label('关闭第三方许可').click();page.get_by_label('项目菜单').click()
        expect(composer.get_by_label('Tradition',exact=True)).to_have_value('Chinese')
        composer.get_by_label('Tradition',exact=True).select_option('Japanese')
        composer.get_by_label('集字内容').fill('骨国國学學あか\u3099カ「」、。ー')
        composer.locator('summary').filter(has_text='间距与留白').click()
        composer.get_by_label('保留标点').check()
        page.get_by_role('button',name='生成作品',exact=True).click()
        expect(composer.locator('.feedback')).to_contain_text('已排入 13 字',timeout=120000)
        def project():
            with page.expect_download() as event: page.get_by_role('button',name='保存项目',exact=True).click()
            return json.loads(Path(event.value.path()).read_text(encoding='utf-8'))
        original=project(); assert original['version']==2
        assert len(original['glyphs'])==13
        assert all(g['source']['writing_tradition']=='Japanese' and g['source']['locale']=='ja-JP' for g in original['glyphs'])
        assert all(g['provenance']['type']=='font' and g['metadata']['shaping']['engine']=='harfbuzz-wasm' for g in original['glyphs'])
        assert all(g['metadata']['shaping']['direction']=='ttb' for g in original['glyphs'])
        by_char={g['character']:g for g in original['glyphs']}
        assert by_char['国']['variant']['type']=='shinjitai' and by_char['國']['variant']['type']=='kyujitai'
        assert by_char['か\u3099']['identity']['codepoints']==['U+304B','U+3099']
        for char in '、。':
            alpha=Image.open(io.BytesIO(base64.b64decode(by_char[char]['asset']['url'].split(',')[1]))).getchannel('A')
            bounds=alpha.getbbox(); assert bounds and (bounds[0]+bounds[2])/2>300 and (bounds[1]+bounds[3])/2<200
        # Same selected font/sequence produces the same bitmap across regeneration.
        page.get_by_role('button',name='生成作品',exact=True).click()
        expect(composer.locator('.feedback')).to_contain_text('已排入 13 字',timeout=120000)
        again=project(); assert [g['asset']['checksum'] for g in original['glyphs']]==[g['asset']['checksum'] for g in again['glyphs']]
        page.get_by_role('button',name='选择第1字骨',exact=True).click()
        expect(page.locator('.visual-readout .profile-values')).to_be_visible(timeout=60000)
        assert not any('Chinese' in t for t in page.locator('.variant-grid small').all_text_contents())
        inspector=page.locator('.inspector')
        inspector.locator('summary').filter(has_text='字形与跨传统探索').click()
        inspector.get_by_label('Candidate mode').select_option('cross-tradition')
        expect(page.locator('.variant-grid')).to_contain_text('Chinese',timeout=60000)
        inspector.get_by_label('Candidate mode').select_option('strict')
        expect(page.locator('.variant-grid')).not_to_contain_text('Chinese',timeout=60000)
        inspector.locator('summary').filter(has_text='字形与跨传统探索').click()
        page.screenshot(path=str(out/'japanese-workbench.png'))
        page.get_by_label('关闭字形调整').click()
        composer.get_by_role('button',name='横排',exact=True).click()
        page.get_by_role('button',name='生成作品',exact=True).click()
        expect(composer.locator('.feedback')).to_contain_text('已排入 13 字',timeout=120000)
        horizontal=project()
        assert all(g['metadata']['shaping']['direction']=='ltr' for g in horizontal['glyphs'])
        for g in horizontal['glyphs']:
            if g['character'] in '、。':
                alpha=Image.open(io.BytesIO(base64.b64decode(g['asset']['url'].split(',')[1]))).getchannel('A')
                bounds=alpha.getbbox(); assert bounds and (bounds[0]+bounds[2])/2<200 and (bounds[1]+bounds[3])/2>300
        composer.get_by_role('button',name='竖排',exact=True).click()
        composer.locator('summary').filter(has_text='字形与跨传统探索').click()
        composer.get_by_label('Variant type').select_option('hentaigana')
        composer.get_by_label('集字内容').fill('ああい')
        page.get_by_role('button',name='生成作品',exact=True).click()
        expect(composer.locator('.feedback')).to_contain_text('已排入 3 字',timeout=120000)
        henta=project(); assert all(g['variant']['type']=='hentaigana' and g['provenance']['type']=='font' for g in henta['glyphs'])
        assert henta['glyphs'][0]['character']=='あ'
        # Historical production sample, no KMNIST assets.
        composer.get_by_label('Variant type').select_option('historical')
        composer.get_by_label('字形来源',exact=True).select_option('original')
        composer.get_by_label('集字内容').fill('あの水')
        page.get_by_role('button',name='生成作品',exact=True).click()
        expect(composer.locator('.feedback')).to_contain_text('已排入 3 字',timeout=120000)
        history=project(); assert all(g['source']['rights']['share_alike_required'] for g in history['glyphs'])
        assert all(g['source']['language'] is None for g in history['glyphs'])
        assert all(g['metadata']['source_bbox'] and g['metadata']['page'] for g in history['glyphs'])
        page.get_by_role('button',name='导出作品',exact=True).click()
        with page.expect_download() as event: page.get_by_role('button',name='下载 PNG',exact=True).click()
        assert event.value.suggested_filename.endswith('.zip')
        with zipfile.ZipFile(event.value.path()) as z:
            assert z.testzip() is None and 'artwork.png' in z.namelist()
            assert 'ATTRIBUTION.txt' in z.namelist() and 'licenses/CC-BY-SA-4.0.txt' in z.namelist()
            attribution=json.loads(z.read('attribution.json'))
            assert attribution['artwork_license']=='CC-BY-SA-4.0'
            assert all(g['source']['rights']['share_alike_required'] for g in attribution['glyphs'])
        # Reload proves project schema, local assets and persisted policy survive.
        page.reload(); page.wait_for_load_state('networkidle')
        expect(composer.get_by_label('Tradition',exact=True)).to_have_value('Japanese')
        restored=project(); assert restored['glyphs']==history['glyphs']
        # Long Japanese composition with repeated kana, vertical punctuation, and ZIP attribution.
        page.get_by_role('button',name='长卷模式 · 自动成篇',exact=True).click()
        roll=page.locator('.roll-controls')
        roll.get_by_label('Variant type').select_option('') if roll.get_by_label('Variant type').is_visible() else roll.locator('summary').filter(has_text='字形与跨传统探索').click()
        roll.get_by_label('Variant type').select_option('')
        roll.get_by_label('长卷内容',exact=True).fill('日本あいうカナ'.__mul__(145))
        page.get_by_role('button',name='自动生成长卷',exact=True).click()
        expect(roll.locator('.feedback')).to_contain_text('已生成 1015 字',timeout=180000)
        with page.expect_download(timeout=120000) as event: page.get_by_role('button',name='批量导出 ZIP',exact=True).click()
        with zipfile.ZipFile(event.value.path()) as z:
            manifest=json.loads(z.read('manifest.json'))
            assert manifest['version']==2
            assert all(g['source']['writing_tradition']=='Japanese' for g in manifest['glyphs'].values())
            assert 'attribution.json' in z.namelist()
        page.screenshot(path=str(out/'japanese-long-roll.png'))
        assert not errors,errors
        browser.close()
    print('PASS: Japanese shaping, deterministic bitmap, CJK safety, hentaigana, vertical punctuation, Visual Profile, CODH, share-alike ZIP, persisted v2 project and 1015-character roll')


if __name__=='__main__': main()
