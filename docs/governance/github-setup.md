# Guia de Configuração do GitHub (15 minutos)

**Versão:** 0.1
**Data:** 2026-11-25
**Status:** Rascunho para aprovação
**Dono:** PMO

Executar uma vez, por quem for administrador da organização, **antes** de convidar a equipe. Pré-requisito: DEC-002 (pessoas e papéis) e DEC-003 (licença/visibilidade) decididas.

## 1. Repositório (2 min)
1. Criar o repositório `rabisco-studio/platform`. **Visibilidade: pública** (decidido; ver [DEC-003](decision-log.md)). Público significa que *qualquer pessoa* na internet pode ler, clonar e fazer fork; o convite à organização controla só quem escreve e aprova. Antes de publicar: nenhum segredo ou dado pessoal no repositório e revisão de [riscos](risk-register.md) e [decisões](decision-log.md) para conteúdo sensível. Na organização, exigir **autenticação em dois fatores** de todos os membros (Settings → Authentication security).
2. Enviar o conteúdo do ZIP para a branch `main` (primeiro commit direto; depois disso a proteção do passo 3 vale).
3. Settings → General → Pull Requests: marcar *Allow squash merging* e desmarcar os outros dois; marcar *Automatically delete head branches*.

## 2. Equipes (3 min)
Organização → Teams. Criar exatamente os nomes usados no [CODEOWNERS](../../.github/CODEOWNERS) e dar acesso *Write* ao repositório:

| Equipe | Quem |
|---|---|
| `architects` | Arquiteto-chefe e arquitetos (mín. 2) |
| `tech-leads` | Tech leads de core, backend e clients |
| `product` | PO e analistas de requisitos |
| `pmo` | Gestão do projeto |
| `core-leads`, `backend-leads`, `client-leads` | Leads por área (usadas após o gate G3) |
| `qa` | Qualidade |

Os nomes das equipes em `CODEOWNERS` já usam a organização `rabisco-studio` (`@rabisco-studio/architects` etc.).

## 3. Proteção da `main` (4 min)
A regra está versionada em [`.github/rulesets/main-protection.json`](../../.github/rulesets/main-protection.json).

**Ordem obrigatória:** (1) fazer o primeiro push direto na `main`; (2) esperar o workflow `sdd-check` rodar uma vez (aba *Actions*); (3) só então criar a regra. O check `verify` só existe na lista depois da primeira execução.

**Caminho rápido (importar):** repositório → Settings → Rules → Rulesets → New ruleset → **Import a ruleset** → escolher o arquivo JSON → conferir → Create. Se o GitHub recusar algum campo, use o caminho manual abaixo.

**Caminho manual:** repositório → Settings → Rules → Rulesets → New ruleset → New branch ruleset. (Use o ruleset **do repositório**, não o da organização: os da organização só são aplicados no plano Team.)

| Campo | Valor |
|---|---|
| Ruleset Name | `main-protection` |
| Enforcement status | Active |
| Bypass list | vazia (ninguém, nem administradores) |
| Target branches | Add target → *Include default branch* |
| Restrict deletions | ☑ |
| Block force pushes | ☑ |
| Require linear history | ☑ (combina com merge por squash) |
| Require a pull request before merging | ☑, com: aprovações = **1**; *Dismiss stale approvals*; **Require review from Code Owners**; **Require approval of the most recent reviewable push**; *Require conversation resolution*; método de merge: só *Squash* |
| Require status checks to pass | ☑, com *Require branches to be up to date* e o check **`verify`** |
| Demais regras (signed commits, code scanning, coverage, Copilot…) | desmarcadas |

**Sem bypass para ninguém:** o administrador também passa pelo PR. Isso é o que garante que autor ≠ aprovador. Se a equipe for de 1 pessoa no início, a regra de aprovação trava os merges; nesse caso, reduza temporariamente para 0 aprovações e registre a exceção no [decision-log](decision-log.md), religando assim que houver um segundo aprovador.

## 4. Quadro do projeto (5 min)
Projects → New project → **Board** → nome **"Rabisco Platform"**. Vincular ao repositório `platform`.

