# Índice de templates

**Versão:** 0.1
**Data:** 2026-11-25
**Status:** Rascunho para aprovação
**Dono:** PMO

**Regra:** tudo que é compartilhado, lido ou feito por outras pessoas usa o template correspondente. Documento fora do modelo não é aprovado. Copie o template, preencha todos os campos e apague as instruções. Templates não têm links de markdown, para que o verificador não os trate como referências reais.

## Documentos (em docs/templates/)
| Template | Quando usar | Quem escreve | Quem revisa/aprova | Onde salvar |
|---|---|---|---|---|
| [spec-requirements-template.md](spec-requirements-template.md) | Requisitos de uma spec (G1) | Dono da spec | PO + tech lead | .ai/sdd/specs/NNN-slug/requirements.md |
| [spec-design-template.md](spec-design-template.md) | Design de uma spec (G2) | Dono da spec | Arquiteto | .ai/sdd/specs/NNN-slug/design.md |
| [spec-tasks-template.md](spec-tasks-template.md) | Tarefas de uma spec (G3) | Dono da spec | Tech lead | .ai/sdd/specs/NNN-slug/tasks.md |
| [adr-template.md](adr-template.md) | Decisão de arquitetura | Autor da ADR | Arquitetos | docs/adr/ADR-NNN-slug.md |
| [spike-plan-template.md](spike-plan-template.md) | Planejar um spike | Arquiteto | Arquitetos | spikes/spike-x-nome/README.md |
| [spike-report-template.md](spike-report-template.md) | Relatar o resultado de um spike | Quem executou | Revisor diferente do autor | spikes/spike-x-nome/report.md |
| [gate-review-template.md](gate-review-template.md) | Registrar a revisão de um gate G1 a G5 | Aprovador | (é o registro da aprovação) | Comentário no PR do .status |
| [test-plan-template.md](test-plan-template.md) | Plano de testes de uma spec | QA ou tech lead | Tech lead | .ai/sdd/specs/NNN-slug/test-plan.md |
| [privacy-impact-template.md](privacy-impact-template.md) | Funcionalidade com dados pessoais (DPIA) | SEC | SEC + PO | docs/governance/dpia/NOME.md |
| [decision-entry-template.md](decision-entry-template.md) | Decisão relevante (detalhe de DEC-nnn) | Dono da decisão | Quem decide | Issue de pergunta e linha no decision-log |
| [risk-entry-template.md](risk-entry-template.md) | Risco de exposição 12 ou mais | Dono do risco | PMO | Linha no risk-register e issue |
| [release-baseline-template.md](release-baseline-template.md) | Congelar a baseline de um release | PMO | PO + Arquiteto-chefe | docs/governance/baselines/ |
| [status-report-template.md](status-report-template.md) | Relatório semanal | PMO | (informativo) | Discussão ou issue da semana |
| [meeting-minutes-template.md](meeting-minutes-template.md) | Ata de reunião | Redator | Facilitador | Issue ou discussão da reunião |
| [onboarding-checklist-template.md](onboarding-checklist-template.md) | Entrada de uma pessoa nova | Responsável pelo onboarding | PMO | Issue da pessoa |
| [handover-template.md](handover-template.md) | Troca de dono de spec, área ou atividade | Quem sai | Quem recebe + PMO | Issue ou PR |

## Issues (formulários em .github/ISSUE_TEMPLATE/)
| Formulário | Quando usar |
|---|---|
| change-request.yml | Mudar algo aprovado, contrato ou arquitetura |
| gate-approval.yml | Pedir aprovação de G1 a G5 |
| task.yml | Tarefa T-xxx, só após o G3 |
| spike.yml | Experimento da Fase 0 |
| open-question.yml | Pergunta Q-xxx ou decisão pendente |
| defect.yml | Defeito em documento ou código |

## Pull requests (em .github/PULL_REQUEST_TEMPLATE/)
Abra o PR com o template do tipo certo, adicionando `?template=<arquivo>` ao final do endereço de criação do PR.

| Template | Quando usar |
|---|---|
| spec.md | Escrever ou alterar requirements, design ou tasks |
| gate.md | Alterar o .status (aprovação de portão); só o aprovador |
| adr.md | Criar ou alterar uma ADR |
| contract.md | Alterar contracts/ ou crates.toml |
| governance.md | Governança, catálogos, tooling e documentação em geral |
| code.md | Código, somente após o G3 da spec |
