# Spike (a) — Rust + wgpu em desktop e web

**Hipótese:** O mesmo core Rust com wgpu renderiza conteúdo raster e vetor em desktop (Metal/Vulkan/DX12) e em web (WebGPU, fallback WebGL2).

**Duração estimada:** 2 semanas

## Objetivos
1. Renderizar um canvas 4096×4096 com 30 camadas RGBA8 (R-A) a 60 fps em desktop.
2. Renderizar o mesmo cenário em WASM + WebGPU em pelo menos 2 navegadores.
3. Medir frame time, latência de input (mouse) e consumo de memória.
4. Executar compute shader WGSL para stamping de dabs.

## Critérios de Aprovação
- Frame time p95 ≤ 16,6 ms em R-A no desktop de referência.
- WebGPU funciona em Chrome e Firefox (versões atuais).
- Compute shader executa sem erro em desktop e web.

## Se reprovar
- Web com backend WebGL2 reduzido (sem compute shaders → fragment shader fallback).
- Ou render alternativo (Skia para web, wgpu para desktop).

## Entregáveis
- Binário desktop + página web com o cenário de teste.
- Relatório com números: frame time, latência, memória, tamanho do WASM bundle.
- Recomendação fundamentada para ADR-001 e ADR-002.

## Escopo negativo
- Sem UI completa (apenas canvas com pan/zoom).
- Sem persistência.
- Sem pincéis reais (apenas dabs sintéticos).
