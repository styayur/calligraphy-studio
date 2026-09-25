import Konva from 'konva'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Image as KonvaImage, Layer, Rect, Stage, Text, Transformer } from 'react-konva'
import { GLYPH_DRAG_TYPE } from '../components/glyph-browser/GlyphBrowser'
import { useEditorStore } from '../stores/editor'
import type { Glyph, GlyphInstance } from '../types'
import { registerStageExporter } from './stageExport'
import { useHtmlImage } from './useImage'

function GlyphImage({
  glyph,
  nodeRef,
  onReady,
}: {
  glyph: GlyphInstance
  nodeRef: (node: Konva.Node | null) => void
  onReady: () => void
}) {
  const image = useHtmlImage(glyph.asset.url)
  const selectGlyph = useEditorStore((state) => state.selectGlyph)
  const beginHistory = useEditorStore((state) => state.beginHistory)
  const setGlyphTransform = useEditorStore((state) => state.setGlyphTransform)

  useEffect(() => {
    if (image) onReady()
  }, [image, onReady])

  const shared = {
    x: glyph.transform.x,
    y: glyph.transform.y,
    width: glyph.asset.width,
    height: glyph.asset.height,
    offsetX: glyph.asset.width / 2,
    offsetY: glyph.asset.height / 2,
    scaleX: glyph.transform.scaleX,
    scaleY: glyph.transform.scaleY,
    rotation: glyph.transform.rotation,
    skewX: glyph.transform.skewX,
    skewY: glyph.transform.skewY,
    opacity: glyph.appearance.opacity,
    globalCompositeOperation: glyph.appearance.blendMode as GlobalCompositeOperation,
    draggable: true,
    onClick: () => selectGlyph(glyph.id),
    onTap: () => selectGlyph(glyph.id),
    onDragStart: () => {
      beginHistory()
      selectGlyph(glyph.id)
    },
    onDragMove: (event: Konva.KonvaEventObject<DragEvent>) => {
      setGlyphTransform(
        glyph.id,
        { x: event.target.x(), y: event.target.y() },
        { recordHistory: false },
      )
    },
    onTransformStart: () => {
      beginHistory()
      selectGlyph(glyph.id)
    },
    onTransformEnd: (event: Konva.KonvaEventObject<Event>) => {
      const node = event.target as Konva.Image
      setGlyphTransform(
        glyph.id,
        {
          x: node.x(),
          y: node.y(),
          scaleX: node.scaleX(),
          scaleY: node.scaleY(),
          rotation: node.rotation(),
          skewX: node.skewX(),
          skewY: node.skewY(),
        },
        { recordHistory: false },
      )
    },
  }

  if (!image) {
    return (
      <Text
        ref={nodeRef}
        text={glyph.character}
        fontFamily="KaiTi, STKaiti, serif"
        fontSize={160}
        fill="#2a241f"
        {...shared}
      />
    )
  }

  return <KonvaImage ref={nodeRef} image={image} {...shared} />
}

