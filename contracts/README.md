# Contratos

**Versão:** 0.1
**Data:** 2026-11-25
**Status:** Rascunho para aprovação
**Dono:** Arquiteto-chefe

Esta pasta é a **fonte única** das interfaces legíveis por máquina (P-06). Código e specs derivam daqui; nunca o contrário.

| Pasta | Conteúdo | Dono |
|---|---|---|
| `document-format/` | `scene.json`, `operation.json`, `bundle-manifest.json`, `rbsc-schema-v1.sql` | SPEC-001, 003, 002 (ver [ownership-matrix](../docs/architecture/ownership-matrix.md)) |
| `brush-definition/` | `brush.json` | SPEC-005 |
| `conformance/` | Casos de teste compartilhados entre implementações | dono do contrato correspondente |
| `api/`, `events/`, `plugin-api/` | Reservadas para as fases 5 e 8 (vazias de propósito) | SPEC-021/022, SPEC-029 |

## Regras
1. Todo contrato tem `schema_version` SemVer. Mudança incompatível = MAJOR + migração (SPEC-002) + CR classe C3.
2. Mudar contrato exige PR dos arquitetos (CODEOWNERS) e reabre o portão das specs dependentes.
3. Todo contrato novo traz casos em `conformance/`.
4. Cada contrato tem um único dono; ninguém duplica o DDL ou os esquemas em specs.
