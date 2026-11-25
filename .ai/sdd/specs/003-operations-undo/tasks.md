# SPEC-003: Modelo de Operações e Undo/Redo — Tasks

**Status:** tasks:draft (rascunho antecipado; não vinculante até design:approved)
**Requisitos:** `requirements.md`
**Design:** `design.md`

---

## Verificação de Prontidão

- [x] requirements.md escrito
- [x] design.md escrito
- [x] Q-001 a Q-005 respondidas (Q-003 fechada por decisão D-004: fora do escopo desta spec)
- [ ] requirements:approved
- [ ] design:approved

## Cobertura FR → Tarefas

| FR | Tarefa(s) |
|----|-----------|
| FR-001 | T-001, T-009 |
| FR-002 | T-002 |
| FR-003 | T-002 |
| FR-004 | T-003 |
| FR-005 | T-003 |
| FR-006 | T-005 |
| FR-007 | T-001 |
| FR-009 | T-004 |
| FR-008 | T-005 (reabertura e recuperação validadas com SPEC-002 T-005) |
| FR-010 | T-006 |
| FR-011 | T-001 |

## Tarefas

### T-001 — Definir structs: Operation, HLC, Payload, Inverse e DTO OpRecord
**Requisito:** FR-001, FR-007, FR-011
**Prioridade:** Must | **Estimativa:** 4h
**Dependências:** SPEC-001 T-001, SPEC-001 T-005 (NodeData, TileHash)
**Checklist:**
- [ ] Criar crate `history-engine` em `core/history-engine/`
- [ ] Em `core-domain`: `OpRecord` (DTO plano, sem dependência de `history-engine`)
- [ ] Struct `Operation` com todos os campos do envelope e conversões `Operation <-> OpRecord`
- [ ] Struct `HybridLogicalClock` com `tick()` e `merge()`
- [ ] Enum `OpType` para os 12 tipos do R1
- [ ] Enum `Payload` com variantes tipadas
- [ ] Enum `InversePayload` espelhando Payload
- [ ] Struct `TileChange { col, row, hash }`
- [ ] Testes: HLC monotônico, construção de Operation válida, round-trip `Operation -> OpRecord -> Operation`
**AC:** Structs compilam. HLC tick é monotônico. Operation round-trip serde.
**Arquivos:** `core/core-domain/src/op_record.rs`, `core/history-engine/src/operation.rs`, `core/history-engine/src/hlc.rs`
**Verificação:** `cargo test -p history-engine -p core-domain -- structs`

### T-002 — Oplog: append, idempotência, validação HLC
**Requisito:** FR-002, FR-003, FR-011
**Prioridade:** Must | **Estimativa:** 3h
**Dependências:** T-001
**Checklist:**
- [ ] Struct `Oplog` com `Vec<Operation>`, `HashSet<OpId>`, `HashMap<DeviceId, HLC>`
- [ ] `append(op) -> Result<(), OpError>`: idempotência + HLC validation
- [ ] `get(op_id) -> Option<&Operation>`
- [ ] `iter() -> impl Iterator`
- [ ] `len() -> usize`
**AC:** Op duplicada ignorada. Op com HLC stale rejeitada. Append de 10.000 ops < 10 ms.
**Verificação:** `cargo test -p history-engine -- --test oplog`

### T-003 — UndoManager: undo, redo, on_new_op
**Requisito:** FR-004, FR-005
**Prioridade:** Must | **Estimativa:** 4h
**Dependências:** T-002
**Checklist:**
- [ ] Struct `UndoManager` com undo_stack e redo_stack (Vec<OpId>)
- [ ] `undo(oplog, hlc) -> Option<Operation>`: cria inverse op
- [ ] `redo(oplog, hlc) -> Option<Operation>`: reaplica original
- [ ] `on_new_op(op_id)`: push to undo, clear redo
- [ ] Filtro por author_id (preparado para multi-user)
**AC:** Sequência completa undo/redo/undo+nova ação conforme tabela dos exemplos concretos.
**Verificação:** `cargo test -p history-engine -- --test undo`

### T-004 — Operações compostas (compound)
**Requisito:** FR-009
**Prioridade:** Should | **Estimativa:** 2h
**Dependências:** T-003
**Checklist:**
- [ ] `Payload::Compound { sub_ops: Vec<Payload> }`
- [ ] `InversePayload::Compound { sub_inverses: Vec<InversePayload> }`
- [ ] Undo de compound aplica todos os sub-inverses atomicamente
- [ ] Teste: mover grupo com 5 filhos → undo restaura todos
**AC:** Compound op undo/redo é atômico.
**Verificação:** `cargo test -p history-engine -- --test compound`

