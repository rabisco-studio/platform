# Fluxo de Trabalho da Equipe (como não ter conflitos)

**Versão:** 0.1
**Data:** 2026-11-25
**Status:** Rascunho para aprovação
**Dono:** PMO

## 1. Regras de convivência
1. **Uma spec = um dono = uma branch = um PR por documento.** Nunca editar a spec de outra pessoa sem passar pelo dono.
2. **Fonte única.** Cada fato mora em um lugar (catálogos, `crates.toml`, DDL, contratos). Documentos apontam, não copiam.
3. **Arquivos gerados nunca são editados** (`make docs` os atualiza). Conflito neles se resolve regenerando.
4. **Autor ≠ aprovador.** Quem escreveu não aprova (CODEOWNERS + proteção de branch).
5. **Mudou documento aprovado → CR e portão reaberto** ([change-control](change-control.md)).
6. **`make verify` verde** antes de pedir revisão. O CI roda o mesmo comando.

## 2. Ciclo de uma spec (waterfall com portões)
`IDEA → PLAN → REQUIREMENTS → DESIGN → TASKS → IMPLEMENTATION → REVIEW`

| Portão | Entrada | Saída | Quem aprova |
|---|---|---|---|
| G1 Requisitos | `requirements.md` completo, sem Q aberta, cada FR com `Cobre:` | `.status = requirements:approved` | PO + TL (autor ≠ aprovador) |
| G2 Design | `design.md` mapeia todos os FR; contratos/ADRs citados | `design:approved` | ARQ |
| G3 Tarefas | Tarefas de 1–4 h, todo FR coberto, dependências acíclicas | `tasks:approved` | TL |
| G4 Implementação | Tarefas concluídas, testes, conformance | `implementation:done` | TL + QA |
| G5 Revisão | Critérios de aceite verificados, rastreabilidade fechada | `review:done` | PO |

`.status` só avança por PR de aprovação feito pelo aprovador. Um estado `*:draft` nunca libera a próxima fase.

## 2.1 Templates obrigatórios
Tudo que é compartilhado, lido ou feito por outras pessoas usa o template correspondente: documentos em `docs/templates/`, issues em `.github/ISSUE_TEMPLATE/` e PRs em `.github/PULL_REQUEST_TEMPLATE/`. O índice, com quando usar cada um, quem escreve, quem aprova e onde salvar, é [docs/templates/README.md](../templates/README.md). Documento fora do modelo não é aprovado.

## 3. Branches e commits
- `spec/NNN-slug/<assunto>` documentos de uma spec · `adr/NNN-slug` · `gov/<assunto>` · `contracts/<assunto>` · depois do G3: `feat/NNN-T-xxx`.
- Commits pequenos, mensagem `SPEC-NNN: assunto` (ou `ADR-NNN:`, `GOV:`).
- Rebase na `main` antes do PR; PR com 1 assunto.

## 4. Quem pode mexer em quê
Resumo; a matriz completa está em [ownership-matrix.md](../architecture/ownership-matrix.md) e a aplicação em [.github/CODEOWNERS](../../.github/CODEOWNERS).

| Área | Edita | Aprova |
|---|---|---|
| `contracts/`, `docs/adr/`, `docs/architecture/` | Autor da spec âncora / ADR | Arquitetos |
| `.ai/sdd/specs/NNN-*/` | Dono da spec | Revisor ≠ autor + TL da área |
| `docs/requirements/*-catalog.csv` | PO | PO |
| `docs/governance/`, `.github/`, `tools/`, `Makefile` | PMO | PMO + ARQ |
| arquivos gerados | ninguém | — |

## 5. Se acontecer um conflito
| Situação | Resolução |
|---|---|
| Conflito em arquivo gerado | `make docs` e commitar |
| Duas specs discordam de um fato | O fato mora na fonte única; corrigir as duas para apontar para ela; abrir CR se for contrato |
| Duas pessoas editando a mesma spec | Dono da spec arbitra; a outra propõe via comentário/PR para o dono |
| Divergência de arquitetura | ARQ decide e registra em ADR ou [decision-log](decision-log.md) |

## 6. Verificações automáticas (`make verify`)
Catálogos válidos; specs bem-formadas; `.status` coerente com cabeçalhos; todo FR com `Cobre:`, mapeado no design e coberto por tarefa; tarefas de 1–4 h; dependências acíclicas; ADRs/P-/SPEC- citados existem; crates citados existem em `crates.toml`; caminhos citados existem; links; arquivos gerados atualizados; arquivos de governança presentes.
