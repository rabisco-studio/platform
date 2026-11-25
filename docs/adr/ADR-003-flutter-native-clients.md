# ADR-003 — Flutter para clientes nativos

**Status:** Proposta
**Origem:** v1 (mantida)
**Data:** 2026-11-24
**Resolvida por:** Spike (b)
**Requisitos relacionados:** RF-10 (interface), RNF-03 (multiplataforma)

## 1. Contexto e problema

Precisamos de UI nativa para desktop (Windows, macOS) e mobile (iOS, Android) sobre o core Rust. Manter UIs nativas separadas por plataforma multiplica o esforço.

## 2. Requisitos e restrições

- UIs finas: a lógica vive no core Rust.
- Integração GPU: o core renderiza via wgpu, a UI exibe a textura.
- Latência de caneta: sobrecarga p95 ≤ 8 ms sobre a linha de base nativa.

## 3. Alternativas consideradas

### Alternativa A — Flutter
- Um código para desktop e mobile. Ecossistema maduro. flutter_rust_bridge para FFI.
- Risco: integração de textura GPU e latência de caneta.

### Alternativa B — UI nativa por plataforma (SwiftUI, Jetpack Compose, Win32)
- Melhor integração nativa.
- Desvantagem: multiplicação de código de UI.

### Alternativa C — Qt (C++)
- Maduro para desktop.
- Desvantagem: mobile limitado, licença complexa, não é Rust.

## 4. Decisão proposta

Flutter para clientes nativos, condicionada ao spike (b). Três caminhos de integração GPU a testar: textura compartilhada, PlatformView e shell nativo puro.

## 5. Justificativas

Um código de UI para quatro plataformas. Se a latência de caneta não atender, o fallback é shell nativo com Flutter apenas nos painéis.

## 6. Consequências

### Positivas
- Redução drástica de código de UI duplicado.
- Ecossistema rico de widgets e theming.

### Negativas
- Risco de latência na ponte Flutter ↔ wgpu.
- Dependência do Google para o framework.

## 7. Critérios de reavaliação

- Se o spike (b) mostrar sobrecarga > 8 ms.
- Se flutter_rust_bridge não suportar o throughput de eventos necessário.

## 8. Referências

- Spike (b): `spikes/spike-b-flutter-wgpu-pen/`
- flutter_rust_bridge: https://github.com/aspect-build/aspect
