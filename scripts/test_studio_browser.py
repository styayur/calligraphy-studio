"""Browser regression checks. Run against Vite in desktop mode.

python scripts/test_studio_browser.py --url http://127.0.0.1:5178 --channel msedge
Requires playwright and pillow. Screenshots/downloads go into ignored work/.
"""
import argparse
import base64
import io
import json
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright, expect

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:5178')
parser.add_argument('--channel', default=None)
args = parser.parse_args()
output = Path(__file__).resolve().parents[1] / 'work'
output.mkdir(exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel=args.channel)
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(args.url)
    page.wait_for_load_state('networkidle')
    expect(page.get_by_label('集字内容')).to_be_visible()
    page.get_by_label('集字内容').fill('尚未生成的文字')
    page.reload()
    page.wait_for_load_state('networkidle')
    expect(page.get_by_label('集字内容')).to_have_value('尚未生成的文字')
    page.get_by_label('集字内容').fill('明月松间照\n清泉石上流')
    page.get_by_label('项目名称').fill('山居秋暝')
    page.get_by_role('button', name='生成作品', exact=True).click()
    expect(page.locator('.feedback').first).to_contain_text('已排入 10 字', timeout=60000)
    expect(page.locator('.character-strip button')).to_have_count(10)
    page.wait_for_load_state('networkidle')

    def project():
        with page.expect_download() as download:
            page.get_by_role('button', name='保存项目', exact=True).click()
        return json.loads(Path(download.value.path()).read_text(encoding='utf-8'))

    original = project()
    assert original['name'] == '山居秋暝'
    glyphs = original['glyphs']
    assert glyphs[0]['transform']['x'] > glyphs[5]['transform']['x'], 'vertical columns should progress right to left'
    for glyph in glyphs:
        assert 0 < glyph['transform']['x'] < original['canvas']['width']
        assert 0 < glyph['transform']['y'] < original['canvas']['height']
        assert glyph['provenance']['type'] == 'font'
    assert all(g['asset']['url'].startswith('data:image/png') for g in glyphs)

    # Select by clicking the actual paper, then replace by a different font.
    box = page.locator('.paper-frame').bounding_box()
    first = glyphs[0]['transform']
    page.mouse.click(box['x'] + first['x'] / original['canvas']['width'] * box['width'], box['y'] + first['y'] / original['canvas']['height'] * box['height'])
    expect(page.get_by_label('字形调整', exact=True)).to_be_visible()
    page.get_by_role('button', name='替换为Ma Shan Zheng', exact=True).click()
    changed = project()
    assert changed['glyphs'][0]['glyph_id'] != glyphs[0]['glyph_id']
    assert changed['glyphs'][0]['transform'] == glyphs[0]['transform']
    page.get_by_role('button', name='撤销', exact=True).click()
    assert project()['glyphs'][0]['glyph_id'] == glyphs[0]['glyph_id']
    page.get_by_role('button', name='重做', exact=True).click()
    assert project()['glyphs'][0]['glyph_id'] == changed['glyphs'][0]['glyph_id']
    page.get_by_role('button', name='复制单字', exact=True).click()
    expect(page.locator('.character-strip button')).to_have_count(11)
    page.get_by_role('button', name='删除单字', exact=True).click()
    expect(page.locator('.character-strip button')).to_have_count(10)
    page.get_by_role('button', name='选择第1字明', exact=True).click()
    page.keyboard.press('ArrowRight')
    moved = project()
    assert moved['glyphs'][0]['transform']['x'] == first['x'] + 1
    page.screenshot(path=str(output / 'studio-desktop.png'))
    page.get_by_role('button', name='关闭字形调整').click()
    expect(page.get_by_text('草稿已保存到本机', exact=True)).to_be_visible()
    page.reload()
    page.wait_for_load_state('networkidle')
    expect(page.locator('.character-strip button')).to_have_count(10)
    expect(page.get_by_label('项目名称')).to_have_value('山居秋暝')
    assert project()['glyphs'][0]['transform']['x'] == first['x'] + 1

    # PNG resolution, transparent background and actual ink pixels.
    page.get_by_role('button', name='导出作品', exact=True).click()
    page.get_by_label('透明背景').check()
    with page.expect_download() as download:
        page.get_by_role('button', name='下载 PNG', exact=True).click()
    png = Image.open(download.value.path()).convert('RGBA')
    assert png.size == (original['canvas']['width'] * 2, original['canvas']['height'] * 2)
    assert png.getpixel((0, 0))[3] == 0
    assert png.getchannel('A').getbbox() is not None
    png.save(output / 'studio-export.png')

    # Partial missing glyphs preserve a cell; total failure must preserve artwork.
    page.get_by_label('集字内容').fill('山😀水')
    page.get_by_role('button', name='横排', exact=True).click()
    page.get_by_role('button', name='生成作品', exact=True).click()
    expect(page.locator('.composer .feedback')).to_contain_text('缺字「😀」')
    partial = project()
    assert len(partial['glyphs']) == 2
    assert partial['glyphs'][1]['transform']['x'] - partial['glyphs'][0]['transform']['x'] == 344
    page.get_by_label('集字内容').fill('😀')
    page.get_by_role('button', name='生成作品', exact=True).click()
    expect(page.locator('.composer .feedback')).to_contain_text('未找到可用字形')
    assert len(project()['glyphs']) == 2

    # Large text and invalid layout inputs must not mutate the artwork.
    page.get_by_label('集字内容').fill('山' * 1001)
    expect(page.get_by_role('button', name='生成作品', exact=True)).to_be_disabled()
    page.get_by_label('集字内容').fill('山水')
    page.get_by_label('每行或列字数').fill('0')
    page.get_by_role('button', name='生成作品', exact=True).click()
    expect(page.locator('.composer .feedback')).to_contain_text('有效的排版数值')
    page.get_by_label('每行或列字数').fill('5')

    # Grid flow and source switching.
    page.get_by_label('集字内容').fill('山水\n清音')
    page.get_by_role('button', name='方格', exact=True).click()
    page.get_by_label('每行或列字数').fill('2')
    page.get_by_role('button', name='生成作品', exact=True).click()
    expect(page.locator('.composer .feedback')).to_contain_text('已排入 4 字')
    grid = project()['glyphs']
    assert grid[0]['transform']['y'] == grid[1]['transform']['y']
    assert grid[2]['transform']['y'] > grid[0]['transform']['y']
    page.get_by_label('集字内容').fill('春眠不觉晓')
    page.locator('.composer').get_by_label('书体', exact=True).select_option('草书')
    page.get_by_label('字形来源').select_option('original')
    page.get_by_role('button', name='生成作品', exact=True).click()
    expect(page.locator('.composer .feedback')).to_contain_text('已排入')
    originals = project()['glyphs']
    assert all(g['provenance']['type'] == 'original' for g in originals)
    for glyph in originals:
        assert glyph['asset']['processing'] == 'ink-mask'
        ink = Image.open(io.BytesIO(base64.b64decode(glyph['asset']['url'].split(',')[1]))).convert('RGBA')
        assert ink.getpixel((0, 0))[3] == 0
        assert ink.getchannel('A').getbbox() is not None

    # Import a saved project, reject malformed data before replacing the current work.
    page.on('dialog', lambda dialog: dialog.accept())
    file_input = page.locator('input[type=file]')
    file_input.set_input_files({'name': 'restored.json', 'mimeType': 'application/json', 'buffer': json.dumps(original).encode()})
    expect(page.locator('.character-strip button')).to_have_count(10)
    expect(page.get_by_role('button', name='竖排', exact=True)).to_have_attribute('aria-pressed', 'true')
    expect(page.get_by_label('字形来源')).to_have_value('fonts')
    bad = {**original, 'canvas': {**original['canvas'], 'width': -1}}
    file_input.set_input_files({'name': 'bad.json', 'mimeType': 'application/json', 'buffer': json.dumps(bad).encode()})
    expect(page.locator('.toolbar-status')).to_contain_text('无效')
    expect(page.locator('.character-strip button')).to_have_count(10)

    # Search produces the requested character after changing the query and style.
    page.get_by_role('button', name='查字', exact=True).click()
    page.get_by_label('搜索字形').fill('静')
    expect(page.locator('.glyph-grid .glyph-card')).to_have_count(3, timeout=15000)
    page.locator('.glyph-browser').get_by_label('书体', exact=True).select_option('楷书')
    expect(page.locator('.glyph-grid .glyph-card')).to_have_count(1)
    page.locator('.glyph-card').click()
    expect(page.locator('.character-strip button')).to_have_count(11)
    page.get_by_role('button', name='关闭字形调整').click()
    page.get_by_role('button', name='撤销', exact=True).click()
    expect(page.locator('.character-strip button')).to_have_count(10)
    page.get_by_role('button', name='集字', exact=True).click()

    # Touch-sized layout has no horizontal page overflow and keeps both panels usable.
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    expect(page.get_by_label('集字内容')).to_be_visible()
    page.screenshot(path=str(output / 'studio-mobile-editor.png'))
    page.get_by_role('button', name='作品预览').click()
    expect(page.locator('.paper-frame')).to_be_visible()
    page.screenshot(path=str(output / 'studio-mobile-preview.png'))
    page.get_by_role('button', name='选择第1字明').click()
    expect(page.get_by_label('字形调整', exact=True)).to_be_visible()
    page.get_by_role('button', name='关闭字形调整').click()
    assert not errors, errors
    print('PASS: composition, actual canvas selection, replacement, history, duplicate/delete, keyboard, draft restore, PNG alpha/resolution, missing glyphs, validation, original sources, JSON import, live search and mobile layout')
    browser.close()
