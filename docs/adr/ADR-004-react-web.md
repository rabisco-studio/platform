# ADR-004 — React + WebAssembly para web

**Status:** Proposta
**Origem:** v1 (mantida)
**Condição:** só segue para aprovação se o spike (e) reprovar o Flutter web; caso contrário, a ADR é rejeitada.
**Data:** 2026-11-24
**Resolvida por:** Spike (e)
**Requisitos relacionados:** RNF-03.3 (web)

## 1. Contexto e problema

A web entra no R4. A decisão entre Flutter web e React + WASM depende do spike (e).

## 2. Requisitos e restrições

- Tamanho do bundle inicial razoável.
- TTI competitivo.
- Acessibilidade (teclado, screen readers).
- Core Rust via WebAssembly.

## 3. Alternativas consideradas

### Alternativa A — React + TypeScript + WebAssembly
- Ecossistema web maduro. SSR e acessibilidade nativos.
- Desvantagem: UI duplicada em relação ao Flutter.

### Alternativa B — Flutter web
- UI única para todas as plataformas.
- Desvantagem: bundle pesado, acessibilidade limitada, entrada por teclado inconsistente.

## 4. Decisão proposta

Condicional ao spike (e): se Flutter web atender aos critérios, adota-se UI única. Caso contrário, React sobre WebAssembly.

## 5. Justificativas

A web só entra no R4. Até lá, a decisão pode esperar por evidências.

## 6. Consequências

React: duplicação de UI, mas melhor acessibilidade e tamanho. Flutter web: UI única, mas riscos de bundle e acessibilidade.

## 7. Critérios de reavaliação

Resultado do spike (e) com critérios definidos antes do teste.

## 8. Referências

- Spike (e): `spikes/spike-e-web-ui/`
