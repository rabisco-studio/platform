# SPEC-005: Pincéis e Pintura Raster — Tasks

**Status:** tasks:draft (rascunho antecipado; não vinculante até design:approved)
**Requisitos:** `requirements.md`
**Design:** `design.md`

---

## Verificação de Prontidão

- [x] requirements.md escrito
- [x] design.md escrito
- [x] Q-001 a Q-005 respondidas
- [ ] requirements:approved
- [ ] design:approved

## Cobertura FR → Tarefas

| FR | Tarefa(s) |
|----|-----------|
| FR-001 | T-001 |
| FR-002 | T-002 |
| FR-003 | T-003 |
| FR-004 | T-004, T-006 |
| FR-005 | T-005 |
| FR-006 | T-006 |
| FR-007 | T-004 (shader) |
| FR-008 | T-009 |
| FR-009 | T-007 |
| FR-010 | T-003 (blend mode Erase) |
| FR-011 | (removido; ver SPEC-007) |
| FR-012 | T-001 (texture ref) |
| FR-013 | T-006 (stroke record) |

## Tarefas

### T-001 — BrushDefinition e JSON Schema
**Requisito:** FR-001, FR-012
**Prioridade:** Must | **Estimativa:** 3h
**Dependências:** Nenhuma
**Checklist:**
- [ ] Criar crate `brush-engine` em `core/brush-engine/`
- [ ] Struct `BrushDefinition` com todos os campos
- [ ] Struct `TipDefinition`, `RangeParam`
- [ ] Desserializar de JSON (serde)
- [ ] Schema em `contracts/brush-definition/brush.json`
- [ ] Validação: spacing > 0, size.min ≤ size.max, etc.
**AC:** Definição do lápis carrega do JSON sem erro. Validação rejeita spacing ≤ 0.
**Verificação:** `cargo test -p brush-engine -- --test definition`

### T-002 — DynamicsEngine
**Requisito:** FR-002
**Prioridade:** Must | **Estimativa:** 3h
**Dependências:** T-001
**Checklist:**
- [ ] Struct `DynamicsEngine`
- [ ] `evaluate(sample: &InputSample, dynamics: &DynamicsMap) -> DabParams`
- [ ] Curvas: Linear, EaseIn, EaseOut, Custom (pontos de controle)
- [ ] Interpolação de curvas custom com clamp
- [ ] Testes: pressão 0 → min, pressão 1 → max, curva custom
**AC:** Dinâmicas calculadas corretamente para todas as curvas.
**Verificação:** `cargo test -p brush-engine -- --test dynamics`

### T-003 — StrokeEngine: amostras → dabs
**Requisito:** FR-003, FR-010
**Prioridade:** Must | **Estimativa:** 4h
**Dependências:** T-001, T-002
**Checklist:**
- [ ] Struct `StrokeEngine` com estado do traço ativo
- [ ] `begin_stroke(brush: &BrushDefinition, first_sample: InputSample)`
- [ ] `add_sample(sample: InputSample) -> Vec<Dab>`
- [ ] `end_stroke() -> StrokeResult`
- [ ] Interpolação Catmull-Rom entre amostras
- [ ] Geração de dabs por intervalo de espaçamento
- [ ] Borracha: blend mode = Erase (alpha → 0)
- [ ] Input smoothing (moving average, configurável) em `input-engine` (módulo `filter`), junto de `InputSample`
**AC:** Traço de 100 amostras gera ~400 dabs (spacing=0.25). Borracha produz dabs com blend Erase.
**Verificação:** `cargo test -p brush-engine -- --test stroke_engine`

### T-004 — GPU Stamping Shader (wgpu)
**Requisito:** FR-004, FR-007
**Prioridade:** Must | **Estimativa:** 4h
**Dependências:** T-003, SPEC-004 (GpuContext e scaffold do `render-engine`), Spike (a) concluído
**Checklist:**
- [ ] Módulo `overlay` em `core/render-engine/` (o crate e o `GpuContext` são entregues pela SPEC-004)
- [ ] `OverlayTexture`: alocação por bounding box, formato rgba16float
- [ ] Compute shader WGSL `stamp_dab.wgsl`: dab uniform, tip texture, overlay texture, alfa pré-multiplicado, blend modes do pincel
- [ ] Pipeline wgpu: bind groups, dispatch por lote de dabs
- [ ] Shader de composição: overlay + camada → exibição
- [ ] `OverlayTexture::resolve_onto(base_tiles) -> Vec<(col, row, TileData)>` com assert contra predição
**AC:** Dabs aparecem no overlay. Composição overlay + camada visualmente correta. `resolve_onto` falha se houver pixel de predição.
**Arquivos:** `core/render-engine/src/overlay.rs`, `core/render-engine/shaders/stamp_dab.wgsl`
**Verificação:** `cargo test -p render-engine -- --test stamp` (GPU headless via wgpu)

