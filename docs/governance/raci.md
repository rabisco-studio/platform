# Matriz RACI

**Versão:** 0.1
**Data:** 2026-11-25
**Status:** Rascunho para aprovação
**Dono:** PMO

Papéis: **PO** Product Owner · **ARQ** Arquiteto-chefe · **TL** Tech Lead de área (core/backend/clients) · **DEV** Desenvolvedor · **QA** Qualidade · **PMO** Gestão do projeto · **SEC** Segurança/Privacidade.
R = Responsável (executa) · A = Aprovador (um só) · C = Consultado · I = Informado.

| Atividade | PO | ARQ | TL | DEV | QA | PMO | SEC |
|---|---|---|---|---|---|---|---|
| Visão e prioridades (catálogo) | A | C | C | I | I | R | I |
| Escrever requirements.md | C | C | A | R | C | I | C |
| Aprovar gate de requisitos | A | C | C | I | C | I | C |
| Escrever design.md | I | A | R | C | C | I | C |
| Aprovar gate de design | I | A | C | I | C | I | C |
| Escrever tasks.md | I | C | A | R | C | I | I |
| Aprovar gate de tarefas | I | C | A | I | C | I | I |
| ADR (propor / aprovar) | C | A | R | C | I | I | C |
| Contratos (`contracts/`) | I | A | R | C | C | I | C |
| Implementação | I | C | A | R | C | I | I |
| Revisão de código e CI | I | C | A | R | C | I | I |
| Controle de mudanças | A | C | C | I | I | R | I |
| Riscos | C | C | C | I | I | A/R | C |
| Segurança e privacidade (DPIA) | C | C | C | I | I | I | A/R |
| Release e baseline | A | C | C | I | R | R | C |

**Regra:** cada linha tem exatamente um A; o autor de um documento nunca é o seu aprovador (4 olhos). Nomes reais: preencher em [ownership-matrix.md](../architecture/ownership-matrix.md) e `.github/CODEOWNERS`.
