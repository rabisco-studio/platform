# Relatório de Revisão da Baseline — 2026-11-25

Auditoria completa do repositório antes do compartilhamento. Resultado final: `make verify` com **0 erros e 0 avisos**.

## Inconsistências encontradas e corrigidas
| # | Problema | Correção |
|---|---|---|
| 1 | PLAN com fases/releases errados em relação à fonte | PLAN reescrito; catálogo de specs como fonte única |
| 2 | Numeração de specs divergente do cânone da fonte | Specs renumeradas (005 = pincéis); 37 specs catalogadas |
| 3 | Ciclo de dependência SPEC-002 ↔ SPEC-003 | `CommitBatch`/`OpRecord` como DTOs em `core-domain`; `document-engine` orquestra |
| 4 | Dois DDLs possíveis do formato | DDL único `rbsc-schema-v1.sql`, dono SPEC-002 |
| 5 | Seleção (RF-03.7, Must) sem dono | SPEC-007; removida da SPEC-005 |
| 6 | FR sem cobertura (SPEC-003 FR-008, SPEC-001 FR-012) e NFR sem tarefa | Mapeados no design e nas tarefas |
| 7 | Afirmação não verificada "27 blend modes ORA 0.0.6" | Conjunto próprio de 19 valores; ORA na SPEC-013 |
| 8 | Compressão e hash de tiles inconsistentes entre docs | zstd + blake3 (hipóteses, spike C) |
| 9 | Terminologia (page/artboard), nomes de crates, grafo de dependências em ASCII | Artboard; `crates.toml` como fonte única |
| 10 | Falta de migração de formato | FR-013/T-010 na SPEC-002 |
| 11 | `.status` e cabeçalhos incoerentes | Todos `requirements:draft`; verificação automática |
| 12 | Prioridade de RNF atribuída a RNF-04.3 à spec errada | Corrigido para SPEC-018 |

## Lacunas honestas
- **Apenas 4 de 37 specs estão escritas** (001, 002, 003, 005). Cobertura de requisitos: ver [coverage.md](../requirements/coverage.md). O produto **não** está totalmente especificado.
- Nenhum gate foi aprovado: toda aprovação é humana e está pendente.
- Prioridades dos RNF e metas numéricas são **hipóteses** (DEC-001, DEC-004).
- Handles do CODEOWNERS são exemplos (DEC-002).

## Decisões abertas que dependem de você
DEC-001 (prioridades RNF), DEC-002 (pessoas/papéis), DEC-003 (licença), DEC-004 (hardware de referência). Cada uma tem padrão recomendado em [decision-log.md](decision-log.md).
