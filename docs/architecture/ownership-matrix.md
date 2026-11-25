# Matriz de Propriedade (quem é dono de quê)

**Versão:** 0.1
**Data:** 2026-11-25
**Status:** Rascunho para aprovação
**Dono:** Arquiteto-chefe

Cada tipo, tabela, contrato e crate tem **um** dono. Quem precisa de mudança fala com o dono (CR se for contrato). Crates e arestas permitidas: [crates.toml](crates.toml).

| Artefato | Dono (spec) | Observação |
|---|---|---|
| `hybrid-schema-v1.sql` (DDL único) | SPEC-002 | Nenhuma outra spec define tabelas |
| `scene.json`, tipos de nó, `NodeRecord`, `TileRefRecord`, `DocumentMetaRecord` | SPEC-001 | Records vivem em `core-domain` |
| `operation.json`, `OpRecord`, HLC, `apply_operation` | SPEC-003 | `OpRecord` é DTO de `core-domain` |
| `TileHash`, `TileStore` (trait), tipos de tile | SPEC-001 (tipos) / SPEC-006 (memória) | Em `core-domain` |
| `bundle-manifest.json` | SPEC-002 | |
| `brush.json`, `StrokeResult` | SPEC-005 | |
| `InputSample`, suavização | SPEC-005 | Crate `input-engine` |
| Blend set de 19 valores | SPEC-001 (D-003) | Mapeamento ORA: SPEC-013 |
| `GpuContext`, composição | SPEC-004 | `render-engine` |
| Interface `Tool` | `core-domain` (SPEC-001) | Plugins só dependem dela |
| Seleção e transformação | SPEC-007 | Fora da SPEC-005 |
| `document-engine` (orquestração) | SPEC-003 | Une edição, histórico, render e persistência |
| Protocolo de sync | SPEC-021 | |
| `crates.toml` | Arquiteto-chefe | Mudança = C3 |
