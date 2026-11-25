# tools/github

Scripts de apoio à configuração do GitHub (labels, milestones e quadro). Só usam a biblioteca padrão do Python 3 e a CLI [`gh`](https://cli.github.com), autenticada com `gh auth login`. Dono: PMO (veja o [CODEOWNERS](../../.github/CODEOWNERS)).

| Script | O que faz | Estado |
|---|---|---|
| [`setup-labels-milestones.py`](setup-labels-milestones.py) | Cria ou atualiza os 14 labels e os 6 milestones do repositório | Neste repositório |
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
