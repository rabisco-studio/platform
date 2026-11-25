# SPEC-001: Scene Graph — Design

**Status:** design:draft (rascunho antecipado; não vinculante até requirements:approved)
**Requisitos:** `requirements.md`

---

## 1. Resumo Executivo

O documento é uma árvore de nós tipados (`Node`) armazenada em memória como arena indexada e persistida em SQLite (ADR-007). Cada nó carrega identidade, posição fracionária, propriedades visuais e referências a conteúdo (tiles ou objetos vetoriais). A árvore é o input do compositor e o alvo das operações (SPEC-003).

## 2. Mapeamento de Requisitos

| FR | Decisão de Design | Componente |
|----|-------------------|------------|
| FR-001 | Enum `NodeKind` com 6 variantes | `scene_engine` |
| FR-002 | Struct `NodeData` com campos tipados | `scene_engine::node` |
| FR-003 | Validação `is_ancestor(target, node)` antes de reparent | `scene_engine::tree` |
| FR-004 | Struct `DocumentMeta` com campos de cor e dimensão | `scene_engine::document` |
| FR-005 | `TileRef { col, row, hash }` e `TileHash` em `core_domain::tile`; `RasterLayerData` em `scene_engine::raster` | `core_domain::tile`, `scene_engine::raster` |
| FR-006 | `VectorObject` com `Shape` enum | `scene_engine::vector` |
| FR-007 | `MaskData` { kind: Raster/Vector, content } | `scene_engine::mask` |
| FR-008 | Flag `isolation` derivada de `blend_mode != PassThrough` (apenas a regra; a composição é da SPEC-004) | `scene_engine::node` |
| FR-009 | JSON Schema em `contracts/document-format/scene.json` | Build + CI |
| FR-010 | `clip_path: Option<VectorObject>` em `NodeData` | `scene_engine::node` |
| FR-011 | `EmbeddedImage { hash, width, height, format }` | `scene_engine::embedded` |
| FR-012 | Apenas reserva: `NodeKind` é `#[non_exhaustive]`; adjustment layers não são implementados no R1 | `scene_engine::node` |

## 3. Arquitetura

### 3.1 Árvore como Arena

```
SceneGraph {
    nodes: Vec<NodeSlot>,        // arena indexada por NodeIndex
    id_to_index: HashMap<NodeId, NodeIndex>,
    root: NodeIndex,
    schema_version: SemVer,
}

NodeSlot {
    id: NodeId,                  // UUID v7
    parent: Option<NodeIndex>,
    first_child: Option<NodeIndex>,
    next_sibling: Option<NodeIndex>,
    order: FractionalIndex,
    data: NodeData,
}

NodeData {
    kind: NodeKind,
    name: String,
    visible: bool,
    locked: bool,
    opacity: f32,                // 0.0–1.0
    blend_mode: BlendMode,
    transform: AffineTransform,  // [a, b, c, d, tx, ty]
    clip_path: Option<VectorObject>,
    mask: Option<MaskData>,
}
```

**Motivo da arena:** cache-friendly para travessia DFS durante composição. Nenhuma alocação por nó (vs. `Box<Node>` + ponteiros).

### 3.2 Tipos de nó

```rust
enum NodeKind {
    Document(DocumentMeta),
    Artboard,
    Group,
    RasterLayer(RasterLayerData),
    VectorLayer(VectorLayerData),
    EmbeddedImage(EmbeddedImageData),
}
```

### 3.3 Tiles

**Propriedade dos tipos:** `TileHash`, `TileCoord`, `TileRef`, `TileData` e o trait `TileStore` (com `InMemoryTileStore`) vivem em `core-domain`, módulo `tile`, porque são tipos de fronteira usados por `scene-engine`, `raster-engine`, `file-engine` e pelas pontes. `RasterLayerData` (mapa de coordenadas para `TileHash`) vive em `scene-engine`. Cache LRU, compressão e remoção sob pressão de memória pertencem à SPEC-006 (`raster-engine`).

```rust
struct TileRef {
    col: u32,
    row: u32,
    hash: TileHash,  // blake3, 32 bytes
}
```

- Tiles 256×256 px, RGBA, alfa pré-multiplicado.
- 8 bits: 256 KiB/tile. 16 bits: 512 KiB/tile.
- Tiles são imutáveis e content-addressable. Edição gera novo tile com novo hash.
- Tile store: `HashMap<TileHash, TileData>` em memória, tabela `tiles` no SQLite.

### 3.4 Índices Fracionários

Implementação baseada em strings lexicograficamente ordenáveis (base 62).
- Inserir entre "a0" e "a1" → "a0V" (ponto médio).
- Rebalanceamento quando o comprimento exceder 16 caracteres.
- Compatível com LWW merge (ADR-009).

### 3.5 Blend Modes

Conjunto R1 (decisão D-003, 19 valores): Normal, Multiply, Screen, Overlay, Darken, Lighten, ColorDodge, ColorBurn, HardLight, SoftLight, Difference, Exclusion, Hue, Saturation, Color, Luminosity, DestinationIn, DestinationOut, PassThrough.

`PassThrough` é exclusivo de grupos. Valores fora deste conjunto são rejeitados na desserialização com erro `UnknownBlendMode` (nunca convertidos em silêncio).

## 4. Modelo de Dados

