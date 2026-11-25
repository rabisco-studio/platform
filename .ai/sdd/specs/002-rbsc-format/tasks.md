# SPEC-002: Formato `.rbsc` e Ciclo de Vida do Documento — Tasks

**Status:** tasks:draft (rascunho antecipado; não vinculante até design:approved)
**Requisitos:** `requirements.md`
**Design:** `design.md`

---

## Verificação de Prontidão

- [x] requirements.md escrito
- [x] design.md escrito
- [x] Todas as perguntas Q-* respondidas
- [ ] requirements:approved
- [ ] design:approved

## Cobertura FR → Tarefas

| FR | Tarefa(s) |
|----|-----------|
| FR-001 | T-001 |
| FR-002 | T-002 |
| FR-003 | T-003 |
| FR-004 | T-004 |
| FR-005 | T-005 (garantido pelo SQLite WAL; a tarefa o comprova) |
| FR-006 | T-002, T-006 |
| FR-007 | T-004 |
| FR-008 | T-007 |
| FR-009 | T-008 |
| FR-010 | T-008 |
| FR-011 | T-009 |
| FR-012 | T-009 |
| FR-013 | T-010 |

## Tarefas

### T-001 — Criar documento novo e DDL do formato (file-engine::create)
**Requisito:** FR-001
**Prioridade:** Must | **Estimativa:** 3h
**Dependências:** SPEC-001 T-004 (DocumentMetaRecord), SPEC-001 T-009 (registros)
**Checklist:**
- [ ] Criar crate `file-engine` em `core/file-engine/`
- [ ] Versionar `contracts/document-format/rbsc-schema-v1.sql` (já rascunhado no repositório) e embuti-lo no crate (`include_str!`)
- [ ] `FileEngine::create(path, meta) -> Result<DocHandle>`
- [ ] Inicializar SQLite com `PRAGMA journal_mode=WAL` e `foreign_keys=ON`
- [ ] Inserir `document_meta`, a árvore mínima (Document + Artboard + RasterLayer, via `scene-engine`) e `file_meta` (schema_version, doc_id)
**AC:** Arquivo criado, abrível, schema idêntico ao `.sql`, 1 camada raster.
**Arquivos:** `core/file-engine/src/lib.rs`, `core/file-engine/src/schema.rs`, `contracts/document-format/rbsc-schema-v1.sql`
**Verificação:** `cargo test -p file-engine -- --test create`

### T-002 — Abrir documento existente (file-engine::open)
**Requisito:** FR-002, FR-006
**Prioridade:** Must | **Estimativa:** 4h
**Dependências:** T-001, SPEC-001 T-009
**Checklist:**
- [ ] `FileEngine::open(path) -> Result<(DocHandle, SceneRecords)>`
- [ ] PRAGMA integrity_check
- [ ] Verificar schema_version (igual = ok, anterior = migração (T-010), futura = erro legível)
- [ ] Carregar `document_meta` e `nodes` como registros
- [ ] Calcular viewport e carregar tiles visíveis (fases 1 e 2 do plano de abertura)
- [ ] Benchmark `open_ra`: fixture R-A em SQLite, primeiro quadro ≤ 2 s
**AC:** R-A abre com primeiro quadro ≤ 2 s. Documento de versão futura retorna erro legível.
**Arquivos:** `core/file-engine/src/read.rs`, `core/file-engine/benches/open.rs`
**Verificação:** `cargo test -p file-engine -- --test open && cargo bench -p file-engine -- open_ra`

### T-003 — Recuperação e integrity check
**Requisito:** FR-003, FR-005
**Prioridade:** Must | **Estimativa:** 3h
**Dependências:** T-002
**Checklist:**
- [ ] Se integrity_check falhar: tentar WAL replay (reopen)
- [ ] Se replay falhar: retornar `Err(Corrupted { suggestion: "Restaure o backup" })`
- [ ] Logging de cada tentativa de recuperação
**AC:** Documento com WAL corrompido artificialmente: recupera ou reporta erro.
**Verificação:** `cargo test -p file-engine -- --test recovery`

### T-004 — Commit atômico de lotes (CommitBatch)
**Requisito:** FR-004, FR-007
**Prioridade:** Must | **Estimativa:** 4h
**Dependências:** T-001, SPEC-003 T-001 (DTO `OpRecord` em core-domain)
**Checklist:**
- [ ] `DocHandle::commit(batch: CommitBatch) -> Result<()>`
- [ ] BEGIN IMMEDIATE → INSERT oplog → UPSERT tiles → UPSERT/DELETE tile_refs → UPSERT/DELETE nodes → UPDATE file_meta → COMMIT
- [ ] Rollback integral se qualquer etapa falhar
- [ ] Medir latência; registrar aviso se > 100 ms
- [ ] Não conhece `Operation` nem `SceneGraph` (só registros)
**AC:** Commit de 4 tiles (tamanho típico de traço) em p95 ≤ 100 ms. Falha no meio da transação não deixa estado parcial.
**Arquivos:** `core/file-engine/src/commit.rs`, `core/file-engine/benches/commit.rs`
**Verificação:** `cargo test -p file-engine -- --test commit && cargo bench -p file-engine -- commit_stroke`

