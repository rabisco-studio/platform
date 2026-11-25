# ADR-013 — Pipeline de cor

**Status:** Proposta
**Origem:** Nova na v2
**Data:** 2026-11-24
**Resolvida por:** Spike (d)
**Requisitos relacionados:** RF-02.3 (perfil de cores), RF-07 (exportação)

## 1. Contexto e problema
O pipeline de cor afeta formato de pixel, shaders, exportação e a promessa de gerenciamento de cores para profissionais. Precisa ser definido antes dos pincéis e filtros.

## 2. Decisão proposta
- Cada documento declara um **espaço de trabalho** com perfil ICC embutido. Padrão: sRGB. Opção: Display P3.
- Pixels raster em RGBA com **alfa pré-multiplicado**. Profundidade por documento: 8 ou 16 bits por canal.
- Hipótese: 16 bits no desktop, 8 bits em mobile e web — a confirmar por medição.
- Referência de custo: camada 4096×4096 = 64 MiB (8 bits) ou 128 MiB (16 bits).
- Espaço de mesclagem configurável: perceptual (padrão) ou linear.
- Exibição: composição no espaço de trabalho → shader de conversão para o perfil do monitor.
- Exportação: conversão para perfil de destino com ICC embutido.
- CMYK: fora do início (Fase 8).
- Biblioteca de cor: avaliar lcms2 (bindings) vs. alternativas Rust puro para WASM e iOS.

## 3. Critérios de aceitação
- AC-1: imagem sRGB 8 bits importada/exportada sem edição = idêntica bit a bit.
- AC-2: imagem Display P3 exportada para sRGB com ΔE00 ≤ 1 no gamut.
- AC-3: mesma composição em duas GPUs respeita tolerância visual.
- AC-4: ao reabrir, documento mantém perfil, profundidade e espaço de mesclagem.

## 4. Consequências
- Positivas: formato de pixel definido antes de pincéis/filtros.
- Negativas: custo de memória do 16 bits, shader adicional de conversão.

## 5. Critérios de reavaliação
Se 16 bits não couber no iPad de referência. Se AC-2 não for atingível com a biblioteca escolhida.
