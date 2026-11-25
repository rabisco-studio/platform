# SPEC-005: Pincéis e Pintura Raster — Design

**Status:** design:draft (rascunho antecipado; não vinculante até requirements:approved)
**Requisitos:** `requirements.md`

---

## 1. Resumo Executivo

O pipeline de pintura é um caminho hot-path de baixa latência: amostras de entrada são filtradas, convertidas em dabs parametrizados, aplicados por compute shader WGSL em um overlay transitório, e compostos nos tiles da camada ao término do traço. A operação resultante é commitada via SPEC-003/SPEC-002.

## 2. Mapeamento de Requisitos

| FR | Decisão de Design | Componente |
|----|-------------------|------------|
| FR-001 | `BrushDefinition` struct + JSON schema | `brush_engine` |
| FR-002 | `DynamicsEngine` avalia curvas por amostra | `brush_engine::dynamics` |
| FR-003 | `StrokeEngine` recebe amostras, gera dabs | `brush_engine::stroke` |
| FR-004 | `OverlayTexture` + compute shader | `render_engine::overlay` |
| FR-005 | Predição em overlay; assert no commit | `brush_engine::prediction` |
| FR-006 | `StrokeResult` (brush-engine) + `Document::commit_stroke` (document-engine) orquestram overlay → tiles → operação | `document_engine::stroke` |
| FR-007 | Shader respeita blend_space do DocumentMeta | `render_engine::color` |
| FR-008 | Pipeline otimizada; medição de latência | Profiling |
| FR-009 | 5 definições JSON em `assets/brushes/` | Dados |
| FR-010 | Borracha = blend mode "Erase" (alpha → 0) | `brush_engine` |
| FR-011 | Removido: movido para a SPEC-007 | — |
| FR-012 | `paper_texture` em BrushDefinition | `brush_engine` |
| FR-013 | `StrokeRecord` com amostras + brush_hash + seed | `brush_engine::record` |

## 3. Arquitetura

### 3.1 Pipeline de Componentes

```
InputSource (platform-specific)
  → InputFilter (smoothing)
    → StrokeEngine (gera dabs)
      → GPU StampingShader (overlay)
        → CompositorShader (overlay + layer → display)
          → ao terminar: StrokeResult → document-engine (Document::commit_stroke) → Operation → persist
```

### 3.2 Structs Principais

```rust
struct BrushDefinition {
    schema_version: SemVer,
    name: String,
    id: BrushId,
    tip: TipDefinition,
    spacing: f32,         // 0.0–1.0, fração do diâmetro
    size: RangeParam,
    opacity: RangeParam,
    flow: RangeParam,
    rotation: RangeParam,
    scatter: RangeParam,
    blend_mode: BlendMode,
    smoothing: f32,       // 0.0–1.0
    paper_texture: Option<TextureRef>,
    dynamics: DynamicsMap,
}

struct TipDefinition {
    shape: TipShape,       // Round, Square, Custom(texture)
    hardness: f32,         // 0.0 (soft) – 1.0 (hard)
    texture: Option<TextureRef>,
}

struct DynamicsMap {
    pressure: HashMap<DynamicTarget, DynamicCurve>,
    tilt: HashMap<DynamicTarget, DynamicCurve>,
    azimuth: HashMap<DynamicTarget, DynamicCurve>,
    velocity: HashMap<DynamicTarget, DynamicCurve>,
}

enum DynamicTarget { Size, Opacity, Flow, Rotation, Scatter }

struct DynamicCurve {
    curve_type: CurveType,  // Linear, EaseIn, EaseOut, Custom(points)
    min: f32,
    max: f32,
}
```

### 3.3 Input Sample

```rust
struct InputSample {
    position: Vec2,         // canvas coordinates
    timestamp_us: u64,      // microseconds since epoch
    pressure: f32,          // 0.0–1.0
    tilt: f32,              // 0–90 degrees
    azimuth: f32,           // 0–360 degrees
    is_eraser_tip: bool,    // hardware eraser detection
}
```

### 3.4 Dab Generation

```rust
struct Dab {
    position: Vec2,
    size: f32,
    opacity: f32,
    flow: f32,
    rotation: f32,
    color: [f32; 4],  // RGBA pre-multiplied, in document color space
}
```

