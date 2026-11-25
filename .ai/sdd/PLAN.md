# PLAN.md — Roadmap e dependências

**Status:** plan:draft
**Fonte única de specs, fases e releases:** [spec-catalog.csv](../../docs/requirements/spec-catalog.csv) (a tabela abaixo é um resumo; em divergência, vale o catálogo). Cobertura real: [coverage.md](../../docs/requirements/coverage.md). Cronograma/WBS: [schedule-wbs.md](../../docs/governance/schedule-wbs.md).

## Releases e fases

| Release | Nome | Fases | Escopo |
|---|---|---|---|
| R1 | Local Studio | 1–4 | Editor híbrido desktop e offline: cena, formato, undo, render, pincéis, seleção, máscaras, vetor, texto, composição, import/export, UI desktop |
| R2 | Cloud | 5 | Conta, biblioteca, versões, sincronização, backup |
| R3 | Collab | 6 | Compartilhamento, colaboração em tempo real, comentários |
| R4 | Everywhere | 7 | iPadOS, Android, web, responsividade, acessibilidade, i18n |
| R5 | Pro | 8 | Plugins, PSD, CMYK, editor de pincéis, filtros e tipografia avançados |

## Fase 0 — Fundações e spikes (a–e)
Constituição, steering, templates, ADRs e contratos (feito nesta baseline) + cinco spikes. Spikes produzem decisões e números, não código de produto. Planos em [spikes/](../../spikes/README.md).

| Spike | Depende de | Resolve |
|---|---|---|
| a Rust + wgpu | — | ADR-001, ADR-002 |
| b Flutter + wgpu + caneta | a | ADR-003 |
| c Formato `.rbsc` | — | ADR-007 |
| d Pipeline de cor | — | ADR-013 |
| e UI web | a | ADR-004 |

## Specs por fase (resumo do catálogo)

| Fase | Specs |
|---|---|
| 1 | 001 Scene Graph · 002 Formato `.rbsc` · 003 Operações/Undo · 004 Render híbrido · 015 Pipeline de cor |
| 2 | 005 Pincéis · 006 Tiles e memória · 007 Seleção · 008 Máscaras/alfa · 017 Mistura de cores |
| 3 | 009 Paths · 010 Formas/booleanas · 011 Texto vetorial |
| 4 | 012 Composição híbrida · 013 Import/export · 014 Filtros básicos · 016 UI desktop |
| 5 | 018 Identidade · 019 Documentos/versões/quotas · 020 Upload pré-assinado · 021 Protocolo de sync · 022 Fundação do backend |
| 6 | 023 Compartilhamento · 024 Colaboração · 025 Comentários |
| 7 | 026 Mobile · 027 Web · 028 UI responsiva · 036 Painéis personalizáveis · 037 A11y/i18n |
| 8 | 029 Plugins · 030 PSD · 031 CMYK · 032 Editor de pincéis · 033 Filtros avançados · 034 Vetorização · 035 Tipografia avançada |

**Estado:** só as specs 001, 002, 003 e 005 estão escritas, ainda em `requirements:draft`. As demais estão *planejadas*; o produto **não** está totalmente especificado — ver [coverage.md](../../docs/requirements/coverage.md).

## Ordem de adoção do método
1. Piloto completo na SPEC-001 (gates G1–G5).
2. SPEC-002, 003, 004 e 005 em paralelo, após o gate de design da 001.
3. As demais seguem a ordem das fases; cada fase só inicia após os gates de que depende.

## Dependências críticas

```
Spike a ─► ADR-001/002 ─► SPEC-004 (render)
Spike b ─► ADR-003    ─► SPEC-016 (UI desktop)
Spike c ─► ADR-007    ─► SPEC-002 (formato)
Spike d ─► ADR-013    ─► SPEC-015 (cor) ─► SPEC-004
Spike e ─► ADR-004    ─► SPEC-027 (web)

SPEC-001 ─► SPEC-002, SPEC-003 ─► SPEC-005 ─► SPEC-006…008
SPEC-001 ─► SPEC-009…011 ─► SPEC-012 ─► SPEC-013, SPEC-016
```
As dependências detalhadas, no nível de tarefa, estão em cada `tasks.md` e são verificadas contra ciclos pelo `sdd-check`.

## Plataformas e CI

| Plataforma | Build verde no CI | UI completa | Release |
|---|---|---|---|
| Windows | Fase 0 | Fase 4 | R1 |
| macOS | Fase 0 | Fase 4 | R1 |
| Linux | Fase 0 | Fase 4 (melhor esforço, DEC-011) | R1 |
| iPadOS | Fase 0 (cross-compile) | Fase 7 | R4 |
| Android | Fase 0 (cross-compile) | Fase 7 | R4 |
| Web (WASM) | Fase 0 (spikes a/e) | Fase 7 | R4 |