### T-005 — Teste de injeção de falhas (crash safety)
**Requisito:** FR-005, NFR-001
**Prioridade:** Must | **Estimativa:** 4h
**Dependências:** T-004
**Checklist:**
- [ ] Harness de teste: fork + kill -9 em momentos aleatórios durante commit
- [ ] Executar 1.000 interrupções
- [ ] Após cada interrupção: reabrir e verificar integrity_check + contagem de operações
- [ ] Assert: 0 corrupções, 0 operações perdidas que tinham commit
**AC:** 1.000/1.000 recuperações sem corrupção.
**Verificação:** `cargo test -p file-engine -- --test crash_safety --ignored` (lento, CI noturno)

### T-006 — Carregamento progressivo de tiles
**Requisito:** FR-006, NFR-002
**Prioridade:** Must | **Estimativa:** 3h
**Dependências:** T-002
**Checklist:**
- [ ] `TileLoader` em thread pool: carrega tiles por prioridade (distância ao viewport)
- [ ] `BoundedTileCache` (LRU simples) com budget configurável por plataforma, atrás do trait `TileCachePolicy` para a SPEC-006 substituir a política
- [ ] Respeitar o budget: nunca exceder o limite configurado (a remoção sob pressão do sistema é da SPEC-006)
- [ ] API: `request_tiles(viewport_rect) -> Vec<TileHash>` para o compositor
**AC:** R-A abre com tiles visíveis em ≤ 2 s. Tiles fora do viewport carregam em background.
**Verificação:** `cargo test -p file-engine -- --test progressive_load`

### T-007 — Fila de commits e flush para background (mobile)
**Requisito:** FR-008
**Prioridade:** Must | **Estimativa:** 3h
**Dependências:** T-004
**Checklist:**
- [ ] `CommitQueue::enqueue(batch)` não bloqueante; thread de escrita drena a fila e notifica cada COMMIT
- [ ] `DocHandle::flush_pending() -> Result<()>`: bloqueia até a fila esvaziar e o WAL ser sincronizado
- [ ] Hook no bridge Dart: `AppLifecycleState.paused` → chamada FFI de `flush_pending`
- [ ] Registrar aviso se o flush levar mais de 500 ms
**AC:** Com 10 lotes enfileirados, `flush_pending` retorna só depois de todos confirmados. Fechar o processo logo após o retorno preserva os 10.
**Arquivos:** `core/file-engine/src/queue.rs`
**Verificação:** `cargo test -p file-engine -- --test flush_pending`

### T-008 — Backup local e Save As
**Requisito:** FR-009, FR-010
**Prioridade:** Should | **Estimativa:** 3h
**Dependências:** T-002
**Checklist:**
- [ ] `DocHandle::backup(target_path) -> Result<()>` via `VACUUM INTO`
- [ ] `DocHandle::save_as(new_path) -> Result<DocHandle>` = backup + reopen
- [ ] Timer configurável para backup periódico (padrão: desligado)
**AC:** Backup cria cópia válida. Save As retorna novo DocHandle no novo path.
**Verificação:** `cargo test -p file-engine -- --test backup_save_as`

### T-009 — Bundle export/import
**Requisito:** FR-011, FR-012
**Prioridade:** Must | **Estimativa:** 4h
**Dependências:** T-002
**Checklist:**
- [ ] `BundleExporter::export(doc: &DocHandle, zip_path: &Path) -> Result<()>`
  - VACUUM INTO temp
  - Gerar manifesto JSON
  - ZIP deflate: manifest.json + document.db
- [ ] `BundleImporter::import(zip_path: &Path, target_dir: &Path) -> Result<DocHandle>`
  - Extrair, validar manifesto, integrity_check, mover, abrir
- [ ] Schema: `contracts/document-format/bundle-manifest.json`
**AC:** Export → Import → Export preserva o conteúdo lógico: todas as tabelas iguais linha a linha (comparação por consulta; os bytes do ZIP podem diferir por timestamps).
**Verificação:** `cargo test -p file-engine -- --test bundle`

### T-010 — Migração de schema com backup
**Requisito:** FR-013, NFR-003
**Prioridade:** Must | **Estimativa:** 3h
**Dependências:** T-002
**Checklist:**
- [ ] `MigrationRegistry`: funções `vN -> vN+1` registradas por versão semântica
- [ ] Antes de migrar: cópia de segurança `<nome>.pre-migration-<versão>.rbsc`
- [ ] Executar a cadeia de migrações em uma transação; falha preserva o arquivo original
- [ ] Corpus `tests/compat/`: um arquivo por versão publicada do formato (na 1.0.0, o próprio arquivo de referência)
- [ ] Teste: abrir todo o corpus a cada build (P-07)
**AC:** Arquivo de versão anterior simulada abre migrado; migração com falha injetada mantém o original intacto.
**Arquivos:** `core/file-engine/src/migrate.rs`, `tests/compat/`
**Verificação:** `cargo test -p file-engine -- --test migrate`

## Ordem de Execução

```
T-001 (create + DDL) ← SPEC-001 T-004, T-009
  ├─ T-002 (open)
  │    ├─ T-003 (recovery)
  │    ├─ T-006 (progressive load)
  │    ├─ T-008 (backup/save as)
  │    ├─ T-009 (bundle)
  │    └─ T-010 (migração)
  └─ T-004 (commit) ← também SPEC-003 T-001 (OpRecord)
       ├─ T-005 (crash safety)
       └─ T-007 (fila + flush mobile)
```

## Riscos de Implementação

| Risco | Mitigação |
|-------|-----------|
| Teste de crash safety é lento (~30 min) | Executar apenas no CI noturno |
| `VACUUM INTO` lento em documentos grandes | Aceitar para backup/bundle; não usar para autosave |
| LRU eviction race com render thread | Proteger com Arc<RwLock> ou canal |
