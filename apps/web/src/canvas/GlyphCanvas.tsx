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
  selected,
  nodeRef,
  onReady,
}: {
  glyph: GlyphInstance
  selected: boolean
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
      setDisplayScale(Math.min(1, width / project.canvas.width, height / project.canvas.height))
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
    registerStageExporter(() => {
      const stage = stageRef.current
      const transformer = transformerRef.current
      if (!stage) throw new Error('Canvas is not ready')
      const transformerWasVisible = transformer?.visible() ?? false
      transformer?.visible(false)
      const result = stage.toDataURL({ pixelRatio: 1, mimeType: 'image/png' })
      transformer?.visible(transformerWasVisible)
      stage.batchDraw()
      return result
    })
    return () => registerStageExporter(null)
  }, [])

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    const raw = event.dataTransfer.getData(GLYPH_DRAG_TYPE)
    if (!raw) return
    try {
      const glyph = JSON.parse(raw) as Glyph
      const rect = containerRef.current?.getBoundingClientRect()
      if (!rect) return
      const frameWidth = project.canvas.width * displayScale
      const frameHeight = project.canvas.height * displayScale
      const left = rect.left + (rect.width - frameWidth) / 2
      const top = rect.top + (rect.height - frameHeight) / 2
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
        className="relative shadow-[0_24px_80px_rgba(42,32,22,0.18)]"
        style={{
          width: project.canvas.width * displayScale,
          height: project.canvas.height * displayScale,
        }}
      >
        <div
          style={{
            width: project.canvas.width,
            height: project.canvas.height,
            transform: `scale(${displayScale})`,
            transformOrigin: 'top left',
          }}
        >
          <Stage
            ref={stageRef}
            width={project.canvas.width}
            height={project.canvas.height}
            onMouseDown={(event) => {
              if (event.target === event.target.getStage()) selectGlyph(null)
            }}
            onTouchStart={(event) => {
              if (event.target === event.target.getStage()) selectGlyph(null)
            }}
          >
            <Layer listening={false}>
              <Rect
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
                  selected={glyph.id === selectedId}
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
                borderStroke="#a23a2b"
                borderStrokeWidth={1.5}
                anchorStroke="#a23a2b"
                anchorFill="#fff8ed"
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
          <div className="rounded-xl border border-dashed border-ink/20 bg-white/60 px-6 py-5 text-center backdrop-blur-sm">
            <p className="font-display text-3xl text-ink/65">落笔于此</p>
            <p className="mt-1 text-xs text-ink/45">从左侧点击或拖入字形</p>
          </div>
        </div>
      )}
    </div>
  )
}