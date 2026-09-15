# Architecture

## Core invariant

前端、项目文件和 API 永远操作 `Glyph`，而不是直接操作任意图片路径。

```ts
interface Glyph {
  id: string
  character: string
  source: { dataset, calligrapher?, style?, dynasty?, work?, license?, rights? }
  asset: { type, url, width, height, bbox }
  transform: { x, y, scaleX, scaleY, rotation, skewX, skewY }
  appearance: { opacity, blendMode }
  provenance: { type: "original" | "font" | "fallback" | "generated", confidence? }
}
```

项目中的每个字形实例额外保存 `glyph_id`，因此同一原始字形可以在一幅作品中出现多次，而几何变换不会污染字形库。

## Layers

```text
DatasetProvider
  ├── MCCDLmdbProvider
  ├── MCCDManifestProvider
  ├── NCCUCursiveProvider
  ├── FontManifestProvider (OFL / open / non-commercial fonts)
  ├── HanziWriterProvider (fallback)
  └── future: PublicDomain / Licensed / UserUpload / Generated
             ↓
GlyphImporter + AssetStore
             ↓
SQLite Glyph Store + visual embeddings
             ↓
FastAPI Glyph / Search / Similarity / Batch API
             ↓
React + Konva 2D Composition Engine
             ↓
Project JSON + PNG + structural fallback
```

Provider 只负责读取原始数据；Importer 负责校验、复制、checksum、维度、bbox、元数据 upsert。前端不知道数据来自 LMDB、字体文件、目录还是 URL。字体字形拥有独立 `font` provenance，不能与历史真迹混为一谈。

## Rights model

`glyph_sources` 保存：

- dataset
- work
- license / license_url
- source_uri
- rights：商业使用、演绎、再分发、研究使用

这是一项硬边界。后续 `GeneratedProvider` 在读取参考字形前必须检查 `derivatives_allowed`，而不是只读取图像 URL。

## Storage

MVP 使用 SQLite 与本地目录：

```text
data/calligraphy.db
data/hanzi-writer/<character>.json
samples/fonts/ofl/<family>/<font>.ttf
storage/assets/<dataset>/<checksum-prefix>/<character>-<checksum>.ext
```

扩展路径：

- SQLite → PostgreSQL
- local assets → S3-compatible object storage
- simple LIKE search → PostgreSQL FTS / Meilisearch
- float32 BLOB embedding → pgvector

这些替换不会改变 Glyph API 的语义。

## Editor

Konva 明确用于 2D layer composition，而不是通用矢量绘图：

- `BackgroundLayer`
- `GlyphLayer`
- `SelectionLayer`（Transformer）

每个 Glyph 图片节点使用 `globalCompositeOperation`，所以 Multiply、Screen、Overlay 可以直接投影到项目 JSON。批量排版先由后端解析文字，再一次性生成多个 `GlyphInstance`，因此整批操作只占一个撤销步骤。

## Phase 1.5 structural fallback

Hanzi Writer 只提供字符结构，不承担书法风格。后端把 stroke paths 转成 SVG，写入 Glyph Store，并把 provenance 固定为 `fallback`。真正的历史字保持 `original`，AI 输出必须为 `generated`。

## Phase 2 visual similarity

`visual-geometry-256-v1` 对裁切、极性归一化后的字形计算 8×8 单元的 ink/edge 统计，生成 256 维 L2 向量。向量随 `glyph_id + model_name + source_checksum` 持久化，cosine similarity 只作为推荐信号，不修改 Glyph provenance。

该版本是离线、可复现的工程基线，不是深度语义模型。未来学习式 encoder 必须使用新的 model name，并保留旧向量以便回滚和对比。

## Deliberate non-goals before phase 3

- 不把 Hanzi Writer 冒充书法生成
- 不把相似字直接伪装成目标字
- 不把 MCCD 作为不可替换核心
- 不实现未经授权的生成式演绎
- 不实现协作和云端权限系统
