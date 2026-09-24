import { Download, FolderOpen, MoreHorizontal, Redo2, Undo2 } from 'lucide-react'
import { ChangeEvent, useRef, useState } from 'react'
import { exportStagePng } from '../../canvas/stageExport'
import { useEditorStore } from '../../stores/editor'
import { validateProject } from '../../lib/project'
import { saveFile } from '../../lib/download'
import { Button } from '../ui'

export function Toolbar() {
  const fileRef = useRef<HTMLInputElement>(null)
  const [status, setStatus] = useState('')
  const [exportOpen, setExportOpen] = useState(false)
  const [transparent, setTransparent] = useState(false)
  const [scale, setScale] = useState(2)
  const {
    projectName,
    project,
    past,
    future,
    localStatus,
    setProjectName,
    newProject,
    undo,
    redo,
    loadProject,
  } = useEditorStore()
  const exportJson = async () => {
    const blob = new Blob([JSON.stringify({ name: projectName, ...project }, null, 2)], {
      type: 'application/json',
    })
    try {
      const result = await saveFile(`${projectName || '集字作品'}.json`, blob)
      setStatus(
        result === 'shared' ? '项目已交给系统保存或分享' : '项目已下载，可用于备份或继续编辑',
      )
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '导出未完成，请重试')
    }
  }
  const exportPng = async () => {
    try {
      const response = await fetch(exportStagePng({ scale, transparent }))
      const result = await saveFile(`${projectName || '集字作品'}.png`, await response.blob())
      setStatus(result === 'shared' ? '作品已交给系统保存或分享' : '作品已导出')
      setExportOpen(false)
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '导出失败，请重试')
    }
  }
  const loadFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    try {
      if (file.size > 40 * 1024 * 1024) throw new Error('项目文件超过 40 MB，请选择较小的项目')
      const value = JSON.parse(await file.text())
      const parsed = validateProject(value)
      if (
        project.glyphs.length &&
        !window.confirm('载入将替换当前作品。建议先下载项目备份，是否继续？')
      )
        return
      loadProject(
        typeof value.name === 'string' ? value.name : file.name.replace(/\.json$/i, ''),
        parsed,
      )
      setStatus('项目已载入')
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '项目载入失败')
    } finally {
      event.target.value = ''
    }
  }
  return (
    <header className="studio-header">
      <div className="brand-mark" aria-label="集字工作台">
        集
      </div>
      <div className="project-heading">
        <input
          value={projectName}
          onChange={(e) => setProjectName(e.target.value)}
          aria-label="项目名称"
        />
        <span role="status">{localStatus}</span>
      </div>
      <div className="history-actions">
        <Button
          variant="ghost"
          size="icon"
          title="撤销 Ctrl+Z"
          aria-label="撤销"
          disabled={!past.length}
          onClick={undo}
        >
          <Undo2 size={17} />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          title="重做 Ctrl+Shift+Z"
          aria-label="重做"
          disabled={!future.length}
          onClick={redo}
        >
          <Redo2 size={17} />
        </Button>
      </div>
      <div className="header-spacer" />
      <span className="toolbar-status" role="status">
        {status}
      </span>
      <input
        ref={fileRef}
        type="file"
        accept="application/json,.json"
        className="hidden"
        onChange={loadFile}
      />
      <details className="project-menu">
        <summary aria-label="项目菜单">
          <MoreHorizontal size={19} />
          <span>项目</span>
        </summary>
        <div className="menu-popover">
          <button onClick={exportJson}>下载项目文件</button>
          <button onClick={() => fileRef.current?.click()}>载入项目文件</button>
          <button disabled={!past.length} onClick={undo}>
            撤销上一步
          </button>
          <button disabled={!future.length} onClick={redo}>
            重做上一步
          </button>
          <button
            onClick={() => {
              if (
                !project.glyphs.length ||
                window.confirm('新建会清空当前草稿，请先下载需要保留的作品。是否继续？')
              ) {
                newProject()
                setStatus('已新建作品')
              }
            }}
          >
            新建空白作品
          </button>
          <p>项目文件保留字形、排版和来源，可再次编辑。</p>
        </div>
      </details>
      <Button variant="secondary" className="save-project-button" onClick={exportJson}>
        <FolderOpen size={15} />
        保存项目
      </Button>
      <div className="export-wrapper">
        <Button
          onClick={() => setExportOpen(!exportOpen)}
          disabled={!project.glyphs.length}
          aria-expanded={exportOpen}
        >
          <Download size={15} />
          导出作品
        </Button>
        {exportOpen && (
          <div className="export-popover" role="dialog" aria-label="导出作品设置">
            <div className="section-title">
              <h3>导出 PNG</h3>
              <button aria-label="关闭导出设置" onClick={() => setExportOpen(false)}>
                ×
              </button>
            </div>
            <label>
              导出尺寸
              <select
                aria-label="导出尺寸"
                value={scale}
                onChange={(e) => setScale(Number(e.target.value))}
              >
                <option value={1}>
                  原尺寸 · {project.canvas.width} × {project.canvas.height}
                </option>
                <option value={2}>
                  2 倍 · {project.canvas.width * 2} × {project.canvas.height * 2}
                </option>
              </select>
            </label>
            <label className="check-field">
              <input
                type="checkbox"
                checked={transparent}
                onChange={(e) => setTransparent(e.target.checked)}
              />
              透明背景
            </label>
            <p className="field-hint">导出不包含选框。图片字形的清晰度受原图分辨率限制。</p>
            <Button className="w-full" onClick={exportPng}>
              下载 PNG
            </Button>
          </div>
        )}
      </div>
    </header>
  )
}
