# ADR-007 — Formato nativo `.rbsc` (SQLite + bundle ZIP)

**Status:** Proposta
**Origem:** Revisada na v2
**Data:** 2026-11-24
**Resolvida por:** Spike (c)
**Requisitos relacionados:** RF-02 (documentos), RNF-02 (confiabilidade), RNF-07.6 (compatibilidade)

## 1. Contexto e problema

O formato nativo precisa de atomicidade (interrupção durante salvamento não corrompe), carga parcial de tiles, evolução controlada de schema e funcionamento no navegador.

## 2. Alternativas consideradas

### Alternativa A — SQLite em modo WAL (formato de trabalho) + ZIP (troca)
- Transações atômicas. Carga parcial. Índices. WASM com OPFS.

### Alternativa B — ZIP com JSON e blobs (v1)
- Simples e transparente.
- Desvantagem: sem atomicidade, reescreve o arquivo inteiro a cada salvamento.

### Alternativa C — Formato binário proprietário
- Controle total.
- Desvantagem: custo de desenvolvimento e manutenção, sem ferramentas existentes.

## 3. Decisão proposta

**Formato de trabalho local:** SQLite em modo WAL.
**Bundle de troca:** ZIP com o SQLite (sem WAL), um manifesto e a mesma estrutura lógica.

Estrutura lógica (DDL em `contracts/document-format/rbsc-schema-v1.sql`, dono: SPEC-002):

```
project.rbsc (SQLite)
├── file_meta      schema_version, doc_id, timestamps, versão do app
├── document_meta  dimensões, DPI, perfil ICC, profundidade, espaço de mesclagem
├── nodes          estado materializado da árvore (SPEC-001)
├── tile_refs      (camada, mip, col, row) -> hash do tile
├── tiles          hash, codec, dados (imutáveis, endereçados por conteúdo)
├── assets         imagens embutidas (hash, mime, dados)
└── oplog          log de operações append-only (SPEC-003)
```

Fonte da verdade: `oplog` + `tiles`. `nodes` e `tile_refs` são o estado materializado, gravado na mesma transação do `oplog`, e podem ser verificados contra o log. Snapshots versionados e miniaturas entram com a ADR-011 (R2) e não existem no schema 1.0.0.

Compressão de tiles: zstd (hipótese a validar no spike (c); alternativa lz4).

## 4. Justificativas

Atomicidade do SQLite resolve o cenário de interrupção. Carga parcial resolve documentos grandes. WASM+OPFS cobre o navegador.

## 5. Consequências

### Positivas
- 0 corrupções em interrupções. Carga sob demanda. Evolução via migrations.

### Negativas
- Dependência do SQLite. Tamanho do arquivo pode ser maior que ZIP comprimido.

## 6. Critérios de reavaliação

- Se o spike (c) mostrar problemas com SQLite em WASM+OPFS.
- Se a abertura de R-A exceder 2 s.

## 7. Referências

- Spike (c): `spikes/spike-c-rbsc-format/README.md`
- DDL: `contracts/document-format/rbsc-schema-v1.sql`
- Specs: SPEC-002 (formato e ciclo de vida), SPEC-003 (oplog)

## Registro de alterações

| Data | Alteração |
|------|-----------|
| 2026-11-25 | Estrutura lógica alinhada ao schema da SPEC-002: `nodes`/`tile_refs` como estado materializado; `snapshots`, `thumbnails` e `manifest` adiados ou renomeados (`file_meta`); coluna `mip` reservada; compressão zstd. |
