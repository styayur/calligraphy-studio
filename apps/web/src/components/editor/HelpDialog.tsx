import { BookOpenCheck, Check, Copy, FileType2, FolderInput, Scale, Sparkles, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Button } from '../ui'

type HelpTab = 'start' | 'fonts' | 'licenses' | 'static'

const KEYWORDS: Record<string, string[]> = {
  楷书: ['霞鹜文楷', 'LXGW WenKai', 'Ma Shan Zheng', 'AR PL KaitiM', 'FandolKai', '楷书 open font'],
  行书: ['Zhi Mang Xing', 'Klee One', 'LXGW WenKai', '行书 open font', 'Xingkai font'],
  草书: ['Liu Jian Mao Cao', 'Cursive Chinese Calligraphy Dataset', '草书 open font', 'Caoshu font'],
  开源检索: ['Google Fonts chinese handwriting', 'SIL OFL Chinese fonts', 'Open Source Chinese Fonts', 'github chinese calligraphy font'],
  非商用: ['free for personal use Chinese font', 'non-commercial Chinese calligraphy font', 'CC BY-NC font'],
}

const MANIFEST_EXAMPLE = `{
  "fonts": [
    {
      "id": "local-kai",
      "enabled": true,
      "family": "Your Kai Font",
      "designer": "Designer name",
      "style": "楷书",
      "path": "D:/fonts/YourKai.ttf",
      "license": "Replace with exact license",
      "rights": {
        "commercial_use": false,
        "derivatives_allowed": false,
        "redistribution_allowed": false,
        "research_use": true
      }
    }
  ]
}`

const CLI_EXAMPLE = `python -m app.cli import-font-manifest --manifest samples\\fonts\\local-fonts.json --characters 山水春眠不觉晓`

function TabButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-md px-3 py-2 text-left text-xs font-medium transition ${active ? 'bg-ink text-paper' : 'bg-black/5 text-ink/65 hover:bg-black/10'}`}
    >
      {children}
    </button>
  )
}

export function HelpDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [tab, setTab] = useState<HelpTab>('start')
  const [keyword, setKeyword] = useState('')
  const [copied, setCopied] = useState('')
  const visibleKeywords = useMemo<Array<[string, string[]]>>(() => {
    const query = keyword.trim().toLowerCase()
    return Object.entries(KEYWORDS)
      .map(([group, values]) => [
        group,
        query ? values.filter((value) => value.toLowerCase().includes(query)) : values,
      ] as [string, string[]])
      .filter(([, values]) => values.length > 0)
  }, [keyword])

  if (!open) return null

  const copy = async (value: string) => {
    await navigator.clipboard.writeText(value)
    setCopied(value)
    window.setTimeout(() => setCopied(''), 1200)
  }

  return (
    <div className="fixed inset-0 z-[80] grid place-items-center bg-ink/25 p-5 backdrop-blur-sm" onMouseDown={onClose}>
      <section className="panel-scroll flex max-h-[86vh] w-[920px] overflow-hidden rounded-2xl border border-black/10 bg-[#f7f2e8] shadow-2xl" onMouseDown={(event) => event.stopPropagation()}>
        <aside className="w-[190px] shrink-0 border-r border-black/10 bg-[#ece5d8] p-4">
          <div className="mb-5">
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-cinnabar">Help</p>
            <h2 className="font-display text-2xl">使用帮助</h2>
          </div>
          <div className="grid gap-2">
            <TabButton active={tab === 'start'} onClick={() => setTab('start')}><Sparkles className="mr-2 inline h-3.5 w-3.5" />快速上手</TabButton>
            <TabButton active={tab === 'fonts'} onClick={() => setTab('fonts')}><FolderInput className="mr-2 inline h-3.5 w-3.5" />导入本地字库</TabButton>
            <TabButton active={tab === 'licenses'} onClick={() => setTab('licenses')}><Scale className="mr-2 inline h-3.5 w-3.5" />字体授权</TabButton>
            <TabButton active={tab === 'static'} onClick={() => setTab('static')}><BookOpenCheck className="mr-2 inline h-3.5 w-3.5" />GitHub Pages</TabButton>
          </div>
        </aside>

        <div className="panel-scroll min-w-0 flex-1 overflow-y-auto">
          <header className="sticky top-0 z-10 flex items-center justify-between border-b border-black/10 bg-[#f7f2e8]/95 px-6 py-4 backdrop-blur">
            <div>
              <p className="text-xs font-semibold text-ink/70">
                {tab === 'start' && '从搜字到作品'}
                {tab === 'fonts' && '把本地 TTF / OTF 变成 Glyph'}
                {tab === 'licenses' && '商用、非商用和再分发'}
                {tab === 'static' && 'GitHub Pages 静态演示说明'}
              </p>
              <p className="mt-1 text-[11px] text-ink/40">Calligraphy Studio · 当前版本 0.3</p>
            </div>
            <Button variant="ghost" size="icon" onClick={onClose} aria-label="关闭帮助"><X className="h-4 w-4" /></Button>
          </header>

          <div className="space-y-6 p-6 text-sm leading-6 text-ink/70">
            {tab === 'start' && (
              <>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    ['01', '搜索', '按字、书家、书体、朝代或数据源筛选。'],
                    ['02', '组合', '点击或拖入画布，调整图层、旋转、缩放与 Multiply。'],
                    ['03', '导出', '保存项目 JSON、导出 PNG，或使用批量文本集字。'],
                  ].map(([number, title, text]) => (
                    <div key={number} className="rounded-xl border border-black/10 bg-white/55 p-4">
                      <span className="font-mono text-xs text-cinnabar">{number}</span>
                      <h3 className="mt-2 font-semibold text-ink">{title}</h3>
                      <p className="mt-1 text-xs leading-5 text-ink/55">{text}</p>
                    </div>
                  ))}
                </div>
                <div className="rounded-xl border border-black/10 bg-white/50 p-4">
                  <h3 className="font-semibold text-ink">批量文本集字</h3>
                  <p className="mt-1 text-xs text-ink/55">点击顶部“批量集字”，可建立顺序网格、横排和竖排右起布局。每批只占用一个撤销步骤。</p>
                </div>
                <div className="rounded-xl border border-black/10 bg-white/50 p-4">
                  <h3 className="font-semibold text-ink">缺字处理</h3>
                  <p className="mt-1 text-xs text-ink/55">找不到真实字形时，可启用 Hanzi Writer 结构替补。结果会明确标记为 <code>fallback</code>，不会冒充书法真迹。</p>
                </div>
              </>
            )}

            {tab === 'fonts' && (
              <>
                <div className="grid grid-cols-4 gap-3">
                  {[
                    ['1', '下载字体', '获取 TTF / OTF 与 LICENSE。'],
                    ['2', '检查授权', '确认商用、演绎、再分发字段。'],
                    ['3', '写清单', '将本地路径写入 JSON manifest。'],
                    ['4', '执行导入', '运行 import-font-manifest CLI。'],
                  ].map(([number, title, text]) => (
                    <div key={number} className="rounded-xl border border-black/10 bg-white/55 p-3">
                      <span className="grid h-7 w-7 place-items-center rounded-full bg-ink text-xs text-paper">{number}</span>
                      <h3 className="mt-2 text-xs font-semibold text-ink">{title}</h3>
                      <p className="mt-1 text-[11px] leading-4 text-ink/50">{text}</p>
                    </div>
                  ))}
                </div>

                <div>
                  <h3 className="font-semibold text-ink">按书体搜索关键词</h3>
                  <input value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="搜索：楷书、行书、草书、OFL、非商用…" className="mt-3 h-9 w-full rounded-md border border-black/10 bg-white/75 px-3 text-xs outline-none ring-cinnabar/15 focus:ring-2" />
                  <div className="mt-3 space-y-3">
                    {visibleKeywords.map(([group, values]) => (
                      <div key={group}>
                        <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-ink/45">{group}</p>
                        <div className="flex flex-wrap gap-2">
                          {values.map((value) => (
                            <button key={value} type="button" onClick={() => copy(value)} className="inline-flex items-center gap-1 rounded-full border border-black/10 bg-white/65 px-2.5 py-1 text-[11px] text-ink/65 hover:border-cinnabar/30">
                              {copied === value ? <Check className="h-3 w-3 text-emerald-700" /> : <Copy className="h-3 w-3" />}
                              {value}
                            </button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h3 className="mb-2 font-semibold text-ink">清单示例</h3>
                    <pre className="panel-scroll overflow-auto rounded-xl bg-[#241f1a] p-4 text-[11px] leading-5 text-[#f0e9da]"><code>{MANIFEST_EXAMPLE}</code></pre>
                  </div>
                  <div>
                    <h3 className="mb-2 font-semibold text-ink">导入命令</h3>
                    <pre className="panel-scroll overflow-auto rounded-xl bg-[#241f1a] p-4 text-[11px] leading-5 text-[#f0e9da]"><code>{CLI_EXAMPLE}</code></pre>
                    <p className="mt-3 text-xs text-ink/50">仅限本地授权字体时可加 <code>--commercial-only</code> 排除非商用条目。字体文件绝不通过网页上传到第三方。</p>
                  </div>
                </div>
              </>
            )}

            {tab === 'licenses' && (
              <div className="space-y-4">
                <div className="rounded-xl border border-emerald-900/15 bg-emerald-900/5 p-4">
                  <h3 className="flex items-center gap-2 font-semibold text-emerald-950"><FileType2 className="h-4 w-4" /> OFL-1.1</h3>
                  <p className="mt-2 text-xs leading-5">通常允许商用、嵌入和再分发；字体软件修改版仍受 OFL 约束，需要遵守保留字体名规则。使用字体制作的文档本身不强制采用 OFL。</p>
                </div>
                <div className="rounded-xl border border-sky-900/15 bg-sky-900/5 p-4">
                  <h3 className="font-semibold text-sky-950">MIT / Apache-2.0 / GPL with Font Exception</h3>
                  <p className="mt-2 text-xs leading-5">允许商业使用，但必须保留对应声明。GPL 字体必须特别确认是否包含 Font Exception；没有例外时不要把字体直接嵌入网页或分发应用。</p>
                </div>
                <div className="rounded-xl border border-amber-900/20 bg-amber-900/5 p-4">
                  <h3 className="font-semibold text-amber-950">CC BY-NC / CC BY-NC-ND</h3>
                  <p className="mt-2 text-xs leading-5">仅非商业用途。ND 还禁止演绎作品，因此不能作为 AI 字形生成的训练或变形参考。系统会保留 NC/ND 标记，但使用者仍需自行完成法律判断。</p>
                </div>
                <div className="rounded-xl border border-black/10 bg-white/50 p-4 text-xs leading-5">
                  详细字段和协议说明见仓库中的 <code>docs/FONT_LICENSES.md</code>。不确定时把字段设为 <code>null</code>，不要默认允许。
                </div>
              </div>
            )}

            {tab === 'static' && (
              <div className="space-y-4 text-xs leading-6">
                <p>GitHub Pages 只能托管静态资源，不能运行 FastAPI、SQLite 或本地字体导入命令。公开的 GitHub.io 版本使用预导出的 Glyph、元数据和相似度数据，因此搜索、批量集字、图层编辑、JSON 和 PNG 导出可直接使用。</p>
                <p>服务端项目保存、实时重新建库和本地字体导入不会在公开静态站点执行。保存作品请使用“保存 JSON”。</p>
                <p>需要完整导入能力时，在本地运行 API 与 Web；需要公网完整功能时，应把 API 单独部署到支持持久存储和对象存储的平台。</p>
              </div>
            )}
          </div>
        </div>
      </section>
    </div>
  )
}
