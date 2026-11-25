# SPEC-002: Ciclo de Vida do Documento — Design

**Status:** design:draft (rascunho antecipado; não vinculante até requirements:approved)
**Requisitos:** `requirements.md`

---

## 1. Resumo Executivo

O `file-engine` gerencia o ciclo de vida do arquivo `.rbsc` (SQLite WAL). Cada operação do usuário resulta em uma transação atômica que persiste operação + tiles alterados. A abertura é progressiva: metadata e árvore primeiro, tiles do viewport sob demanda.

## 2. Mapeamento de Requisitos

| FR | Decisão de Design | Componente |
|----|-------------------|------------|
| FR-001 | `FileEngine::create(path, meta) -> Result<DocHandle>`; DDL em `rbsc-schema-v1.sql` | `file-engine` |
| FR-002 | `FileEngine::open(path) -> Result<(DocHandle, SceneRecords)>` com checks | `file-engine` |
| FR-003 | WAL replay automático pelo SQLite + fallback de integrity check | `file-engine::recovery` |
| FR-004 | `DocHandle::commit(batch: CommitBatch) -> Result<()>` em uma transação | `file-engine::commit` |
| FR-005 | WAL mode garante atomicidade; nenhum código adicional | SQLite engine |
| FR-006 | Abertura em 2 fases: tree + viewport tiles | `file-engine::loader` |
| FR-007 | Transação single-statement para operações simples | `file-engine::commit` |
| FR-008 | `CommitQueue` + `DocHandle::flush_pending()` chamado no lifecycle hook | `file-engine::queue` + bridge |
| FR-009 | Cópia via `VACUUM INTO` periódica | `file-engine::backup` |
| FR-010 | `VACUUM INTO` para novo path + reopen | `file-engine::save_as` |
| FR-011 | `BundleExporter::export(doc, path)` | `file-engine::bundle` |
| FR-012 | `BundleImporter::import(zip_path, target_dir)` | `file-engine::bundle` |
| FR-013 | `MigrationRegistry` com funções `vN -> vN+1`, backup pré-migração | `file-engine::migrate` |

## 3. Arquitetura

### 3.1 DocHandle e CommitBatch

O `file-engine` é a **camada de armazenamento**: conhece SQLite, tiles e registros; não conhece operações de desenho nem aplica mutações no `SceneGraph`. Quem orquestra edição e persistência é o `document-engine` (SPEC-003, T-005).

```rust
struct DocHandle {
    db: Connection,                         // rusqlite, WAL mode
    meta: DocumentMetaRecord,
    tile_cache: BoundedTileCache,           // limite por plataforma; política simples (LRU)
    queue: CommitQueue,                     // fila de lotes pendentes (FR-008)
}

// Lote atômico: tudo ou nada em uma transação SQLite.
struct CommitBatch {
    ops: Vec<OpRecord>,                     // DTO de core-domain (definido na SPEC-003)
    node_upserts: Vec<NodeRecord>,          // SPEC-001
    node_deletes: Vec<NodeId>,
    tile_ref_changes: Vec<TileRefChange>,   // (layer_id, mip, col, row, Option<TileHash>)
    new_tiles: Vec<(TileHash, TileData)>,
}
```

`file-engine` depende apenas de `core-domain` e `scene-engine` (registros). Não depende de `history-engine`: o que cruza a fronteira é o DTO `OpRecord`.

### 3.2 Fluxo de Abertura

```
open(path)
  ├─ 1. PRAGMA journal_mode=WAL (já deve ser)
  ├─ 2. PRAGMA integrity_check
  │     └─ falha → WAL replay → retry → falha → Err(Corrupted)
  ├─ 3. SELECT schema_version → validar compatibilidade
  ├─ 3b. Se schema_version < atual → backup + migrações (FR-013)
  ├─ 4. Carregar document_meta → DocumentMetaRecord
  ├─ 5. Carregar nodes → NodeRecord[] (o document-engine monta o SceneGraph com from_records)
  ├─ 6. Calcular viewport → listar tile_refs visíveis
  ├─ 7. Carregar tiles visíveis → tile_cache
  └─ 8. Retornar (DocHandle, SceneRecords) pronto para o document-engine
         (tiles restantes carregam em background thread)
```

### 3.3 Fluxo de Commit

```
commit(batch: CommitBatch)
  ├─ BEGIN IMMEDIATE
  ├─ INSERT INTO oplog        (cada OpRecord)
  ├─ UPSERT INTO tiles        (cada tile novo, comprimido zstd)
  ├─ UPSERT/DELETE tile_refs  (tile_ref_changes)
  ├─ UPSERT/DELETE nodes      (node_upserts, node_deletes)
  ├─ UPDATE file_meta         (last_modified)
  └─ COMMIT  → só então o chamador recebe a confirmação de "salvo"
```

Latência-alvo: p95 ≤ 100 ms. Fatores: número de tiles alterados (típico: 1–4 por traço) × tamanho comprimido. A atualização do `SceneGraph` em memória é responsabilidade do `document-engine`, depois do COMMIT bem-sucedido.

**Fila de commits (FR-008):** `CommitQueue::enqueue(batch)` não bloqueia a thread de UI; uma thread de escrita drena a fila e notifica o chamador após cada COMMIT. `flush_pending()` bloqueia até a fila esvaziar e o WAL ser sincronizado.

### 3.4 Abertura Progressiva

- **Fase 1 (blocking):** metadata + tree (< 50 ms para R-A).
- **Fase 2 (blocking):** tiles do viewport atual (tamanho depende do zoom; ≤ 50 tiles típico).
- **Fase 3 (background):** tiles restantes em thread pool, prioridade por distância ao viewport.
- **Evição:** LRU cache de tiles com budget por plataforma (desktop: 512 MB, tablet: 256 MB, web: 128 MB). Sob pressão, tiles são evictos e relidos do disco.

