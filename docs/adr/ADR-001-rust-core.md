# ADR-001 — Rust como linguagem do core

**Status:** Proposta
**Origem:** v1 (mantida)
**Data:** 2026-11-24
**Resolvida por:** Spike (a)
**Requisitos relacionados:** RNF-03 (multiplataforma), RNF-07 (manutenibilidade)

## 1. Contexto e problema

O motor gráfico precisa rodar em seis alvos (Windows, macOS, Linux, iOS, Android, web via WASM) com desempenho previsível, segurança de memória em código de manipulação de tiles e pincéis, e sem garbage collector que cause pausas durante a pintura.

## 2. Requisitos e restrições

- P-01: core independente de UI, backend e nuvem.
- Compilação para todas as plataformas-alvo, incluindo WebAssembly.
- FFI com Dart (Flutter) e JavaScript (web).
- Ecossistema de bibliotecas para geometria, GPU e serialização.

## 3. Alternativas consideradas

### Alternativa A — Rust
- Segurança de memória sem GC. Compilação nativa e WASM. Ecossistema wgpu, serde, SQLite.
- Desvantagem: curva de aprendizagem, menor pool de desenvolvedores.

### Alternativa B — C++
- Maduro, amplo ecossistema gráfico (Skia, Qt).
- Desvantagem: segurança de memória manual, tooling de build complexo, WASM menos ergonômico.

### Alternativa C — Kotlin Multiplatform
- Produtividade alta, interoperabilidade com JVM.
- Desvantagem: GC em hot paths gráficos, suporte a WASM e GPU menos maduro.

## 4. Decisão proposta

Rust como linguagem do core e de todos os engines (raster, vetor, scene, render, brush, history, file, sync).

## 5. Justificativas

- Zero-cost abstractions e ausência de GC em hot paths (pintura, composição, tiles).
- Target triplo: nativo, WASM e FFI com Dart e JS.
- wgpu e wgsl cobrem a abstração de GPU multiplataforma.
- Verificação de dependências do core no CI reforça P-01.

## 6. Consequências

### Positivas
- Um único core para todos os alvos.
- Segurança de memória verificada pelo compilador.
- Desempenho previsível sem pausas de GC.

### Negativas
- Curva de aprendizagem para desenvolvedores sem experiência em Rust.
- Tempo de compilação mais longo.
- Pool de desenvolvedores menor que C++ ou Java.

### Riscos residuais
- Bridges Rust↔Dart e Rust↔WASM podem adicionar overhead. Medido no spike (a) e (b).

## 7. Critérios de reavaliação

- Se o spike (a) mostrar que wgpu+WASM não atende ao frame time p95 ≤ 16,6 ms em R-A.
- Se a bridge para Dart inviabilizar a latência de caneta (spike b).
- Se o ecossistema de bibliotecas necessárias não estiver disponível ou mudar de licença.

## 8. Referências

- Spike (a): `spikes/spike-a-rust-wgpu/`
- wgpu: https://wgpu.rs/
- Rust: https://www.rust-lang.org/
