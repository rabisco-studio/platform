# Resumo dos scripts (tools-summary)

Roteador de `tools/`: **uma linha por script**. Todos usam só a biblioteca padrão do Python 3 (e a CLI `gh` onde falam com o GitHub). O guia detalhado dos scripts do GitHub está em [github/README.md](github/README.md); o que cada workflow faz está em [.github/workflows/README.md](../.github/workflows/README.md).

**Como manter:** o `sdd-check` exige que todo `.py` desta pasta (fora dos testes) apareça aqui.

## tools/sdd/: especificações e verificação
| Script | O que faz | Como roda |
|---|---|---|
| [sdd_check.py](sdd/sdd_check.py) | Valida o repositório: catálogos, specs, `.status`, ADRs, links, governança, diário e arquivos gerados | `make check` / `make strict` |
| [generate.py](sdd/generate.py) | Gera os arquivos derivados: `INDEX.md`, `coverage.md`, `traceability.csv` e o índice de ADRs | `make docs` |
| [sddlib.py](sdd/sddlib.py) | Biblioteca comum: estágios (`STAGES`), leitura de catálogos e tarefas | importada pelos outros |
| [new_spec.py](sdd/new_spec.py) | Cria a pasta de uma spec planejada a partir dos templates | `make new-spec N=018` |
| [build_site.py](sdd/build_site.py) | Gera a página estática de pré-visualização | workflow `pages` |
| [check_crate_deps.py](sdd/check_crate_deps.py) | Confere as dependências dos crates do core contra `crates.toml` (P-01) | workflow `code-ci` |

## tools/github/: automação do GitHub
| Script | O que faz | Usado por |
|---|---|---|
| [setup-labels-milestones.py](github/setup-labels-milestones.py) | Cria ou atualiza os labels e milestones (ensaio por padrão, `--apply` executa) | Manual |
| [check_pr_title.py](github/check_pr_title.py) | Valida o prefixo do título do PR | workflow `pr-title` |
| [check_gate.py](github/check_gate.py) | Valida PRs que mudam um `.status` | workflow `gate-check` |
| [impact_comment.py](github/impact_comment.py) | Comenta o impacto de um PR nas specs, requisitos e ADRs | workflow `impact-comment` |
| [move_card.py](github/move_card.py) | Move o card da spec no quadro | workflow `move-card` |
| [overdue.py](github/overdue.py) | Lista decisões e perguntas abertas vencidas ou sem data | workflow `weekly` |
| [weekly_report.py](github/weekly_report.py) | Monta o rascunho do relatório semanal e abre a issue da semana | workflow `weekly` |
| [nudge_blocked.py](github/nudge_blocked.py) | Cobra issues `bloqueado` há mais de 7 dias | workflow `weekly` |
| [tasks_to_issues.py](github/tasks_to_issues.py) | Gera as issues de tarefa de uma spec (ensaio por padrão, só após o G3) | Manual |
| [baseline_notes.py](github/baseline_notes.py) | Valida a tag de baseline e monta as notas do release | workflow `baseline-release` |
| [ghlib.py](github/ghlib.py) | Funções comuns (git, gh, anotações do Actions) | importada pelos outros |

## Testes
`make test-tools` roda os testes em [github/tests/](github/tests/) e [sdd/tests/](sdd/tests/) (repositórios git temporários e `gh` simulado: nada toca o GitHub). Já faz parte do `make verify`.