Esta spec define **estruturas em memória e registros de persistência**, não DDL. O esquema SQLite (tabelas, índices, pragmas) pertence exclusivamente à SPEC-002 e está em `contracts/document-format/hybrid-schema-v1.sql`.

Registros definidos aqui (módulo `scene_engine::records`), consumidos pela SPEC-002:

```rust
struct NodeRecord {
    node_id: NodeId,            // UUID v7
    parent_id: Option<NodeId>,
    kind: NodeKindTag,          // Document | Artboard | Group | RasterLayer | VectorLayer | EmbeddedImage
    order: FractionalIndex,
    name: String,
    visible: bool,
    locked: bool,
    opacity: f32,
    blend_mode: BlendMode,
    transform: AffineTransform, // 6 x f32
    clip_path: Option<Vec<u8>>, // VectorObject serializado
    mask: Option<Vec<u8>>,      // MaskData serializado
    extra: Vec<u8>,             // dados específicos do kind (JSON)
}

struct TileRefRecord { layer_id: NodeId, col: u32, row: u32, hash: TileHash }
struct DocumentMetaRecord { width: u32, height: u32, dpi: u32, color_profile: Vec<u8>, bit_depth: u8, blend_space: BlendSpace }
```

API: `SceneGraph::to_records() -> SceneRecords` e `SceneGraph::from_records(SceneRecords) -> Result<SceneGraph>`. A conversão valida invariantes (ciclos, profundidade, pai existente) e nunca acessa disco.

## 5. Contratos Afetados

| Contrato | Mudança |
|----------|---------|
| `contracts/document-format/scene.json` | **Novo.** JSON Schema da árvore. |
| `contracts/document-format/tile.json`  | **Novo.** Schema do TileRef. |
| `contracts/conformance/scene/`         | **Novo.** Vetores de teste para round-trip. |

## 6. Crates Impactados

| Crate | Responsabilidade |
|-------|-----------------|
| `scene-engine` (novo) | Árvore, nós, travessia, validação de ciclos, registros de persistência (`records`). |
| `core-domain` (módulo `tile`) | `TileHash`, `TileCoord`, `TileRef`, `TileData`, trait `TileStore`, `InMemoryTileStore`. |
| `file-engine` | **Não impactado.** A SPEC-002 consome `NodeRecord` e `TileRefRecord`. |
| `contracts-codegen` | Geração de structs Rust a partir do JSON Schema. |

## 7. Compatibilidade e Migração

- Primeira versão: schema_version "1.0.0". Sem migração.
- Regra futura: todo bump de schema inclui função de migração e arquivo no corpus `tests/compat/`.

## 8. Segurança e Privacidade

- Nenhum dado pessoal na árvore (nomes de camadas são dados do usuário, não PII).
- Tiles não contêm metadados EXIF: strippados na importação.

## 9. Casos de Borda

| Caso | Comportamento |
|------|---------------|
| Documento com 0 camadas | Válido (Artboard sem filhos). UI pode exibir aviso. |
| Tile todo transparente | Não armazenado (otimização: ausência = transparente). |
| Profundidade > 64 | Operação rejeitada com erro `MaxDepthExceeded`. |
| Dois nós com mesmo node_id | Impossível: UUID v7 + verificação no insert. |
| Índice fracionário com > 16 chars | Trigger rebalance automático de todos os irmãos. |
| RasterLayer sem tiles | Válido. Camada vazia. |
| Mask em Document | Rejeitado: mask só aplica a nós não-Document. |

## 10. Estratégia de Verificação

| Tipo | O que verifica | Como |
|------|---------------|------|
| [BEH] | Round-trip, ciclos, propriedades, exclusão | Testes unitários `scene` + testes de integração `file-engine` |
| [VIS] | Composição com transformações herdadas | Golden images no compositor (spec futura) |
| [PERF] | Travessia ≤ 1 ms, abertura ≤ 500 ms | Benchmark com criterion + R-A |
| [CONF] | Schema em sync com código | CI: `cargo test --features conformance` |

## 11. Decisões Técnicas

### TD-001 — Arena vs. Ponteiros
**Alternativas:** (A) Arena indexada, (B) `Box<Node>` com Rc/Arc, (C) ECS (hecs/bevy_ecs).
**Decisão:** (A). Travessia DFS é O(n) com localidade de cache. ECS é overkill sem sistema de componentes dinâmicos.
**Consequência:** Remoção de nó invalida índices; usar geração (generational index) para detectar uso-após-remoção.

### TD-002 — Hash de tiles
**Alternativas:** (A) blake3, (B) SHA-256, (C) xxHash.
**Decisão:** (A) blake3. 2× mais rápido que SHA-256, criptograficamente seguro (suficiente para content-addressing), crate Rust de referência.

### TD-003 — Serialização de Transform
**Alternativas:** (A) 6 floats binários (24 bytes), (B) JSON array, (C) struct com campos nomeados.
**Decisão:** (A) em SQLite (compacto), (C) em JSON Schema (legível).

## 12. Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Arena exige generational index para segurança | Média | Médio | Implementar desde o início com `slotmap` ou similar |
| JSON Schema não expressa todas as invariantes da árvore | Alta | Baixo | Validação programática além do schema |
| Índices fracionários divergem em merge | Baixa | Alto | Testes de propriedades com merge simulado |
