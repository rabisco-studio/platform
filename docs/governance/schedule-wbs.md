# Cronograma e Estrutura Analítica (WBS)

**Versão:** 0.1
**Data:** 2026-11-25
**Status:** Rascunho para aprovação
**Dono:** PMO

**Sem datas por enquanto.** Datas só após DEC-002/DEC-004 e as estimativas dos spikes. A tabela abaixo é a WBS e a ordem dos marcos.

| WBS | Fase | Marco | Saída (gate) | Specs |
|---|---|---|---|---|
| 0 | Fase 0 | Fundações e spikes a–e | Relatórios dos spikes e ADRs resolvidas; baseline-R0 | — (ver `spikes/`) |
| 1 | Fase 1 | Núcleo: cena, formato, operações, render, cor | Gates das specs 001–004 e 015 | 001, 002, 003, 004, 015 |
| 2 | Fase 2 | Pintura raster | Gates 005–008 e 017 | 005, 006, 007, 008, 017 |
| 3 | Fase 3 | Vetor | Gates 009–011 | 009, 010, 011 |
| 4 | Fase 4 | Composição híbrida, I/O, UI desktop → **R1** | Gates 012–014, 016; baseline-R1 | 012, 013, 014, 016 |
| 5 | Fase 5 | Nuvem → **R2** | Gates 018–022 | 018–022 |
| 6 | Fase 6 | Colaboração → **R3** | Gates 023–025 | 023, 024, 025 |
| 7 | Fase 7 | Mobile, web, a11y/i18n → **R4** | Gates 026–028, 036, 037 | 026, 027, 028, 036, 037 |
| 8 | Fase 8 | Pro → **R5** | Gates 029–035 | 029–035 |

## Esforço conhecido (hipótese)
Somente das specs escritas; ver [coverage.md](../requirements/coverage.md) para o total vigente. As demais specs ainda não têm estimativa.

## Regras do cronograma
- Uma fase só inicia após o gate das specs de que depende (ordem das dependências em cada `tasks.md`).
- Spikes não produzem código de produto; produzem decisões (ADRs) e números.
- A ordem de adoção do método: piloto completo na SPEC-001; depois SPEC-002–005 em paralelo.
