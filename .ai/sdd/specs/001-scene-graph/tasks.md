# SPEC-001: Scene Graph — Tasks

**Status:** tasks:draft (rascunho antecipado; não vinculante até design:approved)
**Requisitos:** `requirements.md`
**Design:** `design.md`

---

## Verificação de Prontidão

- [x] requirements.md escrito
- [x] design.md escrito
- [x] Todas as perguntas Q-* respondidas
- [ ] requirements:approved (pendente aprovação humana)
- [ ] design:approved (pendente aprovação humana)

## Cobertura FR → Tarefas

| FR | Tarefa(s) |
|----|-----------|
| FR-001 | T-001, T-002, T-009 |
| FR-002 | T-002 |
| FR-003 | T-003 |
| FR-004 | T-004 |
| FR-005 | T-005 |
| FR-006 | T-006 |
| FR-007 | T-007 |
| FR-008 | T-003 (flag de isolamento) |
| FR-009 | T-008 |
| FR-010 | T-002 (campo clip_path) |
| FR-011 | T-006 (EmbeddedImage como NodeKind) |
| FR-012 | T-001 (`NodeKind` com `#[non_exhaustive]`; sem implementação no R1) |

## Tarefas

### T-001 — Definir structs do Scene Graph (arena + nós)
**Requisito:** FR-001, FR-002
**Prioridade:** Must | **Estimativa:** 4h
**Dependências:** Nenhuma
**Checklist:**
- [ ] Declarar `NodeKind` como `#[non_exhaustive]` (reserva para adjustment layers, FR-012)
- [ ] Criar o workspace Cargo (`core/Cargo.toml`) e o crate `core-domain` (IDs `NodeId`, trait de erro `RabiscoError`) conforme `docs/architecture/crates.toml`
- [ ] Criar crate `scene-engine` em `core/scene-engine/`
- [ ] Implementar `SceneGraph` com arena (`Vec<NodeSlot>`) e `HashMap<NodeId, NodeIndex>`
- [ ] Implementar `NodeSlot`, `NodeData`, `NodeKind` enum (6 variantes)
- [ ] Implementar `FractionalIndex` com operações de ponto médio e comparação
- [ ] Implementar `BlendMode` enum (19 valores do conjunto R1, decisão D-003)
- [ ] Implementar `AffineTransform` (6 × f32)
**AC:** Structs compilam. Testes unitários para FractionalIndex (inserção, comparação, rebalanceamento).
**Arquivos:** `core/scene-engine/src/lib.rs`, `core/scene-engine/src/node.rs`, `core/scene-engine/src/tree.rs`, `core/scene-engine/src/fractional.rs`, `core/scene-engine/src/blend.rs`
**Verificação:** `cargo test -p scene-engine`

### T-002 — API de manipulação da árvore
**Requisito:** FR-001, FR-002, FR-010
**Prioridade:** Must | **Estimativa:** 4h
**Dependências:** T-001
**Checklist:**
- [ ] `add_node(parent, kind, position) -> Result<NodeId>`
- [ ] `remove_node(id) -> Result<RemovedSubtree>`
- [ ] `move_node(id, new_parent, position) -> Result<()>`
- [ ] `get_node(id) -> Option<&NodeData>`
- [ ] `get_children(id) -> impl Iterator<Item = NodeIndex>`
- [ ] `dfs_iter() -> impl Iterator<Item = (NodeIndex, Depth)>`
- [ ] `set_property(id, prop, value) -> Result<()>` para opacity, blend_mode, visible, locked, transform, name, clip_path
**AC:** Todas as operações testadas. DFS iter visita todos os nós em ordem de profundidade.
**Arquivos:** `core/scene-engine/src/tree.rs`, `core/scene-engine/src/ops.rs`
**Verificação:** `cargo test -p scene-engine -- --test tree_ops`

