# SPEC-003: Modelo de Operações e Undo/Redo — Design

**Status:** design:draft (rascunho antecipado; não vinculante até requirements:approved)
**Requisitos:** `requirements.md`

---

## 1. Resumo Executivo

Toda alteração no documento é representada como uma operação imutável com inverse embutido. O `history-engine` gerencia o oplog em memória e coordena com o `file-engine` para persistência. Undo cria uma nova operação inversa; Redo reaplica a original.

## 2. Mapeamento de Requisitos

| FR | Decisão de Design | Componente |
|----|-------------------|------------|
| FR-001 | Struct `Operation` com todos os campos do envelope | `history_engine` |
| FR-002 | Oplog como `Vec<Operation>` append-only | `history_engine::oplog` |
| FR-003 | `HashMap<OpId, ()>` para lookup O(1) de duplicatas | `history_engine::oplog` |
| FR-004 | `UndoManager::undo()` cria Operation a partir de `inverse` | `history_engine::undo` |
| FR-005 | `UndoManager` com undo_stack e redo_stack | `history_engine::undo` |
| FR-006 | `Document::apply_and_commit` monta `CommitBatch` e chama `DocHandle::commit()` (SPEC-002) | `document-engine::session` |
| FR-007 | Inverse como enum `InversePayload` | `history_engine::operation` |
| FR-008 | Recuperação na reabertura: estado = última transação confirmada (SPEC-002 FR-005); o oplog só recebe a operação após o commit | `document-engine::session` |
| FR-009 | Operações compostas como `op_type: "compound"` | `history_engine::operation` |
| FR-010 | Schema em `contracts/document-format/operation.json` (esta spec é a dona) | Build + CI |
| FR-011 | HLC struct com validação monotônica (duplicata checada antes) | `history_engine::hlc` |

## 3. Arquitetura

### 3.1 Operation Struct

```rust
struct Operation {
    op_id: OpId,                // UUID v7
    author_id: AuthorId,       // UUID do usuário (local no R1)
    device_id: DeviceId,       // UUID do dispositivo
    hlc: HybridLogicalClock,   // 12 bytes: 8 timestamp_ms + 4 counter
    base_seq: u64,             // sequência local monotônica
    schema_version: SemVer,
    op_type: OpType,
    targets: Vec<NodeId>,
    payload: Payload,          // enum tipado por op_type
    inverse: InversePayload,   // enum tipado por op_type
}
```

### 3.2 HybridLogicalClock

```rust
struct HybridLogicalClock {
    timestamp_ms: u64,  // max(local_time, last_hlc.timestamp_ms)
    counter: u32,       // incrementa se timestamp_ms não avançou
}

impl HybridLogicalClock {
    fn tick(&mut self) -> Self { ... }
    fn merge(&mut self, remote: &Self) -> Self { ... }
}
```

Regra: `tick()` garante que `(timestamp_ms, counter)` é estritamente crescente por device_id. `merge()` será usado na Fase 5 para sync.

### 3.3 Oplog

```rust
struct Oplog {
    ops: Vec<Operation>,
    seen: HashSet<OpId>,        // para idempotência O(1)
    last_hlc: HashMap<DeviceId, HybridLogicalClock>,
}

impl Oplog {
    fn append(&mut self, op: Operation) -> Result<(), OpError> {
        if self.seen.contains(&op.op_id) { return Ok(()); }  // idempotente
        if let Some(last) = self.last_hlc.get(&op.device_id) {
            if op.hlc <= *last { return Err(OpError::StaleHLC); }
        }
        self.seen.insert(op.op_id);
        self.last_hlc.insert(op.device_id, op.hlc);
        self.ops.push(op);
        Ok(())
    }
}
```

### 3.4 UndoManager