### T-005 — Integração: `Document::apply_and_commit` (document-engine)
**Requisito:** FR-006, FR-008
**Prioridade:** Must | **Estimativa:** 4h
**Dependências:** T-002, T-003, T-009, SPEC-002 T-004, SPEC-001 T-009
**Checklist:**
- [ ] Criar crate `document-engine` em `core/document-engine/`
- [ ] `Document::apply_and_commit(op)`: `apply_operation` → monta `CommitBatch` → `DocHandle::commit` → só então `oplog.append` e `undo_stack.push`
- [ ] Se o commit falhar: reverter a aplicação em memória usando o inverse e devolver o erro (implementar antes do caminho feliz)
- [ ] Na abertura: reconstruir `SceneGraph` com `from_records` e o `Oplog` a partir de `oplog` (últimas N operações; restante sob demanda)
- [ ] Reabertura após falha: estado igual ao da última transação confirmada
**AC:** Operação persistida. Reabrir mostra a operação no oplog e o Undo continua funcionando (US-005).
**Arquivos:** `core/document-engine/src/session.rs`
**Verificação:** `cargo test -p document-engine -- --test integration`

### T-006 — JSON Schema e conformance suite
**Requisito:** FR-010
**Prioridade:** Must | **Estimativa:** 3h
**Dependências:** T-001
**Checklist:**
- [ ] `contracts/document-format/operation.json` (JSON Schema draft 2020-12)
- [ ] Vetores de teste em `contracts/conformance/operations/`:
  - Operação válida de cada op_type
  - Operação com op_id duplicado (idempotência)
  - Operação com HLC stale (rejeitada)
  - Compound operation
  - Undo/redo round-trip
- [ ] Validação no CI: deserializar cada vetor com código Rust
**AC:** Conformance suite passa 100%.
**Verificação:** `cargo test --features conformance`

### T-007 — Property-based tests de convergência
**Requisito:** NFR-002
**Prioridade:** Must | **Estimativa:** 4h
**Dependências:** T-003, T-009
**Checklist:**
- [ ] Usar `proptest` ou `quickcheck`
- [ ] Propriedade 1: apply(op) → undo(op) = estado original
- [ ] Propriedade 2: apply(op) → apply(op) = apply(op) (idempotência)
- [ ] Propriedade 3: apply(A) → apply(B) → undo(B) → undo(A) = estado original
- [ ] Para operações raster: comparar tile hashes (bit a bit)
- [ ] Para operações de nó: comparar SceneGraph serializado
**AC:** 10.000 iterações sem falha para cada propriedade.
**Verificação:** `cargo test -p history-engine -- --test proptest --ignored` (CI noturno)

### T-008 — Benchmark de commit e undo
**Requisito:** NFR-001, NFR-003
**Prioridade:** Must | **Estimativa:** 2h
**Dependências:** T-005
**Checklist:**
- [ ] Benchmark: commit de traço com 4 tiles → p95 ≤ 100 ms
- [ ] Benchmark: undo de traço raster → ≤ 50 ms (troca de refs)
- [ ] Benchmark: 1.000 ops no oplog em memória: busca por op_id ≤ 1 µs
**AC:** Benchmarks dentro dos limites.
**Verificação:** `cargo bench -p history-engine -p document-engine`

### T-009 — Aplicação de operações no SceneGraph (`apply_operation`)
**Requisito:** FR-001, FR-002, FR-009
**Prioridade:** Must | **Estimativa:** 4h
**Dependências:** T-001, T-002, SPEC-001 T-002, SPEC-001 T-007
**Checklist:**
- [ ] `apply_operation(scene, op) -> Result<AppliedEffects>` para os 12 `op_type` do R1
- [ ] `AppliedEffects { node_upserts, node_deletes, tile_ref_changes }`
- [ ] Idempotência: segunda aplicação do mesmo `op_id` devolve efeitos vazios
- [ ] Compound: aplica todos os sub-efeitos ou nenhum
- [ ] Erros tipados (`ApplyError`): `CycleDetected`, `NodeNotFound`, `LockedNode`
**AC:** Cada `op_type` aplicado e revertido pelo seu inverse devolve o `SceneGraph` ao estado original.
**Arquivos:** `core/history-engine/src/apply.rs`
**Verificação:** `cargo test -p history-engine -- --test apply`

## Ordem de Execução

```
T-001 (structs Operation/HLC/OpRecord)
  ├─ T-006 (schema + conformance)
  └─ T-002 (Oplog)
       ├─ T-003 (UndoManager)
       │    └─ T-004 (compound)
       └─ T-009 (apply_operation) ← SPEC-001 T-002, T-007
            ├─ T-007 (property-based tests) ← também T-003
            └─ T-005 (integração, document-engine) ← T-003, SPEC-002 T-004, SPEC-001 T-009
                 └─ T-008 (benchmarks)
```

## Riscos de Implementação

| Risco | Mitigação |
|-------|-----------|
| Property-based tests lentos | Executar apenas no CI noturno com 10.000 iterações; local com 100 |
| JSON Schema para Payload enum complexo | Usar `oneOf` com discriminador `op_type` |
| Rollback em memória se commit falha | Implementar antes do happy path |