### T-003 — Validação de ciclos e isolamento de grupo
**Requisito:** FR-003, FR-008
**Prioridade:** Must | **Estimativa:** 2h
**Dependências:** T-002
**Checklist:**
- [ ] `is_ancestor(candidate, node) -> bool` percorre a árvore até a raiz
- [ ] `move_node` chama `is_ancestor` e retorna `Err(CycleDetected)` se verdadeiro
- [ ] Profundidade máxima = 64. `add_node` / `move_node` retorna `Err(MaxDepthExceeded)`
- [ ] Flag `isolation` derivada de blend_mode (interface pública para o compositor)
**AC:** Testes: mover para descendente falha, mover para não-descendente sucede, profundidade 65 falha.
**Arquivos:** `core/scene-engine/src/tree.rs`, `core/scene-engine/src/validation.rs`
**Verificação:** `cargo test -p scene-engine -- --test validation`

### T-004 — DocumentMeta e perfil de cor
**Requisito:** FR-004
**Prioridade:** Must | **Estimativa:** 2h
**Dependências:** T-001
**Checklist:**
- [ ] Struct `DocumentMeta` com width, height, dpi, color_profile (bytes ICC), bit_depth, blend_space
- [ ] Validação: width/height > 0 e ≤ 65536, dpi > 0, bit_depth ∈ {8, 16}, blend_space ∈ {perceptual, linear}
- [ ] Factory `Document::new(width, height, dpi, profile, bit_depth, blend_space) -> SceneGraph` cria árvore mínima (Document + Artboard + RasterLayer)
**AC:** Documento criado com todos os campos. Validação rejeita valores fora do range.
**Arquivos:** `core/scene-engine/src/document.rs`
**Verificação:** `cargo test -p scene-engine -- --test document`

### T-005 — Tiles e TileRef
**Requisito:** FR-005
**Prioridade:** Must | **Estimativa:** 3h
**Dependências:** T-001
**Checklist:**
- [ ] Em `core-domain` (módulo `tile`): `TileHash` (blake3, 32 bytes), `TileCoord`, `TileRef { col, row, hash }`, `TileData`
- [ ] Trait `TileStore`: `get(hash) -> Option<&TileData>`, `put(data) -> TileHash`, `contains(hash) -> bool`
- [ ] `InMemoryTileStore` para testes
- [ ] Em `scene-engine`: `RasterLayerData` = `HashMap<(u32, u32), TileHash>`
- [ ] Tile ausente = transparente (otimização documentada)
**AC:** Put + get round-trip. Hash de dois tiles com mesmo conteúdo é idêntico. Tile ausente retorna None (transparente).
**Arquivos:** `core/core-domain/src/tile.rs`, `core/scene-engine/src/raster.rs`
**Verificação:** `cargo test -p core-domain -p scene-engine -- tiles`

### T-006 — Tipos vetoriais e EmbeddedImage
**Requisito:** FR-006, FR-011
**Prioridade:** Must | **Estimativa:** 3h
**Dependências:** T-001
**Checklist:**
- [ ] Enum `Shape` { Path(BezierPath), Rect, Ellipse, Polygon }
- [ ] Struct `VectorObject` { id, shape, fill, stroke, transform }
- [ ] `Fill` enum { Solid(Color), LinearGradient(...), RadialGradient(...) }
- [ ] `Stroke` struct { color, width, cap, join, dash }
- [ ] `VectorLayerData` = `Vec<VectorObject>` com ordenação
- [ ] `EmbeddedImageData` { hash, width, height, format }
**AC:** Criar VectorLayer com 3 objetos, serializar/deserializar, comparar.
**Arquivos:** `core/scene-engine/src/vector.rs`, `core/scene-engine/src/embedded.rs`
**Verificação:** `cargo test -p scene-engine -- --test vector`

### T-007 — Masks
**Requisito:** FR-007
**Prioridade:** Must | **Estimativa:** 2h
**Dependências:** T-005, T-006
**Checklist:**
- [ ] Enum `MaskKind` { Raster, Vector }
- [ ] Struct `MaskData` { kind, tiles ou shape }
- [ ] Validação: mask em Document é rejeitada
- [ ] API: `set_mask(node_id, mask)`, `remove_mask(node_id)`
**AC:** Mask raster e vetorial criadas e removidas. Mask em Document retorna erro.
**Arquivos:** `core/scene-engine/src/mask.rs`
**Verificação:** `cargo test -p scene-engine -- --test mask`

