# ADR-002 — wgpu para renderização

**Status:** Proposta
**Origem:** v1 (mantida)
**Data:** 2026-11-24
**Resolvida por:** Spike (a)
**Requisitos relacionados:** RNF-01 (desempenho)

## 1. Contexto e problema

O motor precisa de uma abstração de GPU que funcione em Metal (macOS/iOS), Vulkan (Windows/Linux/Android), DX12 (Windows) e WebGPU (web), sem manter backends separados.

## 2. Requisitos e restrições

- 60 fps sustentados em R-A (frame time p95 ≤ 16,6 ms).
- Suporte a WebGPU no navegador.
- Shaders em linguagem única (WGSL).

## 3. Alternativas consideradas

### Alternativa A — wgpu + WGSL
- Abstração Rust nativa sobre todos os backends. Mesmo código para nativo e web.
- Desvantagem: projeto em evolução rápida, possíveis breaking changes.

### Alternativa B — Skia (via skia-safe)
- Motor maduro e testado (usado pelo Flutter e Chrome).
- Desvantagem: binding Rust menos ergonômico, controle limitado sobre pipeline de shaders, build complexo.

### Alternativa C — Vulkan/Metal direto
- Controle total.
- Desvantagem: duplicação de código por backend, sem suporte direto a WebGPU.

## 4. Decisão proposta

wgpu como abstração de renderização, com shaders em WGSL.

## 5. Justificativas

Cobertura de todos os backends com um único código Rust. WGSL como linguagem de shader única. Integração natural com o ecossistema Rust.

## 6. Consequências

### Positivas
- Um pipeline de rendering para todas as plataformas.
- Shaders em WGSL versionados e testados.

### Negativas
- Dependência de um projeto em evolução.
- WebGPU ainda não é universal; fallback WebGL2 necessário.

## 7. Critérios de reavaliação

- Se wgpu não atingir o frame time alvo no spike (a).
- Se WebGPU não avançar em adoção de navegadores até o R4.

## 8. Referências

- wgpu: https://wgpu.rs/
- WebGPU: https://www.w3.org/TR/webgpu/
