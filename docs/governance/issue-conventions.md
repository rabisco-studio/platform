# Convenções de Issues, Labels e Quadro

**Versão:** 0.1
**Data:** 2026-11-25
**Status:** Rascunho para aprovação
**Dono:** PMO

Issues não substituem os documentos: **a spec é a fonte da verdade**; a issue só rastreia o trabalho e aponta para ela pelo ID. Issues em branco estão desativadas; use um dos formulários em [`.github/ISSUE_TEMPLATE/`](../../.github/ISSUE_TEMPLATE/).

## 1. Qual formulário usar
| Situação | Formulário | Prefixo do título | Label | Quem abre |
|---|---|---|---|---|
| Mudar algo já aprovado, contrato ou arquitetura | Change Request | `[CR]` | `change-request` | Qualquer pessoa; o PMO classifica (C0–C4) |
| Pedir aprovação de um portão G1–G5 | Pedido de aprovação de gate | `[SPEC-NNN] G?:` | `gate` | Dono da spec |
| Trabalho de implementação (só após G3) | Tarefa | `[SPEC-NNN T-NNN]` | `task` | Tech lead, copiando do `tasks.md` |
| Experimento da Fase 0 | Spike | `[SPIKE-x]` | `spike` | Arquiteto |
| Pergunta que bloqueia um gate ou decisão pendente | Pergunta aberta | `[Q]` | `question` | Qualquer pessoa |
| Erro em documento, contrato ou código | Defeito | `[BUG]` | `defect` | Qualquer pessoa |

## 2. Regras
1. **Uma issue, um assunto, um dono** (assignee).
2. **Issue de tarefa só depois do gate G3.** Antes disso as tarefas podem mudar; criar issues cedo gera retrabalho.
3. A issue **copia** o ID e o checklist do `tasks.md`, mas **não altera escopo**. Mudou o escopo → Change Request e gate reaberto.
4. Todo PR referencia sua issue (`Closes #n`) e usa o [template de PR](../../.github/pull_request_template.md).
5. Todo item aberto (pergunta ou decisão) tem **padrão recomendado e prazo**; vencido o prazo vale o padrão, registrado no [decision-log](decision-log.md).
6. Decisões C2 ou maiores vão para o decision-log; a issue só aponta para ele.

## 3. Labels
| Grupo | Labels |
|---|---|
| Tipo | `task`, `gate`, `spike`, `question`, `defect`, `change-request`, `adr` |
| Área | `area:core`, `area:backend`, `area:clients`, `area:platform` |
| Rigor | `rigor:anchored`, `rigor:spec-first` |
| Estado | `bloqueado` |

Release é um **milestone** (`R1 Local Studio` … `R5 Pro`, `Fase 0 Spikes`), não um label. A spec é um campo do quadro (ex.: `SPEC-001`).

## 4. Quadro e ciclo de vida
Colunas: `Ideia → Requisitos → Design → Tarefas → Implementação → Revisão → Feito`.
- O **card de uma spec** muda de coluna junto com o PR que altera o `.status` (um gate aprovado = card avança).
- Issues de **tarefa** ficam na coluna da spec; fecham quando o PR é mesclado e a verificação do `tasks.md` foi cumprida.
- Issue `bloqueado` deve citar o bloqueio (outra issue, Q- ou DEC-) e o responsável por destravar.

## 5. Exemplo de título
`[SPEC-001 T-004] DocumentMeta e perfil de cor` · `[SPEC-002] G1: pedido de aprovação` · `[CR] Mover RF-03.9 do R1 para o R2` · `[Q] SPEC-001 Q-005: modelo de mesclagem`