### 4.1 Colunas (campo *Status*), na ordem
Um card representa **uma spec** (não uma tarefa) e fica na coluna da fase **em que o trabalho está agora**. Ele só avança junto com o PR que altera o `.status` da spec (ver [fluxo da equipe](team-workflow.md)). As colunas seguem o pipeline `IDEA → REQUIREMENTS → DESIGN → TASKS → IMPLEMENTATION → REVIEW`.

| # | Coluna | O que significa | `.status` correspondente | Sai da coluna quando | Quem move |
|---|---|---|---|---|---|
| 1 | **Ideia** | Spec planejada no catálogo, ainda sem pasta nem dono. Entra aqui por padrão. | (sem pasta; `estado = planejada`) | Há um dono e a pasta `NNN-slug` é criada com `requirements:draft` | PMO |
| 2 | **Requisitos** | Dono escrevendo ou revisando `requirements.md` (EARS, `Cobre:`, sem Q aberta). | `requirements:draft` | **G1 aprovado**: PR muda o `.status` para `requirements:approved` | Aprovador do G1 (PO + TL, ≠ autor) |
| 3 | **Design** | Escrevendo `design.md`: cada FR mapeado, contratos e ADRs citados. | `requirements:approved`, `design:draft` | **G2 aprovado**: `design:approved` | Arquiteto |
| 4 | **Tarefas** | Escrevendo `tasks.md`: tarefas de 1 a 4 h, todo FR coberto, dependências acíclicas. | `design:approved`, `tasks:draft` | **G3 aprovado**: `tasks:approved`. Agora criam-se as issues de tarefa. | Tech lead |
| 5 | **Implementação** | Código e testes em andamento; as issues `T-xxx` estão abertas. | `tasks:approved`, `implementation:in-progress` | Todas as tarefas concluídas e testes verdes: **G4** (`implementation:done`) | TL + QA |
| 6 | **Revisão** | Verificando critérios de aceite, conformance e rastreabilidade final. | `implementation:done` | **G5 aprovado**: `review:done` | PO |
| 7 | **Feito** | Spec concluída e congelada. Mudar exige Change Request e reabre o portão. | `review:done` | (reabre apenas por CR classe C2 ou maior) | PO |

**Regras do quadro**
- Um estado `*:draft` **nunca** move o card para a coluna seguinte; só a aprovação humana (PR do `.status`).
- Se um gate for reaberto por Change Request, o card **volta** para a coluna da fase reaberta.
- Limite sugerido: no máximo 3 specs por pessoa em *Requisitos* ou *Design* ao mesmo tempo.

### 4.2 Campos extras (Settings do projeto → *New field*)
| Campo | Tipo | Valores | Para quê |
|---|---|---|---|
| **Spec** | Texto | `SPEC-001` a `SPEC-037` | Liga o card ao catálogo (`docs/requirements/spec-catalog.csv`) |
| **Release** | Opção única | R1, R2, R3, R4, R5 | Agrupar e filtrar por release; reflete o milestone |
| **Fase** | Opção única | 1 a 8 | Ordem do cronograma (`schedule-wbs.md`) |
| **Rigor** | Opção única | anchored, spec-first | Define o nível de formalidade (anchored = contratos, formato, sync, segurança) |
| **Dono** | Pessoa (Assignee) | membro da organização | Responsável por escrever a spec. Autor ≠ aprovador |

### 4.3 Automações embutidas (Workflows do projeto)
**Só podem ser configuradas na interface:** a API do GitHub não expõe os workflows embutidos de um Project, então nenhum script do repositório as ativa. Quem for administrador da organização faz isto uma vez, no quadro **"Rabisco Platform"**.

Caminho comum: organização `rabisco-studio` → **Projects** → **Rabisco Platform** → menu **⋯** (canto superior direito) → **Settings** → **Workflows** (barra lateral esquerda). Clique no workflow, ajuste e use **Save and turn on workflow**.

- [ ] **Item added to project** — Workflows → *Item added to project* → em *Set*, escolha **Status = Ideia** → *Save and turn on workflow*. Todo card ou issue novo entra em Ideia.
- [ ] **Item closed** — Workflows → *Item closed* → *Set* **Status = Feito** → *Save and turn on workflow*. Atenção: vale para todo item fechado, inclusive issues de pergunta e defeito.
- [ ] **Pull request merged** — Workflows → *Pull request merged* → *Set* **Status = Feito**. Restrinja o filtro do workflow aos itens de **tarefa** (label `task`), se a interface oferecer o filtro; confira o escopo na tela antes de salvar. → *Save and turn on workflow*.
- [ ] **Auto-add to project** — Workflows → *Auto-add to project* → **Edit** → *Repository*: `rabisco-studio/platform` → filtro `is:issue,pr is:open` (issues e PRs novos) → **Save** → *Turn on workflow*. Combinado com o primeiro item, tudo que for aberto no repositório aparece em Ideia.