Para cada intervalo de `spacing * current_size` ao longo do traço interpolado:
1. Interpolar posição (Catmull-Rom ou linear).
2. Interpolar pressão/tilt/azimuth.
3. Avaliar dinâmicas → size, opacity, flow, rotation.
4. Criar `Dab`.

Dabs acumulados em buffer (CPU), enviados em lote à GPU.

### 3.5 GPU Stamping (Compute Shader)

```wgsl
// Pseudocódigo do compute shader
@compute @workgroup_size(16, 16)
fn stamp_dab(
    @builtin(global_invocation_id) gid: vec3<u32>,
    dab: DabUniform,
    overlay: texture_storage_2d<rgba16float, read_write>,
    tip_texture: texture_2d<f32>,
) {
    let pixel_pos = vec2<f32>(gid.xy) + overlay_offset;
    let local_pos = inverse_transform(pixel_pos, dab.position, dab.rotation, dab.size);
    let tip_alpha = textureSample(tip_texture, local_pos).r * dab.opacity * dab.flow;
    let src_color = vec4<f32>(dab.color.rgb * tip_alpha, tip_alpha);  // pre-multiplied
    let dst_color = textureLoad(overlay, gid.xy);
    let result = blend(src_color, dst_color, dab.blend_mode);
    textureStore(overlay, gid.xy, result);
}
```

Overlay texture:
- Formato: `rgba16float` (para precisão no blending intermediário).
- Tamanho: bounding box do traço + margem (não canvas inteiro).
- Alocado no início do traço, liberado após commit.

### 3.6 Fim do traço e commit

Responsabilidades por crate (dependências: `brush-engine` não conhece `history-engine`, `file-engine` nem GPU):

| Crate | Papel no fim do traço |
|-------|----------------------|
| `brush-engine` | Devolve `StrokeResult { record: StrokeRecord, bounds, layer_id }`. Não persiste nada. |
| `render-engine` | `OverlayTexture::resolve_onto(base_tiles) -> Vec<(col, row, TileData)>`: compõe o overlay sobre os tiles base na GPU e devolve os pixels resultantes; falha se houver pixel de predição (assert de P-09). |
| `document-engine` | `Document::commit_stroke(result)`: lê os tiles base, chama `resolve_onto`, calcula hashes, cria a Operation `raster.stroke` e chama `apply_and_commit` (SPEC-003 T-005). |

```rust
// document-engine
impl Document {
    fn commit_stroke(&mut self, result: StrokeResult, overlay: &mut OverlayTexture) -> Result<()> {
        let base = self.tiles_covering(result.layer_id, &result.bounds);          // (col,row) -> Option<TileHash>
        let new_tiles = overlay.resolve_onto(&base, &self.tile_store)?;           // GPU; falha se houver predição
        let changes: Vec<TileChange> = new_tiles.iter().map(|t| TileChange {
            col: t.col, row: t.row, old: base.hash_at(t.col, t.row), new: self.tile_store.put(t.data.clone()),
        }).collect();
        let op = Operation::raster_stroke(result.layer_id, &changes, &result.record);
        self.apply_and_commit(op)?;                                               // SPEC-003 T-005
        overlay.clear();
        Ok(())
    }
}
```

### 3.7 Predição

- 1–3 pontos extrapolados via regressão linear dos últimos N amostras.
- Renderizados no overlay com flag `is_prediction = true`.
- Ao chegar a amostra real, predição é descartada e substituída.
- **Assert no commit:** nenhum pixel de predição presente.

### 3.8 Input Smoothing

Moving average com janela configurável (padrão: 3 amostras).
- Reduz jitter de digitalizadores de baixa qualidade.
- Adiciona ~2–5 ms de latência.
- Desligável por pincel (`smoothing: 0.0`).

## 4. Modelo de Dados

### Brush Definition Schema

```
contracts/brush-definition/brush.json — JSON Schema
assets/brushes/pencil.json
assets/brushes/pen.json
assets/brushes/airbrush.json
assets/brushes/marker.json
assets/brushes/eraser.json
```

### Stroke Record (no oplog)

