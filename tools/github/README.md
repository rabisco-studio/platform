# tools/github

Scripts de apoio à configuração do GitHub (labels, milestones e quadro). Só usam a biblioteca padrão do Python 3 e a CLI [`gh`](https://cli.github.com), autenticada com `gh auth login`. Dono: PMO (veja o [CODEOWNERS](../../.github/CODEOWNERS)).

| Script | O que faz | Estado |
|---|---|---|
| [`setup-labels-milestones.py`](setup-labels-milestones.py) | Cria ou atualiza os 15 labels e os 6 milestones do repositório | Neste repositório |
| [`check_pr_title.py`](check_pr_title.py) | Valida o prefixo do título do PR | Workflow `pr-title` |
| [`check_gate.py`](check_gate.py) | Valida PRs que mudam um `.status` (transição, autor, cabeçalhos, template) | Workflow `gate-check` |
| [`impact_comment.py`](impact_comment.py) | Comenta o impacto (requisitos, specs e dependentes) no PR | Workflow `impact-comment` |
| [`move_card.py`](move_card.py) | Move o card da spec para a coluna do novo `.status` | Workflow `move-card` (segredo `PROJECT_TOKEN`) |
| [`overdue.py`](overdue.py) | Lista decisões e perguntas abertas vencidas ou sem data | Workflow `weekly` |
| [`weekly_report.py`](weekly_report.py) | Rascunho do relatório semanal e issue da semana | Workflow `weekly` |
| [`nudge_blocked.py`](nudge_blocked.py) | Cobra issues `bloqueado` há mais de 7 dias | Workflow `weekly` |
| [`tasks_to_issues.py`](tasks_to_issues.py) | Gera as issues de tarefa de uma spec a partir do `tasks.md` (só após o G3; ensaio por padrão, `--apply` cria) | Manual |
| [`baseline_notes.py`](baseline_notes.py) | Valida a tag `baseline-R<n>-v<n>` e monta as notas da baseline | Workflow `baseline-release` |
| [`ghlib.py`](ghlib.py) | Funções comuns (git, gh, anotações do Actions) | Biblioteca |
| `create-board-cards.py` | Cria os cards das specs no quadro "Rabisco Platform" | Entregue à parte; ainda não está nesta pasta |

## setup-labels-milestones.py

```bash
python3 tools/github/setup-labels-milestones.py            # ENSAIO (padrão): somente leitura
python3 tools/github/setup-labels-milestones.py --apply    # executa as mudanças
python3 tools/github/setup-labels-milestones.py --repo ORG/REPO   # outro repositório
```

- **Ensaio por padrão.** Mostra o que criaria (`+`), atualizaria (`~`) e ignoraria (`=`). Só escreve com `--apply`.
- **Idempotente.** O que já existe e está igual é ignorado; diferença de descrição ou cor é atualizada e relatada.
- **Nunca apaga.** Labels e milestones que não estão na lista (como os padrões do GitHub) são só contados.
- **Dados:** labels, cores e milestones vêm do [README](../../README.md) (seções 8 e 9) e de [issue-conventions.md](../../docs/governance/issue-conventions.md). Os milestones são criados sem data de entrega. Para mudar um label ou milestone, edite as listas `LABELS` e `MILESTONES` no topo do script, no mesmo PR que atualiza esses documentos.
- **Permissão:** exige triagem ou escrita no repositório.

| Código de saída | Significado |
|---|---|
| 0 | Concluído (no ensaio, mesmo havendo mudanças a aplicar) |
| 1 | Erro inesperado (rede, resposta inválida) |
| 2 | `gh` ausente ou sem autenticação |
| 3 | Sem permissão, ou repositório inacessível |

Passo a passo completo: [github-setup.md](../../docs/governance/github-setup.md), seção 5.

## Automações do quadro

As automações embutidas do Project (Item added, Item closed, Pull request merged, Auto-add) **não podem ser configuradas por script**; a API do GitHub não as expõe. O checklist de cliques está em [github-setup.md](../../docs/governance/github-setup.md), seção 4.3.

## Testes
`make test-tools` (ou `python3 -m unittest discover -s tools/github/tests -v`) roda os testes dos scripts com repositórios git temporários e `gh` simulado: nada toca o GitHub. Já faz parte do `make verify`.

## Workflows
Gatilhos, segredos e o que acontece sem eles: [team-workflow.md](../../docs/governance/team-workflow.md), seção 7. Como criar `PROJECT_TOKEN` e `ORG_READ_TOKEN`: [github-setup.md](../../docs/governance/github-setup.md), seção 9.

## Camada 3
Scripts que criam coisas no GitHub têm **ensaio por padrão** e só agem com `--apply`:

```bash
python3 tools/github/tasks_to_issues.py 001                  # ensaio: mostra as issues que criaria
python3 tools/github/tasks_to_issues.py 001 --check-existing # ensaio que também consulta o GitHub (marca o que seria ignorado)
python3 tools/github/tasks_to_issues.py 001 --apply          # cria (só se o .status for tasks:approved ou posterior)
python3 tools/github/baseline_notes.py --notes baseline-R1-v1  # imprime as notas, sem criar tag nem release
```

`tasks_to_issues.py --apply` é idempotente (marcador `<!-- task:SPEC-NNN:T-NNN -->`), mas a listagem de issues do GitHub é eventualmente consistente: depois de criar, o script espera até 60 s as issues novas aparecerem e avisa se alguma ainda não aparece. Se o aviso surgir, aguarde alguns minutos antes de rodar `--apply` de novo (a segunda rodada logo em seguida duplicou 2 issues no teste do sandbox).

Tabela de todas as automações da Camada 3 (gatilho, flag, o que fazer se der errado): [team-workflow.md](../../docs/governance/team-workflow.md), seção 8. Em `tools/sdd/`: `new_spec.py`, `build_site.py` e `check_crate_deps.py`, também com testes (`tools/sdd/tests`).
