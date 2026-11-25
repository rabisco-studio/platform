# ADR-010 — Estratégia de colaboração concorrente

**Status:** Proposta
**Origem:** v1 (mantida)
**Data:** 2026-11-24
**Resolvida por:** Spike da Fase 6
**Requisitos relacionados:** RF-09 (colaboração)

## 1. Contexto e problema
Colaboração em tempo real em documentos gráficos é fundamentalmente diferente de texto: raster não aceita merge character-by-character.

## 2. Decisão proposta
- Fase 1–5: single-user com modelo de operações preparado para multi-user.
- Fase 6: colaboração com bloqueio cooperativo por camada raster. Vetores e propriedades por LWW (ADR-009).
- Traços concorrentes na mesma camada raster: avaliados no spike da Fase 6.

## 3. Consequências
Colaboração incremental e segura, sem prometer o que não foi validado.

## 4. Critérios de reavaliação
Resultado do spike da Fase 6.
