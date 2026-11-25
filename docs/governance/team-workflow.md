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

## 7. Automações
O que cada workflow faz, com gatilho, permissões, segredos e o que fazer se falhar: [.github/workflows/README.md](../../.github/workflows/README.md).

Os workflows ficam em [`.github/workflows/`](../../.github/workflows/) e os scripts em [`tools/github/`](../../tools/github/README.md) (só biblioteca padrão do Python 3; testados por `make test-tools`).

| Workflow | Gatilho | O que faz | Segredo necessário | Sem o segredo ou sem permissão |
|---|---|---|---|---|
| `sdd-check` | PR e push na `main` | `make verify`; falha com "rode `make docs` e faça commit" se os gerados estiverem velhos | nenhum | — |
| `labeler` | PR (aberto, atualizado, reaberto) | Aplica labels por pasta (`.github/labeler.yml`) | nenhum (`GITHUB_TOKEN`) | PR de fork: aviso, sem labels |
| `pr-title` | PR (inclui edição do título) | Valida o prefixo: `SPEC-NNN:`, `ADR-NNN:`, `GOV:`, `contracts:`, `feat NNN T-xxx:` ou `feat/NNN-T-xxx` | nenhum | — |
| `gate-check` | PR que altera `.ai/sdd/specs/*/.status` | Transição válida, autor ≠ quem escreveu a spec, cabeçalhos coerentes, template de gate; opcionalmente confere a equipe aprovadora | `ORG_READ_TOKEN` (opcional) | Aviso: a checagem de equipe fica manual; o resto roda |
| `impact-comment` | PR em specs, ADRs, contratos ou catálogos | Comenta (e atualiza) requisitos, specs e dependentes afetados | nenhum (`GITHUB_TOKEN`) | PR de fork: aviso, relatório só no resumo do job |
| `move-card` | Push na `main` que altera um `.status` (o merge do PR) | Move o card da spec para a coluna do novo estado | `PROJECT_TOKEN` | Aviso e imprime o que faria; sucesso |
| `weekly` | Segunda 12:00 UTC e manual | Itens vencidos, relatório semanal (1 issue `status-report` por semana) e cobrança de `bloqueado` | nenhum (`GITHUB_TOKEN`) | Sem permissão: aviso; sucesso |

Todos declaram `permissions:` mínimas, usam `pull_request` (nunca `pull_request_target`), fixam as actions por SHA e passam dados do PR por variáveis de ambiente. Segredos: [github-setup.md](github-setup.md), seção 9.

### Como cada automação decide
- **Label por pasta:** `contracts/` e `docs/architecture/` → `area:platform` + `rigor:anchored`; `core/`, `backend/`, `clients/` → `area:core`, `area:backend`, `area:clients`; `docs/adr/` → `adr`; `.github/`, `tools/`, `Makefile` → `area:platform`; `spikes/` → `spike`; `.ai/sdd/specs/**` não recebe label (a spec define o próprio rigor). Labels nunca são removidos.
- **Título do PR:** os prefixos aceitos são os da seção 3. O erro mostra exemplos válidos.
- **Gate:** (a) `.status` avança no máximo uma etapa em `STAGES` (ou volta, por reabertura); (b) o autor do PR não pode ter escrito `requirements.md`, `design.md` ou `tasks.md` da spec (conferido pelo `git log` da base) e o PR só pode mudar a linha `**Status:**` desses documentos; (c) `sdd_check` verde; (d) corpo com "## Gate" e "## Registro da revisão" (template `gate.md`). O autor é reconhecido pelo login, pelo nome ou pelo e-mail do commit (inclusive o e-mail `noreply` do GitHub); para outros e-mails da mesma pessoa, defina `GATE_AUTHOR_ALIASES` no workflow. **Não é gate:** spec nova (criada por `make new-spec`, em `requirements:draft`), pasta renomeada sem mudança de estágio e `.status` apagado; nesses casos só a transição é validada, sem exigir o template de gate nem checar a autoria.
- **Equipe aprovadora (opcional):** G1 `product` ou `tech-leads`; G2 `architects`; G3 `tech-leads`; G4 `tech-leads` ou `qa`; G5 `product`. Só é checada com `ORG_READ_TOKEN`.
- **Impacto:** lista requisitos pelo `traceability.csv` e specs dependentes (transitivamente) pelas dependências dos `tasks.md`; ADRs e contratos alterados apontam para as specs que os citam.
- **Card:** a coluna vem da tabela do [README](../../README.md), seção 7. Dispara no push à `main` (resultado do merge) e não em `pull_request`, para o segredo nunca chegar a código de PR.
- **Semanal:** "vencido" é prazo em data ISO (AAAA-MM-DD) anterior a hoje; "sem data" é item aberto sem data ISO. A issue da semana tem o título "Relatório de status — semana de <segunda-feira>" e não é duplicada. A cobrança de `bloqueado` comenta uma vez a cada 7 dias, marcando o responsável.