export function GlyphCanvas() {
  const containerRef = useRef<HTMLDivElement>(null)
  const stageRef = useRef<Konva.Stage>(null)
  const transformerRef = useRef<Konva.Transformer>(null)
  const nodeRefs = useRef<Record<string, Konva.Node | null>>({})
  const [displayScale, setDisplayScale] = useState(1)
  const [nodeVersion, setNodeVersion] = useState(0)
  const handleNodeReady = useCallback(() => setNodeVersion((value) => value + 1), [])
  const project = useEditorStore((state) => state.project)
  const selectedId = useEditorStore((state) => state.selectedId)
  const selectGlyph = useEditorStore((state) => state.selectGlyph)
  const addGlyph = useEditorStore((state) => state.addGlyph)

  useEffect(() => {
    const element = containerRef.current
    if (!element) return
    const update = () => {
      const width = element.clientWidth - 48
      const height = element.clientHeight - 48
      setDisplayScale(
        Math.max(
          0.01,
          Math.min(1, width / project.canvas.width, height / project.canvas.height),
        ),
      )
    }
    update()
    const observer = new ResizeObserver(update)
    observer.observe(element)
    return () => observer.disconnect()
  }, [project.canvas.width, project.canvas.height])

  useEffect(() => {
    const transformer = transformerRef.current
    if (!transformer) return
    const node = selectedId ? nodeRefs.current[selectedId] : null
    transformer.nodes(node ? [node] : [])
    transformer.getLayer()?.batchDraw()
  }, [selectedId, project.glyphs, nodeVersion])

  useEffect(() => {
    registerStageExporter(({ scale, transparent }) => {
      const stage = stageRef.current
      const transformer = transformerRef.current
      if (!stage) throw new Error('画布尚未准备好')
      const logical = useEditorStore.getState().project.canvas
      if (logical.width * logical.height * scale * scale > 40_000_000)
        throw new Error('导出尺寸过大，请选择原尺寸或减小纸面')
      if (stage.find('Image').length !== useEditorStore.getState().project.glyphs.length)
        throw new Error('部分字形图片尚未加载，请稍后重试或检查字库连接')
      const background = stage.findOne('.paper-background')
      const transformerWasVisible = transformer?.visible() ?? false
      transformer?.visible(false)
      if (transparent) background?.visible(false)
      try {
        const snapshot = stage.toCanvas({ pixelRatio: scale / stage.scaleX() })
        // Canvas bitmap dimensions round fractional viewport sizes. Restore exact
        // requested export dimensions (at most a one-pixel resampling correction).
        const output = document.createElement('canvas')
        output.width = Math.round(logical.width * scale)
        output.height = Math.round(logical.height * scale)
        output.getContext('2d')!.drawImage(snapshot, 0, 0, output.width, output.height)
        return output.toDataURL('image/png')
      } finally {
        transformer?.visible(transformerWasVisible)
        background?.visible(true)
        stage.batchDraw()
      }
    })
    return () => registerStageExporter(null)
  }, [])

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    const raw = event.dataTransfer.getData(GLYPH_DRAG_TYPE)
    if (!raw) return
    try {
      const glyph = JSON.parse(raw) as Glyph
      const rect = stageRef.current?.container().getBoundingClientRect()
      if (!rect) return
      const left = rect.left
      const top = rect.top
      addGlyph(
        glyph,
        Math.max(0, Math.min(project.canvas.width, (event.clientX - left) / displayScale)),
        Math.max(0, Math.min(project.canvas.height, (event.clientY - top) / displayScale)),
      )
    } catch {
      // Ignore unrelated drag payloads.
    }
  }

  return (
    <div
      ref={containerRef}
      className="paper-grid relative flex min-h-0 min-w-0 flex-1 items-center justify-center overflow-hidden"
      onDragOver={(event) => {
        if (event.dataTransfer.types.includes(GLYPH_DRAG_TYPE)) {
          event.preventDefault()
          event.dataTransfer.dropEffect = 'copy'
        }
      }}
      onDrop={handleDrop}
    >
      <div
        className="paper-frame relative"
        style={{
          width: project.canvas.width * displayScale,
          height: project.canvas.height * displayScale,
        }}
      >
        <div
          style={{
            width: project.canvas.width * displayScale,
            height: project.canvas.height * displayScale,
          }}
        >
          <Stage
            ref={stageRef}
            width={project.canvas.width * displayScale}
            height={project.canvas.height * displayScale}
            scaleX={displayScale}
            scaleY={displayScale}
            onMouseDown={(event) => {
              if (event.target === event.target.getStage()) selectGlyph(null)
            }}
            onTouchStart={(event) => {
              if (event.target === event.target.getStage()) selectGlyph(null)
            }}
          >
            <Layer listening={false}>
              <Rect
                name="paper-background"
                x={0}
                y={0}
                width={project.canvas.width}
                height={project.canvas.height}
                fill={project.canvas.background}
              />
            </Layer>
            <Layer>
              {project.glyphs.map((glyph) => (
                <GlyphImage
                  key={glyph.id}
                  glyph={glyph}
                  nodeRef={(node) => {
                    nodeRefs.current[glyph.id] = node
                  }}
                  onReady={handleNodeReady}
                />
              ))}
            </Layer>
            <Layer>
              <Transformer
                ref={transformerRef}
                rotateEnabled
                keepRatio={false}
                borderStroke="#48675a"
                borderStrokeWidth={1.5}
                anchorStroke="#48675a"
                anchorFill="#ffffff"
                anchorSize={8}
                anchorCornerRadius={2}
                boundBoxFunc={(oldBox, newBox) =>
                  newBox.width < 12 || newBox.height < 12 ? oldBox : newBox
                }
              />
            </Layer>
          </Stage>
        </div>
      </div>
      {project.glyphs.length === 0 && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="canvas-empty">
            <div className="empty-character">字</div>
            <p>把喜欢的文字，集成一幅作品</p>
            <span>输入一句诗或一段文字，点击「生成作品」</span>
          </div>
        </div>
      )}
    </div>
  )
}