### T-008 — JSON Schema e conformance suite
**Requisito:** FR-009, NFR-003
**Prioridade:** Must | **Estimativa:** 4h
**Dependências:** T-001 a T-007
**Checklist:**
- [ ] Escrever `contracts/document-format/scene.json` (JSON Schema draft 2020-12)
- [ ] Escrever `contracts/document-format/tile.json`
- [ ] Criar vetores de teste em `contracts/conformance/scene/`: documento mínimo, 30 camadas, grupo aninhado, mask raster, mask vetorial, embedded image
- [ ] Script de validação: deserializa cada vetor com código Rust, valida contra schema
- [ ] Integrar no CI: `cargo test --features conformance`
**AC:** Todos os vetores passam. Schema rejeita documento com campo faltante.
**Arquivos:** `contracts/document-format/scene.json`, `contracts/document-format/tile.json`, `contracts/conformance/scene/*.json`
**Verificação:** `cargo test --features conformance`

### T-009 — Registros de persistência (sem SQL)
**Requisito:** FR-001, NFR-002
**Prioridade:** Must | **Estimativa:** 3h
**Dependências:** T-001 a T-007
**Checklist:**
- [ ] Structs `NodeRecord`, `TileRefRecord`, `DocumentMetaRecord` em `scene_engine::records`
- [ ] `SceneGraph::to_records()` e `SceneGraph::from_records()` com validação de invariantes (ciclo, profundidade ≤ 64, pai existente, ordem fracionária válida)
- [ ] Round-trip: `from_records(to_records(g)) == g` para todos os vetores de `contracts/conformance/scene/`
- [ ] Nenhuma dependência de SQLite neste crate (o DDL e a escrita pertencem à SPEC-002)
**AC:** R-A simulado (30 camadas) converte para registros e volta sem diferença. `from_records` de R-A ≤ 500 ms.
**Arquivos:** `core/scene-engine/src/records.rs`
**Verificação:** `cargo test -p scene-engine -- records`

### T-010 — Benchmark de travessia e de reconstrução da árvore
**Requisito:** NFR-001, NFR-002
**Prioridade:** Must | **Estimativa:** 2h
**Dependências:** T-002, T-009
**Checklist:**
- [ ] Benchmark com criterion: travessia DFS de R-A (30 camadas, árvore simulada)
- [ ] Benchmark: `from_records` de R-A (sem decodificação de tiles)
- [ ] Assert: travessia ≤ 1 ms, `from_records` ≤ 500 ms
- [ ] O benchmark de abertura com SQLite pertence à SPEC-002 (T-002)
**AC:** Benchmarks executam e ficam dentro dos limites.
**Arquivos:** `core/scene-engine/benches/traversal.rs`, `core/scene-engine/benches/records.rs`
**Verificação:** `cargo bench -p scene-engine`

## Ordem de Execução

```
T-001 (structs)
  ├─ T-002 (API árvore)
  │    └─ T-003 (validação ciclos)
  ├─ T-004 (DocumentMeta)
  ├─ T-005 (tiles)
  │    └─ T-007 (masks) ← também depende de T-006
  ├─ T-006 (vetores + embedded)
  ├─ T-008 (schema + conformance) ← após T-001–T-007
  └─ T-009 (registros de persistência) ← após T-001–T-007
      └─ T-010 (benchmarks de travessia e reconstrução)
```

## Riscos de Implementação

| Risco | Mitigação |
|-------|-----------|
| Generational index adiciona complexidade | Usar crate `slotmap` já validada |
| blake3 não disponível em WASM | blake3 tem feature `no_std` e compilação WASM; verificar no spike (a) |
| Benchmark flaky no CI | Executar com margem 2× e flag `--baseline` |
