# Spike (d) — Pipeline de cor e 16 bits

**Hipótese:** 16 bits por canal cabe nos orçamentos de memória, e a pipeline de cor (sRGB/Display P3, perceptual/linear) é viável com a biblioteca de cor escolhida.

**Duração estimada:** 1 semana

## Objetivos
1. Implementar conversão sRGB ↔ Display P3 com lcms2 (ou alternativa Rust pura).
2. Testar 16 bits (RGBA16) no R-A: memória total, tempo de composição.
3. Verificar critérios AC-1 a AC-4 (ADR-013).
4. Testar a biblioteca em WASM e iOS (compilação cross).

## Critérios de Aprovação
- AC-1: sRGB 8 bits import/export sem edição = idêntica bit a bit.
- AC-2: Display P3 export para sRGB com ΔE00 ≤ 1 no gamut.
- AC-3: mesma composição em 2 GPUs respeita tolerância visual.
- AC-4: documento mantém perfil, profundidade e blend space após reabrir.
- R-A em 16 bits cabe no iPad de referência com remoção de tiles.

## Se reprovar
- 8 bits como padrão em mobile (16 bits apenas desktop).
- Ou substituir lcms2 por alternativa.

## Entregáveis
- Relatório com medições de memória, tempos de conversão, resultados de AC-1 a AC-4.
- Recomendação para ADR-013.
