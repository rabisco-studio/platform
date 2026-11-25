# Rabisco — Repositório de Especificações (`rabisco-studio/platform`)

**Rabisco** é uma plataforma de arte digital híbrida (raster + vetor). Este repositório contém **somente especificações e governança**; o código só começa após os portões de cada spec (modelo waterfall via Spec-Driven Development).

> **Estado da baseline:** fundações completas (constituição, steering, 18 ADRs, contratos, 5 planos de spike, governança e automação). **4 de 37 specs escritas**, todas em `requirements:draft`. Veja a [cobertura](docs/requirements/coverage.md).

## Por onde começar
| Eu sou… | Leia |
|---|---|
| Qualquer pessoa nova | [Charter](docs/governance/project-charter.md) → [Fluxo da equipe](docs/governance/team-workflow.md) |
| Product Owner | [Catálogo de requisitos](docs/requirements/requirements-catalog.csv) · [Cobertura](docs/requirements/coverage.md) · [Decisões abertas](docs/governance/decision-log.md) |
| Arquiteto | [Constituição](docs/constitution.md) · [ADRs](docs/adr/README.md) · [Crates](docs/architecture/crates.toml) · [Propriedade](docs/architecture/ownership-matrix.md) |
| Dev / autor de spec | [AGENTS.md](AGENTS.md) · [Índice de specs](.ai/sdd/INDEX.md) · [Templates](docs/templates/README.md) |
| Gestão / PMO | [Guia GitHub](docs/governance/github-setup.md) · [Issues](docs/governance/issue-conventions.md) · [RACI](docs/governance/raci.md) · [Riscos](docs/governance/risk-register.md) · [Cronograma](docs/governance/schedule-wbs.md) · [Mudanças](docs/governance/change-control.md) |

## Estrutura
```
docs/constitution.md        Princípios P-01..P-11
docs/adr/                   Decisões de arquitetura (ADR-001..018)
docs/architecture/          crates.toml, matriz de propriedade
docs/requirements/          Catálogos (fonte) + rastreabilidade e cobertura (gerados)
docs/governance/            Charter, RACI, mudanças, riscos, decisões, cronograma, glossário
docs/templates/             Modelos de todos os documentos compartilhados (índice em README.md)
.ai/steering/               Contexto técnico permanente
.ai/sdd/                    PLAN, INDEX (gerado) e specs/NNN-slug/
contracts/                  Contratos legíveis por máquina (fonte única)
spikes/                     Planos da Fase 0
tools/sdd/                  sdd-check e gerador
.github/                    CODEOWNERS, CI, regra da main, templates de issue e de PR
```

## Comandos
```
make verify   # regenera derivados + valida tudo (o CI roda o mesmo)
make docs     # só regenera arquivos gerados
make strict   # avisos também falham (baseline de release)
```
Requer apenas Python 3.

## Regras de ouro
1. Uma spec, um dono, um PR. 2. Fonte única para cada fato. 3. Arquivos gerados não se editam. 4. Autor ≠ aprovador. 5. Mudou algo aprovado → Change Request e portão reaberto.

Repositório: `rabisco-studio/platform`. Atribuição do método: [ATTRIBUTION.md](ATTRIBUTION.md).