Já existente neste guia e mantido: *Item reopened* → **Status = Requisitos** (a reabertura obriga a revisitar os requisitos; ajuste depois para a fase correta).

Depois de ativar, confira em *Workflows* que os quatro aparecem com o indicador de ativo. O estado atual **não está registrado aqui**: este checklist descreve o que fazer, não o que já foi feito.

### 4.4 Carga inicial
Criar 1 card por spec do [catálogo](../requirements/spec-catalog.csv) (37). As 4 já escritas (001, 002, 003 e 005) entram direto em **Requisitos**; as outras 33 ficam em **Ideia**. Preencher Spec, Release, Fase e Rigor conforme o catálogo.

### 4.5 Visões úteis (Views)
- **Por release:** tabela agrupada por *Release*, ordenada por *Fase*.
- **Meus cards:** filtro `assignee:@me`.
- **Gates pendentes:** filtro nas colunas Requisitos, Design e Tarefas com label `gate`.

## 5. Milestones e labels (2 min)
- Milestones: `Fase 0 Spikes`, `R1 Local Studio`, `R2 Cloud`, `R3 Collab`, `R4 Everywhere`, `R5 Pro` (sem data de entrega).
- Labels: `task`, `gate`, `spike`, `question`, `defect`, `change-request`, `adr`, `area:core`, `area:backend`, `area:clients`, `area:platform`, `rigor:anchored`, `rigor:spec-first`, `bloqueado` (detalhes em [issue-conventions](issue-conventions.md)). Os formulários de issue usam esses labels; crie-os antes de abrir a primeira issue.

### 5.1 Criar tudo por script
Em vez de criar à mão, rode [`tools/github/setup-labels-milestones.py`](../../tools/github/setup-labels-milestones.py). Requer Python 3 e a CLI `gh` autenticada (`gh auth login`) por uma conta com permissão de triagem ou escrita no repositório.

```bash
python3 tools/github/setup-labels-milestones.py            # ENSAIO (padrão): só lê e mostra o plano
python3 tools/github/setup-labels-milestones.py --apply    # executa
python3 tools/github/setup-labels-milestones.py --repo ORG/REPO
```

- O **ensaio** lista o que seria criado (`+`), atualizado (`~`) e ignorado (`=`), sem escrever nada.
- É **idempotente**: o que já está igual é ignorado; descrição ou cor diferentes são **atualizadas** e relatadas. **Nunca apaga** nada (labels e milestones fora da lista só são contados).
- Sai com código **3** se faltar permissão (e **2** se o `gh` faltar ou não estiver autenticado).
- Depois do `--apply`, rode o ensaio de novo: deve mostrar **0 mudanças**.

## 6. Convite e primeiro uso (1 min)
1. Convidar as pessoas **pelas equipes**, nunca individualmente.
2. Cada pessoa roda `make verify` uma vez para confirmar o ambiente (só Python 3).
3. Primeira tarefa de todos: ler o [fluxo da equipe](team-workflow.md) e o [README](../../README.md).

## 7. Rotina
| Quando | Quem | O quê |
|---|---|---|
| Toda mudança | Autor | Branch `spec/NNN-slug/assunto` → PR com o template → `make verify` verde |
| Gate | Aprovador ≠ autor | PR que altera o `.status`; mover o card de coluna |
| Mudança em documento aprovado | PMO | Change Request (issue) antes do PR |
| Fim de release | PMO | Tag `baseline-<release>-vN` |
| Semanal | PMO | Revisar [riscos](risk-register.md) e [decisões abertas](decision-log.md) |

## 8. Verificação final
Abrir um PR de teste que altere um arquivo gerado à mão: o CI deve falhar. Abrir outro, de uma conta sem acesso de Code Owner à pasta: o merge deve ficar bloqueado. Se ambos acontecerem, a configuração está correta.
