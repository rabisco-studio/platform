# Diário — 2026-11-25

**Data:** 2026-11-25
**Autor:** maria-brito15
**Escrita com IA:** sim (rascunho feito com o Claude Code a partir da sessão do dia; revisão do autor pendente)

## Resumo do dia
Primeiro dia de automação do repositório. Foram mescladas as Camadas 1, 2 e 3 da governança (labels e milestones, workflows de PR, quadro, issues, baseline, CI de código), a licença proprietária e a troca de nome do formato de `.hybrid` para `.rbsc`. Na segunda parte do dia entraram os resumos de uma linha por documento, a guarda de nomenclatura e os testes práticos no sandbox. O repositório passou a ter 111 testes de scripts rodando no `make verify`.

## O que foi feito
- **Camada 1 (PR #1 e #2):** script `tools/github/setup-labels-milestones.py` (ensaio por padrão, idempotente, nunca apaga); labels e milestones aplicados no repositório (as 6 descrições de milestone foram ajustadas). Documentado o desenho do quadro: só issues `task` entram, em Implementação; "Item closed" leva a Feito.
- **Camada 2 (PR #3):** workflows `labeler`, `pr-title`, `gate-check`, `impact-comment`, `move-card` e `weekly`, com scripts em `tools/github/` e testes. Testes práticos feitos: o `weekly` criou a issue #4 sem duplicar no segundo disparo; uma issue `task` de teste entrou no quadro em Implementação e foi para Feito ao fechar (issue e card apagados depois).
- **Licença (PR #5):** arquivo [LICENSE](../../../LICENSE) proprietário, todos os direitos reservados, com a exceção da parte derivada do método SDD (CC BY-NC-SA 4.0).
- **Camada 3 (PR #7):** `make new-spec`, `tasks_to_issues.py` (ensaio por padrão), `baseline-release` (pre-release), `pages` (desligado), `code-ci` (hoje: "sem código ainda") e `check_crate_deps.py`.
- **Nomenclatura (PR #9):** produto **Rabisco** e formato **`.rbsc`** em 37 arquivos; mantidos `HybridLogicalClock` e o adjetivo "híbrido".
- **Resumos (PR #11):** `*-summary.md` de uma linha por documento, mapa `docs/README.md`, `.github/workflows/README.md` e `check_summaries` no `sdd_check`.
- **Guarda de nomenclatura (PR #12):** `sdd_check` falha se os nomes antigos (extensão e identificadores com o prefixo anterior) voltarem; exceções justificadas em `tools/sdd/naming-allow.txt`; 5 testes. Reaproveitada do commit 3195af8 do PR #8, que foi **fechado** por duplicar o #9.
- **Sandbox privado (apagar ao final):** `baseline-R1-v1` gerou o pre-release e `baseline-R9-v1` foi rejeitada; labels e milestones idempotentes; `code-ci` passou com um `core/` mínimo e falhou com aresta proibida; o gate aberto pela autora da spec falhou; o `weekly` disparado duas vezes criou 1 issue. O `tasks_to_issues --apply` rodado duas vezes seguidas **duplicou** 2 issues (consistência eventual da listagem); corrigido neste PR.
- **Exceções temporárias na proteção da `main`** (autorizadas uma a uma por você; horário local, regra restaurada logo após cada merge):

| PR | Relaxada | Restaurada |
|---|---|---|
| #1 | 13:26:03 | 13:27:24 |
| #2 | 13:33:40 | 13:34:02 |
| #3 | 13:53:41 | 13:54:49 |
| #5 | 14:39:20 | 14:40:36 |
| #7 | 16:03:34 | 16:03:46 |
| #9 | 16:13:20 | 16:13:30 |
| #10 | (ver o comentário no PR #10) | (ver o comentário no PR #10) |
| #11 | (ver o comentário no PR #11) | (ver o comentário no PR #11) |
| #12 | (ver o comentário no PR #12) | (ver o comentário no PR #12) |
| #13 | (ver o comentário no PR #13) | (ver o comentário no PR #13) |
| #14 | (ver o comentário no PR #14) | (ver o comentário no PR #14) |

## Decisões do dia
- **DEC-003:** licença proprietária adotada; pendências de titular e de revisão jurídica.
- **DEC-015:** registro das exceções acima.
- **DEC-016:** nomenclatura Rabisco / `.rbsc`. Ver o [decision-log](../../../docs/governance/decision-log.md).

## Problemas e como foram resolvidos
- **Ruleset com valor diferente do arquivo versionado:** a contagem de aprovações estava em 0 no GitHub e em 1 no arquivo. Corrigido na primeira restauração.
- **`check_gate.py` tratava `.status` novo como gate:** renomear a pasta de uma spec (ou criar uma com `make new-spec`) falhava o check no PR #9. Corrigido no próprio PR, com 4 testes novos.
- **Python 3.12 do CI:** `Path.read_text(newline=...)` só existe no 3.13; o CI do PR #7 acusou e foi corrigido.
- **`sdd_check` embaralhava acentos no Windows** ao ler a saída do gerador. Corrigido.
- **Nome do quadro:** no GitHub é "Rabisco Studio" (projeto nº 1), e a documentação dizia "Rabisco Platform". O `move_card.py` aceita os dois.
- **Fork:** o GitHub não permite desativar fork em repositório público; a licença proíbe o uso da cópia, mas não impede o fork.
- **Bloqueios do sistema de permissões do Claude Code:** relaxar o ruleset sem a frase "exceção temporária" e criar o repositório de sandbox sem confirmação explícita foram negados; nenhum dos dois foi contornado.

## Pendências e próximos passos
- [ ] Apagar o repositório `rabisco-studio/sandbox`: exige `gh auth refresh -s delete_repo` (ou a interface). Pages fica desligado por decisão.
- [ ] O `move-card` com o `PROJECT_TOKEN` real ainda não foi exercitado; só acontece no primeiro PR de gate mesclado.
- [ ] Trocar o domínio de exemplo `rabisco.example` nos `$id` dos schemas pelo real.
- [ ] Licença: confirmar o titular, revisão jurídica da convivência com a CC BY-NC-SA e decidir sobre repositório privado antes do primeiro código de produto.
- [ ] Preencher "Depende de" e "Tags" quando as specs novas forem criadas; instalar o `actionlint` para validar os workflows.

## Referências
- [Guia dos scripts](../../../tools/github/README.md)
- [Fluxo da equipe, seções 7 e 8 (automações)](../../../docs/governance/team-workflow.md)
- [Registro de decisões](../../../docs/governance/decision-log.md)