```rust
struct UndoManager {
    undo_stack: Vec<OpId>,   // aponta para ops no Oplog
    redo_stack: Vec<OpId>,
    author_id: AuthorId,     // filtra por autor (futuro: multi-user)
}

impl UndoManager {
    fn undo(&mut self, oplog: &Oplog, hlc: &mut HybridLogicalClock) -> Option<Operation> {
        let op_id = self.undo_stack.pop()?;
        let original = oplog.get(op_id);
        let inverse_op = Operation::from_inverse(original, hlc.tick());
        self.redo_stack.push(op_id);
        Some(inverse_op)
    }

    fn redo(&mut self, oplog: &Oplog, hlc: &mut HybridLogicalClock) -> Option<Operation> {
        let op_id = self.redo_stack.pop()?;
        let original = oplog.get(op_id);
        let redo_op = Operation::from_redo(original, hlc.tick());
        self.undo_stack.push(op_id);
        Some(redo_op)
    }

    fn on_new_op(&mut self, op_id: OpId) {
        self.undo_stack.push(op_id);
        self.redo_stack.clear();  // nova ação descarta redo
    }
}
```

### 3.5 Payload/Inverse Enums

```rust
enum Payload {
    NodeAdd { data: NodeData, parent_id: NodeId, position: FractionalIndex },
    NodeRemove { node_id: NodeId },
    NodeMove { node_id: NodeId, new_parent: NodeId, new_position: FractionalIndex },
    NodeSetProperty { node_id: NodeId, prop: Property, value: PropertyValue },
    RasterStroke { layer_id: NodeId, tiles: Vec<TileChange> },
    RasterFill { layer_id: NodeId, tiles: Vec<TileChange> },
    VectorAddObject { layer_id: NodeId, object: VectorObject },
    VectorRemoveObject { layer_id: NodeId, object_id: ObjectId },
    VectorModifyObject { layer_id: NodeId, object_id: ObjectId, changes: VectorChanges },
    MaskSet { node_id: NodeId, mask: MaskData },
    MaskRemove { node_id: NodeId },
    DocumentSetMeta { changes: MetaChanges },
    Compound { sub_ops: Vec<Payload> },
}

struct TileChange {
    col: u32,
    row: u32,
    new_hash: TileHash,
}

// InversePayload espelha Payload com os valores anteriores
```

### 3.6 Fluxo Completo: Traço Raster

Quem orquestra é o `document-engine` (`Document::apply_and_commit`). Cada crate faz só o seu papel.

```
1. Usuário termina traço
2. brush-engine produz o resultado do traço (tiles novos) — sem tocar em disco nem no log
3. document-engine, para cada tile alterado:
   a. old_hash = scene.tile_ref(layer, col, row)
   b. new_hash = hash(new_tile_data)
4. document-engine cria a Operation (history-engine):
   - op_type: raster.stroke
   - payload: [(col, row, new_hash), ...]   inverse: [(col, row, old_hash), ...]
5. history_engine::apply_operation(&mut scene, &op) -> AppliedEffects
   (atualiza tile_refs na memória e devolve o que mudou)
6. document-engine monta CommitBatch { ops: [OpRecord], tile_ref_changes, new_tiles, node_upserts }
7. file_engine.commit(batch)   ← COMMIT SQLite
8. Só após o COMMIT: oplog.append(op) em memória, undo_stack.push, UI informa "salvo"
   (se o COMMIT falhar: desfazer o passo 5 com o inverse e informar o erro)
9. Render atualizado
```

**Undo deste traço:**
1. `UndoManager` pega o inverse (hashes antigos)
2. Cria nova Operation `raster.stroke` com os hashes antigos como payload
3. Mesmo caminho dos passos 5 a 8 (tiles antigos já estão no store; nada é decodificado)
4. Render atualizado — custo ≤ 50 ms (troca de referências)

## 4. Persistência e Aplicação de Operações

**DDL:** a tabela `oplog` e seus índices pertencem à SPEC-002 (`contracts/document-format/hybrid-schema-v1.sql`). Esta spec não define DDL.

**DTO de persistência (`core-domain::op_record`)**, que evita dependência de `file-engine` em `history-engine`:

