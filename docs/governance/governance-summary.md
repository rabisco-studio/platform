# Resumo da governança (governance-summary)

**Versão:** 0.1
**Data:** 2026-11-25
**Status:** Rascunho para aprovação
**Dono:** PMO

Roteador dos documentos de `docs/governance/`: **uma linha por documento**. Ao abrir um assunto de processo, comece por aqui.

**Como manter:** o `sdd-check` exige que todo `.md` desta pasta apareça aqui. Ao criar um documento de governança, acrescente a linha.

| Documento | O que é | Quando consultar |
|---|---|---|
| [project-charter.md](project-charter.md) | Termo de abertura: objetivo, escopo e visão do projeto | Quem acabou de chegar |
| [team-workflow.md](team-workflow.md) | Fluxo da equipe: regras de convivência, gates, branches, quem edita o quê e as automações | Antes de abrir o primeiro PR |
| [issue-conventions.md](issue-conventions.md) | Qual formulário de issue usar, labels, milestones e o ciclo de vida do quadro | Ao abrir uma issue |
| [change-control.md](change-control.md) | Como mudar documento aprovado: Change Request, classes C0 a C4 e reabertura do gate | Antes de mexer em algo aprovado |
| [document-control.md](document-control.md) | Ciclo de vida dos documentos (rascunho, aprovado, substituído) e regra dos arquivos gerados | Ao criar ou aposentar um documento |
| [decision-log.md](decision-log.md) | Decisões do projeto (`DEC-nnn`), abertas e tomadas, com padrão recomendado e prazo | Para saber o que já foi decidido |
| [risk-register.md](risk-register.md) | Riscos (`RSK-nn`) com probabilidade, impacto e mitigação | Em toda revisão de gate |
| [raci.md](raci.md) | Matriz de papéis: quem é responsável, aprova, é consultado e informado | Para saber quem decide |
| [schedule-wbs.md](schedule-wbs.md) | Cronograma e estrutura analítica (ainda sem datas) | Para planejar |
| [glossary.md](glossary.md) | Glossário dos termos do projeto | Ao ler um termo desconhecido |
| [github-setup.md](github-setup.md) | Guia de configuração do GitHub: repositório, equipes, ruleset da `main`, quadro, labels, segredos e Pages | Ao configurar ou auditar o GitHub |
| [review-report-2026-11-25.md](review-report-2026-11-25.md) | Relatório da auditoria da baseline de 2026-11-25 (registro histórico) | Para entender o ponto de partida |

Documentos vizinhos que fazem parte da governança, mas moram em outros lugares:
- Princípios inegociáveis: [constitution.md](../constitution.md).
- Quem é dono de cada contrato, tipo e crate: [ownership-matrix.md](../architecture/ownership-matrix.md).
- O que cada workflow do GitHub Actions faz: [workflows/README.md](../../.github/workflows/README.md).
- Diário do projeto: [journal/](../../journal/README.md).
