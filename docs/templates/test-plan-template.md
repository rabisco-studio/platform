# Plano de testes — SPEC-NNN <slug>

**Versão:** 0.1
**Data:** AAAA-MM-DD
**Status:** Rascunho
**Dono:** <QA ou tech lead>

## 1. Escopo
Requisitos cobertos: <FR e NFR da spec>. Fora de escopo: <itens>.

## 2. Estratégia por tag de verificação
| Tag | Como testar | Ferramenta | Onde roda |
|---|---|---|---|
| BEH | testes automatizados de comportamento | | CI |
| VIS | comparação com imagens de referência (golden) com tolerância | | tests/graphics |
| PERF | benchmark no hardware de referência | | tests/performance |
| CONF | conformance suite contra contracts/ | | tests/integration |

## 3. Casos de teste
| ID | Requisito | Tipo | Pré-condição | Passos | Resultado esperado |
|---|---|---|---|---|---|
| TC-001 | FR-001 | BEH | | | |

## 4. Dados e referências
Documentos de referência (R-A, R-B), corpus de compatibilidade, imagens golden: <caminhos>.

## 5. Critérios de saída
- Todos os casos Must passam.
- Metas de desempenho atingidas em <hardware de referência>.
- Sem defeito aberto de severidade alta.

## 6. Rastreabilidade
| Requisito | Casos |
|---|---|
| | |
