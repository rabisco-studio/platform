# Controle de Documentos

**Versão:** 0.1
**Data:** 2026-11-25
**Status:** Rascunho para aprovação
**Dono:** PMO

## 1. Tipos de documento e donos
| Tipo | Local | Dono | Aprovador | Gerado? |
|---|---|---|---|---|
| Constituição | `docs/constitution.md` | Arquiteto-chefe | PO + Arquiteto-chefe | não |
| Steering | `.ai/steering/*.md` | Arquiteto-chefe | Arquiteto-chefe | não |
| ADR | `docs/adr/ADR-NNN-*.md` | Autor da ADR | Arquitetos (CODEOWNERS) | só o índice |
| Spec (requirements/design/tasks) | `.ai/sdd/specs/NNN-slug/` | Autor da spec | Revisor ≠ autor | só o índice |
| Contratos | `contracts/` | Dono da spec âncora | Arquitetos + Tech Leads | não |
| Catálogos | `docs/requirements/*-catalog.csv` | PO | PO | não |
| Rastreabilidade e cobertura | `docs/requirements/{traceability.csv,coverage.md}` | — | — | **sim** |
| Governança | `docs/governance/` | PMO | PO | não |

## 2. Estados de um documento
`Rascunho → Em revisão → Aprovado → (Substituído | Obsoleto)`. Para specs, o estado é o `.status` (fonte única); os cabeçalhos dos `.md` devem concordar (verificado pelo `sdd-check`).

## 3. Versionamento
- Governança: `Versão` MAJOR.MINOR no cabeçalho; MAJOR = mudança aprovada em change request.
- Specs e ADRs: histórico no Git + tabela "Histórico de mudanças" quando alteradas após aprovação.
- Contratos: SemVer próprio (`schema_version`), regras em [contracts/README.md](../../contracts/README.md).

## 4. Arquivos gerados
Nunca editar à mão (`.ai/sdd/INDEX.md`, `coverage.md`, `traceability.csv`, `docs/adr/README.md`). Rode `make docs`; o CI falha se estiverem desatualizados.

## 5. Templates
Todo tipo de documento compartilhado tem template em [docs/templates/](../templates/README.md). Mudança em template é mudança de processo: PR de governança aprovado pelo PMO.

## 6. Convenções
Idioma: português (termos técnicos e identificadores em inglês). Um assunto, um dono, um local (fonte única).
