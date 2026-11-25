# Resumo dos requisitos (requirements-summary)

Roteador de `docs/requirements/`: os catálogos (fonte) e os relatórios gerados. **Uma linha por arquivo.**

**Como manter:** o `sdd-check` exige que todo arquivo desta pasta apareça aqui. Os arquivos marcados como **gerado** nunca são editados à mão (`make docs`).

| Arquivo | Tipo | O que é | Quando consultar |
|---|---|---|---|
| [requirements-catalog.csv](requirements-catalog.csv) | Fonte | Catálogo dos requisitos globais (RF e RNF), com prioridade, release e spec planejada | Para saber o que o produto deve fazer |
| [spec-catalog.csv](spec-catalog.csv) | Fonte | As 37 specs do plano: slug, título, área, fase, release, rigor e estado (planejada ou escrita) | Para criar uma spec nova ou ver o plano |
| [tablet-compatibility.md](tablet-compatibility.md) | Fonte | Matriz de compatibilidade de mesas digitalizadoras e canetas (RNF-03.7): APIs por sistema, o que se verifica e os modelos testados | Ao testar uma mesa ou responder "funciona com a minha mesa?" |
| [coverage.md](coverage.md) | Gerado | Quanto do produto já está especificado, por release e por spec | Para medir o progresso da especificação |
| [traceability.csv](traceability.csv) | Gerado | Rastreabilidade: requisito, spec, FR e tarefas que o cobrem | Para saber de onde um requisito vem e quem o cobre |

Fluxo: o PO edita os catálogos; o `make docs` gera a cobertura e a rastreabilidade; o `sdd-check` confere que tudo bate. A lista de specs com uma linha cada está em [spec-summary.md](../../.ai/sdd/specs/spec-summary.md).
