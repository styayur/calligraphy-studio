import { CircleHelp, Cloud, Download, FileJson, FolderOpen, ListPlus, Redo2, RotateCcw, Undo2 } from 'lucide-react'
import { ChangeEvent, useRef, useState } from 'react'
import { createProject, isStaticMode, updateProject } from '../../api/client'
import { exportStagePng } from '../../canvas/stageExport'
import { useEditorStore } from '../../stores/editor'
import type { ProjectDocument } from '../../types'
import { Button } from '../ui'
import { HelpDialog } from './HelpDialog'

function download(name: string, href: string) {
  const anchor = document.createElement('a')
  anchor.href = href
  anchor.download = name
  anchor.click()
}

function validateProject(value: unknown): ProjectDocument {
  if (!value || typeof value !== 'object') throw new Error('项目文件不是有效对象')
  const document = value as ProjectDocument
  if (document.version !== 1 || !document.canvas || !Array.isArray(document.glyphs)) {
    throw new Error('仅支持 version 1 的 Calligraphy Studio 项目')
  }
  return document
}

export function Toolbar() {
  const fileRef = useRef<HTMLInputElement>(null)
  const [status, setStatus] = useState('')
  const [helpOpen, setHelpOpen] = useState(false)
  const projectId = useEditorStore((state) => state.projectId)
  const projectName = useEditorStore((state) => state.projectName)
  const project = useEditorStore((state) => state.project)
  const pastCount = useEditorStore((state) => state.past.length)
  const futureCount = useEditorStore((state) => state.future.length)
  const dirty = useEditorStore((state) => state.dirty)
  const setProjectName = useEditorStore((state) => state.setProjectName)
  const newProject = useEditorStore((state) => state.newProject)
  const undo = useEditorStore((state) => state.undo)
  const redo = useEditorStore((state) => state.redo)
  const loadProject = useEditorStore((state) => state.loadProject)
  const markSaved = useEditorStore((state) => state.markSaved)
  const setBatchOpen = useEditorStore((state) => state.setBatchOpen)

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(project, null, 2)], { type: 'application/json' })
    download(`${projectName || 'calligraphy-project'}.json`, URL.createObjectURL(blob))
    setStatus('JSON 已导出')
  }

  const exportPng = () => {
    try {
      download(`${projectName || 'calligraphy-artwork'}.png`, exportStagePng())
      setStatus('PNG 已导出')
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '导出失败')
    }
  }

  const saveCloud = async () => {
    setStatus('保存中…')
    try {
      const record = projectId
        ? await updateProject(projectId, projectName, project)
        : await createProject(projectName, project)
      markSaved(record.id)
      setStatus('项目已保存')
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '保存失败')
    }
  }

  const loadFile = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    try {
      const parsed = validateProject(JSON.parse(await file.text()))
      loadProject(file.name.replace(/\.json$/i, ''), parsed)
      setStatus('项目已载入')
    } catch (error) {
      setStatus(error instanceof Error ? error.message : '项目载入失败')
    } finally {
      event.target.value = ''
    }
  }

  return (
    <header className="flex h-14 shrink-0 items-center gap-2 border-b border-black/10 bg-[#f4efe5]/95 px-3 shadow-sm backdrop-blur">
      <div className="flex items-center gap-1 border-r border-black/10 pr-3">
        <Button variant="ghost" size="icon" title="新建项目" onClick={newProject}><RotateCcw className="h-4 w-4" /></Button>
        <Button variant="ghost" size="icon" title="撤销" disabled={!pastCount} onClick={undo}><Undo2 className="h-4 w-4" /></Button>
        <Button variant="ghost" size="icon" title="重做" disabled={!futureCount} onClick={redo}><Redo2 className="h-4 w-4" /></Button>
      </div>

      <div className="flex min-w-0 flex-1 items-center gap-3 pl-1">
        <div className="grid h-9 w-9 place-items-center rounded-md bg-ink font-display text-xl text-paper">集</div>
        <div className="min-w-0">
          <input
            value={projectName}
            onChange={(event) => setProjectName(event.target.value)}
            className="h-6 w-[240px] truncate border-none bg-transparent font-display text-xl outline-none focus:border-b focus:border-cinnabar/40"
            aria-label="项目名称"
          />
          <p className="text-[10px] text-ink/40">
            {dirty ? '存在未保存更改' : '已同步'} · {project.glyphs.length} 个字形 · {project.canvas.width}×{project.canvas.height}
          </p>
        </div>
      </div>

      <span className="max-w-[220px] truncate text-xs text-ink/50">{status}</span>
      <Button variant="ghost" size="icon" onClick={() => setHelpOpen(true)} title="帮助与本地字库导入"><CircleHelp className="h-4 w-4" /></Button>
      <input ref={fileRef} type="file" accept="application/json,.json" className="hidden" onChange={loadFile} />
      <Button variant="secondary" size="sm" onClick={() => fileRef.current?.click()}><FolderOpen className="h-3.5 w-3.5" />载入 JSON</Button>
      <Button variant="secondary" size="sm" onClick={exportJson}><FileJson className="h-3.5 w-3.5" />保存 JSON</Button>
      <Button variant="secondary" size="sm" onClick={() => setBatchOpen(true)}><ListPlus className="h-3.5 w-3.5" />批量集字</Button>
      <Button variant="secondary" size="sm" onClick={saveCloud} disabled={isStaticMode} title={isStaticMode ? 'GitHub Pages 静态版请使用保存 JSON' : '保存到 API'}><Cloud className="h-3.5 w-3.5" />{isStaticMode ? '静态演示' : '保存项目'}</Button>
      <Button size="sm" onClick={exportPng}><Download className="h-3.5 w-3.5" />导出 PNG</Button>
      <HelpDialog open={helpOpen} onClose={() => setHelpOpen(false)} />
    </header>
  )
}