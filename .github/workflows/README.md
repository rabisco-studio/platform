# Workflows do GitHub Actions

O que cada workflow desta pasta faz, quando roda, o que precisa e o que fazer se falhar. Visão de equipe: [team-workflow.md](../../docs/governance/team-workflow.md), seções 7 e 8. Segredos e variáveis: [github-setup.md](../../docs/governance/github-setup.md), seções 9 a 11. Os scripts ficam em [`tools/`](../../tools/tools-summary.md).

**Regras comuns a todos:** `permissions:` explícito e mínimo; evento `pull_request` (nunca `pull_request_target`); actions de terceiros fixadas por SHA de commit; dados do PR (título, corpo, autor) passados por variáveis de ambiente, nunca interpolados no shell; o que depende de segredo detecta a ausência, avisa e termina com sucesso.

| Workflow | Arquivo | Gatilho | Resumo |
|---|---|---|---|
| `sdd-check` | [sdd-check.yml](sdd-check.yml) | PR e push na `main` | Roda `make verify`: gerados em dia, `sdd-check` e testes dos scripts. **É o check obrigatório (`verify`)** |
| `labeler` | [labeler.yml](labeler.yml) | PR | Aplica labels por pasta |
| `pr-title` | [pr-title.yml](pr-title.yml) | PR (inclui edição do título) | Valida o prefixo do título |
| `gate-check` | [gate-check.yml](gate-check.yml) | PR que muda um `.status` | Valida a transição de gate |
| `impact-comment` | [impact-comment.yml](impact-comment.yml) | PR em specs, ADRs, contratos ou catálogos | Comenta o impacto |
| `move-card` | [move-card.yml](move-card.yml) | Push na `main` que muda um `.status` | Move o card da spec no quadro |
| `weekly` | [weekly.yml](weekly.yml) | Segunda 12:00 UTC e manual | Relatório semanal e cobrança de `bloqueado` |
| `baseline-release` | [baseline-release.yml](baseline-release.yml) | Push de tag `baseline-*` | Cria um pre-release com as notas da baseline |
| `pages` | [pages.yml](pages.yml) | Push na `main` e manual | Publica o site de pré-visualização (desligado por padrão) |
| `code-ci` | [code-ci.yml](code-ci.yml) | PR e push na `main` | CI do código de produto; hoje "sem código ainda" |

Além dos workflows, [labeler.yml](../labeler.yml) (na pasta `.github/`) é a configuração de pastas e labels usada pelo `labeler`.

---

## sdd-check
- **Gatilho:** `pull_request` e `push` em `main`.
- **O que faz:** (1) `python3 tools/sdd/generate.py --check`: falha com "rode `make docs` e faça commit" se algum arquivo gerado estiver desatualizado; (2) `make verify`, que regenera os derivados, roda o `sdd_check.py` e os testes de `tools/github/tests` e `tools/sdd/tests`.
- **Permissões:** `contents: read`. **Segredos:** nenhum.
- **Se falhar:** leia a mensagem. "Arquivos gerados desatualizados": rode `make docs` e faça commit. Erro do `sdd-check`: o texto aponta o arquivo e a regra. Teste quebrado: rode `make test-tools` localmente.
- **Observação:** o job se chama `verify` e é o único check exigido pelo ruleset da `main`.

## labeler
- **Gatilho:** `pull_request` (aberto, atualizado, reaberto).
- **O que faz:** aplica labels conforme as pastas alteradas (`.github/labeler.yml`): `contracts/` e `docs/architecture/` → `area:platform` + `rigor:anchored`; `core/`, `backend/`, `clients/` → `area:*`; `docs/adr/` → `adr`; `.github/`, `tools/`, `Makefile` → `area:platform`; `spikes/` → `spike`. `.ai/sdd/specs/**` não recebe label. Nunca remove labels.
- **Permissões:** `contents: read`, `pull-requests: write`. **Segredos:** nenhum.
- **PR de fork:** o token é somente leitura; o workflow emite um aviso e não aplica labels.
- **Se falhar:** o passo tem `continue-on-error`; um mantenedor aplica os labels à mão.

## pr-title
- **Gatilho:** `pull_request` (aberto, **editado**, atualizado, reaberto).
- **O que faz:** roda `tools/github/check_pr_title.py`. Aceita `SPEC-NNN:`, `ADR-NNN:`, `GOV:`, `contracts:`, `feat NNN T-xxx:` e `feat/NNN-T-xxx:`.
- **Permissões:** `contents: read`. **Segredos:** nenhum.
- **Se falhar:** a mensagem mostra exemplos válidos; edite o título do PR (o check roda de novo sozinho).

## gate-check
- **Gatilho:** `pull_request` com mudança em `.ai/sdd/specs/*/.status`.
- **O que faz:** roda `tools/github/check_gate.py`: (a) o `.status` avança no máximo uma etapa ou volta por reabertura; (b) o autor do PR não escreveu `requirements.md`, `design.md` ou `tasks.md` da spec, e o PR só muda a linha `**Status:**` deles; (c) o `sdd_check` passa; (d) o corpo usa o template de gate ("## Gate" e "## Registro da revisão"). Com o segredo, confere também a equipe aprovadora do gate.
- **Não é gate:** spec nova (em `requirements:draft`), pasta renomeada sem mudança de estágio e `.status` apagado.
- **Permissões:** `contents: read`. **Segredo:** `ORG_READ_TOKEN` (opcional). Sem ele, a checagem de equipe vira aviso.
- **Se falhar:** cada erro vem numerado (a, b, c, d). O check **não é obrigatório** no ruleset.

