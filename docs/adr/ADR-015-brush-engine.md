# ADR-015 — Modelo de pincel

**Status:** Proposta
**Origem:** Nova na v2
**Data:** 2026-11-24
**Resolvida por:** SPEC-005
**Requisitos relacionados:** RF-03 (raster)

## 1. Contexto e problema
O pincel define a percepção de qualidade. Precisa de especificação e modelo paramétrico.

## 2. Decisão proposta
- **Definição de pincel versionada** (JSON com schema em `contracts/`): ponta, espaçamento, tamanho, opacidade, fluxo, rotação, dispersão, textura de papel, blend mode, suavização.
- **Dinâmicas:** curvas que ligam pressão, inclinação, azimute e velocidade aos parâmetros.
- **Renderização:** dabs aplicados em lote na GPU diretamente nos tiles.
- **Pipeline:** entrada → filtro → predição → dabs → carimbo GPU (overlay) → commit nos tiles → operação no log.
- **Predição:** só em overlay transitório (P-09). Nunca persiste.
- **Determinismo:** operação guarda amostras de entrada + hash do pincel + semente. Tiles são autoridade (P-04).
- **Conjunto inicial (R1):** lápis, caneta, aerógrafo, marcador, borracha.
- **Fora do R1:** mistura úmida, editor visual de pincéis.
- **Compatibilidade com formatos terceiros:** fora do início por risco de licença.

## 3. Critérios de aceitação (hipóteses)
- Latência caneta → tela p95 ≤ 30 ms (meta 20 ms).
- Traço de 1.000 amostras reproduzido = tiles idênticos (mesma GPU).
- Dinâmicas de pressão/inclinação validadas contra gravações de referência.

## 4. Critérios de reavaliação
Se o modelo de dabs não atingir a qualidade percebida em testes com artistas.