### T-005 — Predição de traço
**Requisito:** FR-005
**Prioridade:** Must | **Estimativa:** 2h
**Dependências:** T-003
**Checklist:**
- [ ] `PredictionEngine`: extrapola 1–3 pontos via regressão linear
- [ ] Dabs de predição renderizados no overlay com flag
- [ ] Ao chegar amostra real: descartar predição, substituir
- [ ] Assert no commit: `overlay.has_prediction() == false`
**AC:** Predição visível durante traço. Nenhuma predição no commit (assert).
**Verificação:** `cargo test -p brush-engine -- --test prediction`

### T-006 — Fim do traço: `StrokeResult` e `Document::commit_stroke`
**Requisito:** FR-004, FR-006, FR-013
**Prioridade:** Must | **Estimativa:** 4h
**Dependências:** T-004, SPEC-001 T-005, SPEC-003 T-005
**Checklist:**
- [ ] `brush-engine`: `StrokeResult { record: StrokeRecord, bounds, layer_id }` e `StrokeRecord` (amostras + hash do pincel + semente)
- [ ] `document-engine`: `Document::commit_stroke(result, overlay)`: lê tiles base, `resolve_onto`, calcula hashes, cria `Operation::raster_stroke` e chama `apply_and_commit`
- [ ] Limpar o overlay após o commit
- [ ] Medir latência; registrar aviso se > 100 ms
**AC:** Traço completo persistido. Undo restaura tiles anteriores.
**Arquivos:** `core/brush-engine/src/record.rs`, `core/document-engine/src/stroke.rs`
**Verificação:** `cargo test -p brush-engine -p document-engine -- commit_stroke`

### T-007 — Definições dos 5 pincéis do R1
**Requisito:** FR-009
**Prioridade:** Must | **Estimativa:** 2h
**Dependências:** T-001
**Checklist:**
- [ ] `assets/brushes/pencil.json` — traço fino, pressão → opacidade+size
- [ ] `assets/brushes/pen.json` — traço limpo, hardness alta
- [ ] `assets/brushes/airbrush.json` — spray difuso, opacidade acumulativa
- [ ] `assets/brushes/marker.json` — ponta larga, semi-transparente
- [ ] `assets/brushes/eraser.json` — blend mode Erase, pressão → size
- [ ] Validar cada JSON contra o schema
**AC:** 5 JSONs válidos carregados sem erro.
**Verificação:** `cargo test -p brush-engine -- --test builtin_brushes`

### T-008 — (Removida) SelectionTool
Movida para a **SPEC-007** (RF-03.7). O ID é mantido como registro e não é reutilizado.

### T-009 — Benchmark de latência e fps
**Requisito:** NFR-001, NFR-002, NFR-004
**Prioridade:** Must | **Estimativa:** 3h
**Dependências:** T-004, T-006
**Checklist:**
- [ ] Benchmark: latência input → overlay atualizado (timestamp diff)
- [ ] Benchmark: frame time durante traço em R-A (p95 ≤ 16,6 ms)
- [ ] Benchmark: commit de traço com 4 tiles (p95 ≤ 100 ms)
- [ ] Determinismo: mesmo input → mesmo tile hash (mesma GPU)
**AC:** Métricas dentro dos limites no desktop de referência.
**Verificação:** `cargo bench -p brush-engine -p render-engine -p document-engine -- latency fps commit`

### T-010 — Golden images dos pincéis
**Requisito:** NFR-003
**Prioridade:** Must | **Estimativa:** 3h
**Dependências:** T-004, T-007
**Checklist:**
- [ ] Gerar traço de referência (1.000 amostras, pressão crescente 0→1) com cada pincel
- [ ] Renderizar em canvas 1024×1024 com fundo branco
- [ ] Salvar como golden images em `tests/graphics/golden/brushes/`
- [ ] Script de comparação: diff por canal ≤ 4/255
- [ ] Integrar no CI: `cargo test --features golden`
**AC:** 5 golden images geradas. CI passa com tolerância configurada.
**Verificação:** `cargo test --features golden -- --test brush_golden`

## Ordem de Execução

```
T-001 (BrushDefinition)
  ├─ T-002 (Dynamics)
  │    └─ T-003 (StrokeEngine)
  │         ├─ T-004 (GPU Stamping) ← SPEC-004, Spike (a)
  │         │    ├─ T-006 (Fim do traço + commit) ← SPEC-001 T-005, SPEC-003 T-005
  │         │    │    └─ T-009 (benchmarks)
  │         │    └─ T-010 (golden images) ← também T-007
  │         └─ T-005 (Predição)
  └─ T-007 (5 pincéis JSON)
```

## Riscos de Implementação

| Risco | Mitigação |
|-------|-----------|
| Shader WGSL não disponível antes do spike (a) | T-004 bloqueado pelo spike; stub CPU para testes iniciais |
| Golden images instáveis no CI (GPU diferente) | Executar em GPU de referência no CI; tolerância configurável |
| Catmull-Rom produz overshooting | Limitar extrapolação; opção de linear no pincel |