```rust
struct OpRecord {
    op_id: OpId, author_id: AuthorId, device_id: DeviceId,
    hlc_ts: u64, hlc_counter: u32,
    base_seq: u64, schema_version: SemVer,
    op_type: String,
    targets: Vec<NodeId>,
    payload: Vec<u8>,   // JSON (zstd na gravação)
    inverse: Vec<u8>,   // JSON (zstd na gravação)
}
```

`history-engine` converte `Operation <-> OpRecord`. O mapeamento para as colunas do `oplog` é feito pelo `file-engine`.

**Aplicação (`history_engine::apply`)**:

```rust
fn apply_operation(scene: &mut SceneGraph, op: &Operation) -> Result<AppliedEffects, ApplyError>;

struct AppliedEffects {
    node_upserts: Vec<NodeRecord>,
    node_deletes: Vec<NodeId>,
    tile_ref_changes: Vec<TileRefChange>,
}
```

Idempotente: aplicar o mesmo `op_id` duas vezes devolve `AppliedEffects` vazio na segunda.

## 5. Contratos Afetados

| Contrato | Mudança |
|----------|---------|
| `contracts/document-format/operation.json` | **Novo.** JSON Schema do envelope completo. |
| `contracts/conformance/operations/` | **Novo.** Vetores: idempotência, undo/redo round-trip, compound op. |

## 6. Crates Impactados

| Crate | Responsabilidade |
|-------|-----------------|
| `history-engine` (novo) | Operation, Oplog, UndoManager, HLC, `apply_operation`. Depende de `core-domain` e `scene-engine`. |
| `core-domain` | `OpRecord` (DTO de persistência). |
| `document-engine` (novo) | `Document`: orquestra apply → CommitBatch → commit → oplog/undo. |
| `file-engine` | Não impactado (SPEC-002 persiste `OpRecord`). |

## 7. Compatibilidade

- Novas op_types adicionadas em minor bumps do schema_version.
- Op_types desconhecidos: logados e ignorados (forward compatibility).

## 8. Casos de Borda

| Caso | Comportamento |
|------|---------------|
| Undo sem operações no stack | No-op. Retorna None. |
| Redo após nova ação | Redo stack vazio. Retorna None. |
| Operação composta com 50 nós | Undo atômico: todos ou nenhum. |
| Inverse de NodeRemove (subárvore de 100 nós) | Inverse carrega snapshot completo da subárvore. |
| Op com schema_version > atual | Logada, ignorada, warning ao usuário. |
| Kill -9 entre append no Oplog em memória e commit no SQLite | Operação perdida (não havia sido confirmada). Aceito por design. |

## 9. Estratégia de Verificação

| Tipo | O que verifica | Como |
|------|---------------|------|
| [BEH] | Idempotência, undo/redo round-trip, compound | Testes unitários + property-based testing |
| [PERF] | Commit ≤ 100 ms, undo raster ≤ 50 ms | Benchmark com criterion |
| [CONF] | Schema operation.json | Conformance suite no CI |

## 10. Decisões Técnicas

### TD-001 — Inverse embutido vs. calculado
**Alternativas:** (A) Inverse embutido na operação, (B) Calcular inverse percorrendo o log.
**Decisão:** (A). O(1) para Undo, sem replay. Custo: espaço extra no log.

### TD-002 — Undo stack como referências vs. cópias
**Decisão:** Referências (OpId). As operações vivem no Oplog. Undo/Redo stack são listas de OpId.

### TD-003 — Compound operations
**Alternativas:** (A) Op_type "compound" com sub-ops, (B) Marcadores begin/end no log.
**Decisão:** (A). Mais simples, atômico por construção.

## 11. Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| Inverse de operações complexas é grande | Média | Médio | Tiles são referências, não cópias. Propriedades são pequenas. |
| Oplog em memória cresce | Alta | Médio | Lazy loading: carregar apenas últimas N ops ao abrir; restantes sob demanda. |
| Property-based tests encontram bug de convergência | Média | Alto | Corrigir antes de approval. Testes rodam no CI a cada PR. |