```json
{
  "brush_id": "builtin:pencil",
  "brush_hash": "abc123...",
  "seed": 42,
  "samples": [
    {"x": 100.5, "y": 200.3, "p": 0.7, "tilt": 45, "az": 120, "t": 1000}
  ]
}
```

Armazenado no `payload.extra` da operação. Informativo (P-04: tiles são autoridade).

## 5. Contratos Afetados

| Contrato | Mudança |
|----------|---------|
| `contracts/brush-definition/brush.json` | **Novo.** Schema da definição de pincel. |
| `contracts/conformance/brushes/` | **Novo.** Vetores de teste para determinismo. |

## 6. Crates Impactados

| Crate | Responsabilidade |
|-------|-----------------|
| `input-engine` (módulo `filter`) | `InputSample`, suavização de entrada (moving average). |
| `brush-engine` (novo) | Definição, dinâmicas, geração de dabs, predição, suavização, `StrokeResult`. Depende de `core-domain`, `color-engine`, `input-engine`, `raster-engine`. |
| `render-engine` (módulo `overlay`; scaffold e `GpuContext` na SPEC-004) | Overlay, compute shader de stamping, `resolve_onto`, composição de exibição. |
| `document-engine` (módulo `stroke`) | `Document::commit_stroke`. |
| `scene` | Referências de tiles atualizadas no commit. |
| `history` | Recebe operação de traço. |

## 7. Compatibilidade

- BrushDefinition versionada. Novas propriedades em minor bumps com defaults.
- Pincéis do R1 são embutidos (não removíveis). Pincéis do usuário no R5.

## 8. Segurança e Privacidade

- Amostras de entrada (posição, pressão) são dados do documento, não PII.
- Nenhuma telemetria de amostras sem opt-in.

## 9. Casos de Borda

| Caso | Comportamento |
|------|---------------|
| Traço de 1 ponto (tap) | Gera 1 dab. Overlay composto nos tiles. |
| Traço cruzando borda do canvas | Dabs fora do canvas são clipados. Tiles afetados = interseção. |
| Pressão = 0 durante todo traço | Se opacity e size são mapeados por pressão: nada visível. No-op se todos os dabs resultam em alpha=0. |
| GPU sem compute shaders | Fallback CPU (lento, mas funcional). Warning ao usuário. |
| Overlay maior que VRAM disponível | Dividir overlay em chunks e processar sequencialmente. |
| Dois traços simultâneos (multitouch) | Apenas um traço ativo por camada no R1. Segundo ignorado. |

## 10. Estratégia de Verificação

| Tipo | O que verifica | Como |
|------|---------------|------|
| [VIS] | Golden images dos 5 pincéis | Traço de referência (1.000 amostras) → comparar por canal ≤ 4/255 |
| [PERF] | Latência ≤ 30 ms, 60 fps | Benchmark com timestamps do sistema |
| [BEH] | Determinismo, commit, undo, predição não persistida | Testes unitários + integração |
| [CONF] | Schema brush.json | CI: validação |

## 11. Decisões Técnicas

### TD-001 — Overlay por bounding box vs. canvas inteiro
**Decisão:** Bounding box. R-A inteiro em rgba16float = 4096×4096×8 = 128 MiB por overlay. Bounding box típico = < 10 MiB.

### TD-002 — rgba16float vs. rgba8unorm para overlay
**Decisão:** rgba16float. Precisão no blending intermediário (evita banding em gradientes suaves e baixas opacidades). Tiles finais podem ser 8 bits; a conversão é no commit.

### TD-003 — Catmull-Rom vs. Linear para interpolação de traço
**Decisão:** Catmull-Rom (curvas mais suaves). Linear como fallback com < 4 amostras.

## 12. Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Latência > 30 ms | Média | Alto | Profiling no spike (a); reduzir smoothing; otimizar shader dispatch |
| Determinismo impossível entre GPUs | Alta | Médio | Tolerância ≤ 4/255; determinismo exato por modelo de GPU |
| Compute shaders não disponíveis em WebGL2 | Alta | Alto | Fallback para fragment shader; medir performance |
| Overlay chunks complexos | Baixa | Médio | Implementar apenas se OOM detectado em testing |