### 3.5 Bundle (ZIP)

**Exportação:**
1. `VACUUM INTO` para criar snapshot sem WAL.
2. Gerar manifesto JSON: `{ schema_version, created_at, tile_count, checksum: { algorithm: "blake3", value } }` (contrato `bundle-manifest.json`).
3. ZIP deflate: `manifest.json`, `document.db` (o SQLite), tiles soltos opcionais (para inspeção).

**Importação:**
1. Extrair ZIP para diretório temporário.
2. Validar manifesto + integrity_check do SQLite.
3. Mover SQLite para diretório do usuário.
4. Abrir normalmente.

### 3.6 Mobile Background

No Flutter, hook `AppLifecycleState.paused`:
1. Chamar `DocHandle::flush_pending()` via FFI.
2. `flush_pending` faz commit de todas as operações pendentes.
3. Se commit leva > 500 ms, logar aviso (operações demais sem commit intermediário).

## 4. Modelo de Dados

O DDL completo e comentado está em **`contracts/document-format/rbsc-schema-v1.sql`** (fonte única; esta spec é a única dona de DDL). Resumo:

| Tabela | Conteúdo | Origem dos dados |
|--------|----------|------------------|
| `file_meta` | schema_version, doc_id, timestamps, versão do app | file-engine |
| `document_meta` | dimensões, DPI, perfil ICC, profundidade, espaço de mesclagem | `DocumentMetaRecord` (SPEC-001) |
| `nodes` | estado materializado da árvore | `NodeRecord` (SPEC-001) |
| `tiles` | pixels comprimidos, endereçados por hash, imutáveis | `TileData` (core-domain) |
| `tile_refs` | (camada, mip, col, row) → hash do tile | `TileRefRecord` (SPEC-001) |
| `assets` | imagens embutidas (EmbeddedImage) | SPEC-001 FR-011 |
| `oplog` | log de operações append-only | `OpRecord` (SPEC-003) |

**Relação com a ADR-007:** `nodes` e `tile_refs` são o estado materializado, atualizado na mesma transação do `oplog`. Snapshots versionados e miniaturas ficam para a ADR-011 (R2).

## 5. Contratos Afetados

| Contrato | Mudança |
|----------|---------|
| `contracts/document-format/rbsc-schema-v1.sql` | **Novo.** DDL do formato (fonte única). |
| `contracts/document-format/bundle-manifest.json` | **Novo.** Schema do manifesto ZIP. |
| `contracts/document-format/operation.json` | Sem mudança (SPEC-003 é a dona; esta spec apenas persiste). |
| `contracts/document-format/scene.json` | Sem mudança (SPEC-001). |

## 6. Crates Impactados

| Crate | Responsabilidade |
|-------|-----------------|
| `file-engine` | Criação, abertura, commit, fila, backup, bundle, migração. Depende só de `core-domain` e `scene-engine`. |
| `core-domain` | Consome `OpRecord` (SPEC-003), `TileHash`/`TileData` (SPEC-001). |
| `scene-engine` | Apenas registros (`NodeRecord` etc.). Sem mudança. |

## 7. Compatibilidade e Migração

- schema_version "1.0.0" → primeira versão. Sem migração.
- Regra: adicionar coluna = minor bump com DEFAULT. Remover coluna = major bump com migração.

## 8. Segurança e Privacidade

- Arquivo SQLite no filesystem do usuário com permissões do OS.
- Bundle ZIP não inclui metadados de máquina (hostname, path absoluto).
- Tiles não contêm EXIF.

## 9. Casos de Borda

| Caso | Comportamento |
|------|---------------|
| Kill -9 durante commit | WAL garante rollback da transação incompleta. Reopen recupera. |
| Disco cheio durante commit | Transação falha, WAL reverte, erro retornado ao usuário. |
| WAL > 100 MB | Checkpoint forçado no próximo idle. |
| Abrir arquivo de versão futura | Erro legível: "Documento criado com versão X.Y.Z, esta versão suporta até A.B.C." |
| Bundle corrompido (CRC inválido) | Importação falha com erro legível. |
| Dois processos abrindo o mesmo arquivo | SQLite WAL suporta leitores concorrentes. Escrita única via lock. Segundo processo pode ler, não escrever. |

## 10. Estratégia de Verificação

| Tipo | O que verifica | Como |
|------|---------------|------|
| [BEH] | Crash recovery, round-trip, bundle | Teste de injeção de falha (1.000 kill -9) |
| [PERF] | Abertura ≤ 2 s, commit ≤ 100 ms | Benchmark com criterion + R-A |
| [CONF] | Schema oplog e bundle | CI: validação contra JSON Schema |

## 11. Decisões Técnicas

### TD-001 — SQLite WAL vs. DELETE journal
**Decisão:** WAL. Leitores não bloqueiam escritores. Melhor para autosave + render concorrente.

### TD-002 — Compressor de tiles: zstd vs. lz4
**Decisão:** zstd level 3. ~30% menor que lz4 com velocidade comparável para tiles RGBA. Validar no spike (c).

### TD-003 — VACUUM INTO vs. backup API
**Decisão:** `VACUUM INTO` para snapshots. Mais simples, cria arquivo sem WAL.

## 12. Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| SQLite WASM lento com OPFS | Média | Alto | Spike (c) valida; fallback: IndexedDB |
| zstd library incompatível com iOS | Baixa | Médio | zstd-rs compila para iOS; testar no spike (b) |
| Checkpoint bloqueia escrita brevemente | Baixa | Baixo | Checkpoint em idle, nunca durante traço ativo |