### Limites conhecidos
- Os checks de título e de gate rodam o código do próprio PR (evento `pull_request`). Isso é seguro (sem segredos de escrita), mas um PR que altere o script poderia afrouxar o próprio check. Mudanças em `tools/` e `.github/` exigem aprovação do PMO e dos arquitetos (CODEOWNERS).
- O nome do quadro no GitHub hoje é "Rabisco Studio" (projeto nº 1); o `move_card.py` aceita esse nome e "Rabisco Platform", ou a variável `PROJECT_NUMBER`.
- Os checks `gate-check`, `pr-title` e `impact-comment` **não são obrigatórios** na regra da `main` (só `verify`). Torná-los obrigatórios é decisão de governança e exige PR no ruleset.

## 8. Automações da Camada 3
Estas automações **criam coisas** (specs, issues, releases, site); por isso o padrão é o modo ensaio ou a ação explícita do humano.

| Automação | Gatilho | O que faz | Flag para aplicar | Se der errado |
|---|---|---|---|---|
| `make new-spec N=018` (`tools/sdd/new_spec.py`) | Manual | Cria `.ai/sdd/specs/NNN-slug/` com os 3 templates (cabeçalhos do catálogo), `.status` em `requirements:draft`, marca a spec como "escrita" no catálogo e roda o gerador | Nenhuma: cria na hora; recusa spec inexistente, já escrita ou com pasta existente, sem alterar nada | Apague a pasta e restaure `spec-catalog.csv` (`git checkout -- docs/requirements/spec-catalog.csv`); rode `make docs` |
| `tools/github/tasks_to_issues.py NNN` | Manual | Gera as issues de tarefa a partir do `tasks.md`; só com `.status` em `tasks:approved` ou posterior; marcador oculto evita duplicar | `--apply` (o padrão é ENSAIO) | Rodar de novo não duplica. Issue criada por engano: feche e apague pela interface. Falta milestone: `setup-labels-milestones.py --apply` |
| `baseline-release` (`baseline_notes.py`) | Push de tag `baseline-R<n>-v<n>` | Valida a tag, roda `make strict`, monta as notas pelo template e cria um GitHub Release **pre-release** | A própria tag é a ação (só o PMO a cria, depois do `make strict`) | Tag inválida ou `make strict` falho: o workflow para sem criar release. Para refazer: `gh release delete TAG` e `git push --delete origin TAG`, corrija e crie a tag de novo |
| `pages` (`tools/sdd/build_site.py`) | Push na `main` e manual | Gera e publica a página de pré-visualização no GitHub Pages | Variável `PAGES_ENABLED=true` e Pages com Source "GitHub Actions" (github-setup.md, seção 10) | Sem a variável, só avisa. Com o Pages desabilitado, o deploy falha: habilite o Pages ou ponha `PAGES_ENABLED=false` |
| `code-ci` (`check_crate_deps.py`) | PR e push na `main` | Sem código: termina com sucesso ("sem código ainda"). Com `core/Cargo.toml`: `cargo fmt --check`, `clippy -D warnings`, `test` e as arestas de `crates.toml` | Automático | Falha de aresta: ajuste a dependência ou, se a mudança for de arquitetura, abra PR em `crates.toml` (aprovação dos arquitetos) |

### Detalhes
- **`make new-spec`:** o `Depende de` e as `Tags` ficam para o autor preencher (o catálogo não os traz); os blocos de exemplo dos templates (FR-001, T-001...) são removidos para o esqueleto já passar no `sdd-check`. O esqueleto de design e de tarefas leva "rascunho antecipado; não vinculante".
- **Issues de tarefa:** título `[SPEC-NNN T-NNN] <título>`; labels `task`, `area:*` (a área `contracts` usa `area:platform`) e `rigor:*`; milestone do release. O corpo segue o formulário `task.yml`. A estimativa é arredondada para cima e precisa estar entre 1 e 4 h. Tarefas marcadas "Removida" no título são ignoradas.
- **Baseline:** o workflow não cria a tag; o PMO a cria. As notas trazem o escopo (do `INDEX.md`), a cobertura (do `coverage.md`), decisões abertas, riscos com exposição 12 ou mais e os commits desde a baseline anterior. **O pre-release não substitui a aprovação humana**: PO e arquiteto-chefe assinam antes de desmarcar "pre-release". Tags não são protegidas pelo ruleset da `main`: quem tem escrita pode criar `baseline-*` e disparar o workflow.
- **Site:** uma página só, sem JavaScript. Os dados vêm dos mesmos arquivos do repositório; ela não é fonte de verdade. O repositório é público, então o site também é.
- **CI de código:** `backend/` e `clients/` só têm jobs esqueleto comentados (TODO: SPEC-022 e SPEC-016). Para o core, o verificador falha se um crate declarar dependência interna fora das arestas de `docs/architecture/crates.toml` ou dependência de UI, backend ou nuvem (P-01).