## impact-comment
- **Gatilho:** `pull_request` com mudança em `.ai/sdd/specs/**`, `docs/adr/**`, `contracts/**` ou `docs/requirements/**`.
- **O que faz:** roda `tools/github/impact_comment.py` e comenta (ou atualiza o mesmo comentário, pelo marcador oculto) os requisitos RF/RNF afetados, as specs dependentes (de forma transitiva, pelos `tasks.md`) e as specs que citam as ADRs e os contratos alterados.
- **Permissões:** `contents: read`, `pull-requests: write`. **Segredos:** nenhum.
- **PR de fork:** sem permissão para comentar, o script avisa, grava o relatório no resumo do job e termina com sucesso.

## move-card
- **Gatilho:** `push` na `main` com mudança em `.ai/sdd/specs/*/.status` (ou seja, o merge de um PR de gate). Não roda em `pull_request`, para o segredo nunca chegar a código de PR.
- **O que faz:** roda `tools/github/move_card.py`, que move o card da spec para a coluna do novo `.status` (tabela do [README](../../README.md), seção 7), via `gh project item-edit`.
- **Permissões:** `contents: read`. **Segredo:** `PROJECT_TOKEN`; **variável** opcional `PROJECT_NUMBER` (o quadro é o projeto nº 1).
- **Sem o segredo:** avisa e imprime o que faria. Card inexistente: avisa. Em ambos os casos termina com sucesso.
- **Se falhar:** o token expirou ou perdeu o escopo `project`; renove (github-setup.md, seção 9) e mova o card à mão.

## weekly
- **Gatilho:** `schedule` (segunda-feira, 12:00 UTC) e `workflow_dispatch` (manual).
- **O que faz, em ordem:** (1) `overdue.py` lista decisões e perguntas abertas vencidas ou sem data; (2) `weekly_report.py --issue` abre **uma** issue `status-report` por semana, com o rascunho pelo template de relatório (não duplica); (3) `nudge_blocked.py` comenta nas issues `bloqueado` há mais de 7 dias, marcando o responsável, no máximo uma vez a cada 7 dias.
- **Permissões:** `contents: read`, `issues: write`. **Segredos:** nenhum.
- **Se falhar ou faltar label:** sem o label `status-report`, a issue é criada sem label e o log pede `setup-labels-milestones.py --apply`. Sem permissão, avisa e termina com sucesso.
- **Como testar:** Actions → `weekly` → Run workflow; rodar duas vezes não pode duplicar a issue.

## baseline-release
- **Gatilho:** push de tag `baseline-*`. Quem cria a tag é o PMO, depois de `make strict` verde.
- **O que faz:** valida o formato `baseline-R<n>-v<n>` (R1 a R5), roda `make strict`, monta as notas com `baseline_notes.py` (escopo do `INDEX.md`, cobertura do `coverage.md`, decisões abertas, riscos com exposição 12 ou mais, commits desde a baseline anterior) e cria um **pre-release** no GitHub. Se o release já existe, não faz nada.
- **Permissões:** `contents: write` (só neste job). **Segredos:** nenhum.
- **Se falhar:** tag inválida ou `make strict` falho: nada é criado. Para refazer, apague o release (`gh release delete TAG`) e a tag (`git push --delete origin TAG`), corrija e crie de novo.
- **Atenção:** o pre-release **não substitui a aprovação humana**; o PO e o arquiteto-chefe assinam antes de desmarcar "pre-release". Tags não são protegidas pelo ruleset.

## pages
- **Gatilho:** `push` na `main` (caminhos de docs, `.ai/sdd` e `build_site.py`) e `workflow_dispatch`.
- **O que faz:** gera `_site/index.html` com `tools/sdd/build_site.py` (índice de specs, cobertura, decisões abertas, riscos e links) e publica no GitHub Pages. Só a partir da `main`.
- **Condição:** só roda com a variável `PAGES_ENABLED=true` e o Pages habilitado (Settings → Pages → Source: GitHub Actions). Sem a variável, o job `desativado` apenas avisa. **Hoje está desligado, por decisão do projeto.**
- **Permissões:** `contents: read` no build; `pages: write` e `id-token: write` só no deploy.
- **Se falhar:** com o Pages desabilitado, o deploy falha; habilite o Pages ou ponha `PAGES_ENABLED=false`.

## code-ci
- **Gatilho:** `pull_request` e `push` na `main`.
- **O que faz:** o job `detect` verifica se existem `core/Cargo.toml`, ou arquivos reais em `backend/` ou `clients/`. Sem código, tudo termina com sucesso e a mensagem "sem código ainda". Com `core/Cargo.toml`, o job `core` roda `cargo fmt --check`, `cargo clippy -D warnings`, `cargo test` e `tools/sdd/check_crate_deps.py` (arestas de `docs/architecture/crates.toml` e dependências proibidas pelo P-01). O job `resumo` falha se o core falhar.
- **Backend e clients:** jobs esqueleto comentados, com TODO apontando a SPEC-022 (backend) e a SPEC-016 (clientes).
- **Permissões:** `contents: read`. **Segredos:** nenhum.
- **Se falhar:** aresta não permitida: ajuste a dependência, ou, se a mudança for de arquitetura, abra PR em `crates.toml` (aprovação dos arquitetos).

---

## Como validar mudanças nestes arquivos
- Sintaxe YAML (e `actionlint`, se instalado) antes de abrir o PR.
- Toda mudança em `.github/` exige aprovação do PMO e dos arquitetos (CODEOWNERS).
- Mantenha esta página em dia: o `sdd-check` confere que **todo `.yml` desta pasta é citado aqui**.
