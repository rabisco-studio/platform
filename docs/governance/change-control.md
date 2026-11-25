# Controle de Mudanças

**Versão:** 0.1
**Data:** 2026-11-25
**Status:** Rascunho para aprovação
**Dono:** PMO

## 1. Princípio
Documento **aprovado** é congelado. Mudar exige Change Request (CR) aprovada e **reabre o portão** (Regra 6 do SDD): o `.status` volta ao estágio anterior e tudo o que depende do documento é reavaliado.

## 2. Classes de mudança
| Classe | Exemplo | Aprovação | Reabre gate? |
|---|---|---|---|
| C0 Editorial | typo, link, formatação | Revisor | não |
| C1 Esclarecimento | reescrever sem mudar o sentido | TL | não (registrar) |
| C2 Requisito/design | novo FR, mudar critério | TL + ARQ (+PO se requisito) | **sim** |
| C3 Contrato/arquitetura | `contracts/`, `crates.toml`, ADR | ARQ + TLs afetados | **sim**, em todas as specs dependentes |
| C4 Escopo/cronograma | mover requisito de release | PO | sim + replanejamento |

## 3. Fluxo
1. Abrir issue "Change Request" (`.github/ISSUE_TEMPLATE/change-request.yml`; convenções em [issue-conventions](issue-conventions.md)).
2. PMO classifica (C0–C4) e analisa o impacto com [traceability.csv](../requirements/traceability.csv) e o grafo de dependências das specs.
3. Aprovadores da classe decidem; C2+ vai para o [decision-log](decision-log.md).
4. PR com a mudança, histórico atualizado e `.status` reaberto quando aplicável.
5. `make verify` verde; CODEOWNERS aprova; merge.

## 4. Baseline
Ao fim de cada gate de release o PMO cria a tag `baseline-<release>-vN`. Mudar depois da tag segue este fluxo sem exceção.
