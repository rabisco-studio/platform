# SPEC-005: Pincéis e Pintura Raster — Pincéis, Traços e Pipeline de Entrada

**Status:** requirements:draft
**Área:** core
**Release:** R1
**Rigor:** anchored
**Tags:** contract, perf
**ADRs:** ADR-002, ADR-013, ADR-015
**Depende de:** SPEC-001, SPEC-003, SPEC-004 (`GpuContext` e `render-engine`), Spike (a)

---

## 1. Visão Geral

Esta spec define o pipeline completo de pintura raster: da entrada da caneta/mouse ao commit dos tiles alterados no log de operações. Abrange o modelo de pincel, o stamping na GPU, a predição de traço e a integração com o Scene Graph (SPEC-001) e o modelo de operações (SPEC-003).

## 2. Goals

- Latência caneta → tela p95 ≤ 30 ms (meta 20 ms em tablets de ponta).
- Determinismo: mesmo input + mesmo pincel = mesmos tiles (mesma GPU).
- Conjunto inicial de pincéis (R1): lápis, caneta, aerógrafo, marcador, borracha.
- Integração completa com o pipeline de cor (ADR-013).

## 3. Non-Goals

- Sem editor visual de pincéis: R5 (RF-03.3).
- Sem mistura úmida (wet mixing): R5.
- Sem compatibilidade com pincéis de terceiros (Krita, Photoshop): risco de licença.
- Sem texturas de papel avançadas: apenas textura básica (opacity mask) no R1.
- Sem filtros e ajustes: spec separada (RF-03.9 limitado no R1).
- Sem seleção e transformação de regiões: SPEC-007 (RF-03.7, Must do R1).
- Sem a composição de camadas na tela nem o contexto GPU: SPEC-004 (esta spec adiciona o overlay e o shader de carimbo).

## 4. Plataformas e Dispositivos de Referência

| Tier | Plataforma | Input | Caneta de referência |
|------|-----------|-------|---------------------|
| 1 | Windows/macOS | Mouse + Wacom Intuos | Wacom Intuos Pro (pressão + inclinação) |
| 1 | Windows/macOS | Caneta integrada | Surface Pro Pen |
| 2 | iPadOS | Apple Pencil | Apple Pencil 2nd gen |
| 3 | Web | Mouse + touch | — |

## 5. User Stories

### US-001 — Pintar com lápis
**Como** artista, **quero** usar o lápis com variação de pressão e inclinação, **para** fazer esboços naturais.
- **AC-001 [VIS]:** Traço de referência (1.000 amostras, pressão crescente 0→1) = golden image ± 4/255 por canal.
- **AC-002 [PERF]:** Latência caneta → tela p95 ≤ 30 ms.

### US-002 — Pintar com caneta e aerógrafo
**Como** artista, **quero** usar caneta (traço limpo) e aerógrafo (spray difuso), **para** ter ferramentas versáteis.
- **AC-003 [VIS]:** Caneta: bordas definidas. Aerógrafo: opacidade acumulativa com spray.

### US-003 — Apagar com borracha
**Como** artista, **quero** usar a borracha para remover pixels, **para** corrigir o desenho.
- **AC-004 [BEH]:** Borracha altera o canal alfa para 0 nos pixels afetados.

### US-004 — Dinâmicas de caneta
**Como** artista, **quero** mapear pressão, inclinação e velocidade a tamanho, opacidade e fluxo, **para** ter controle expressivo.
- **AC-005 [BEH]:** Curvas de mapeamento configuráveis por pincel. Padrão: pressão → opacidade (linear).
- **AC-006 [BEH]:** Inclinação altera o ângulo do dab quando habilitada no pincel.

### US-005 — Desfazer traço
**Como** artista, **quero** desfazer um traço inteiro (não dab a dab), **para** corrigir rapidamente.
- **AC-007 [BEH]:** Undo de traço restaura todos os tiles à versão anterior. Nenhum pixel parcial.

### US-006 — (Removida) Seleção e transformação de região
Movida para a **SPEC-007** (Seleção e transformação de regiões, RF-03.7, prioridade Must). O ID é mantido como registro e não é reutilizado.

## 6. Requisitos Funcionais (EARS + MoSCoW)

### FR-001 (Must) [BEH]
**Cobre:** RF-03.1
Cada pincel DEVE ser definido por uma **definição versionada** (JSON com schema em `contracts/brush-definition/`): ponta (shape), espaçamento (% do diâmetro), tamanho (px), opacidade, fluxo, rotação, dispersão, textura de papel, blend mode, suavização.

### FR-002 (Must) [BEH]
**Cobre:** RF-03.2, RF-10.5
Dinâmicas DEVEM ser curvas que mapeiam pressão (0–1), inclinação (0–90°), azimute (0–360°) e velocidade (px/ms) a: tamanho, opacidade, fluxo, rotação, dispersão.

### FR-003 (Must) [BEH]
**Cobre:** RF-03.2
QUANDO o usuário iniciar um traço, O SISTEMA DEVE capturar amostras de entrada (posição, timestamp, pressão, inclinação, azimute) e produzir dabs aplicados em lote na GPU.

### FR-004 (Must) [BEH]
**Cobre:** RF-03.1
Dabs DEVEM ser aplicados em um **overlay transitório** durante o traço. QUANDO o traço terminar, os pixels do overlay DEVEM ser compostos nos tiles da camada e uma operação DEVE ser commitada.

### FR-005 (Must) [BEH]
**Cobre:** RNF-01.3
Predição de traço (ponto(s) à frente do input real) DEVE existir apenas no overlay transitório e NUNCA DEVE ser persistida nos tiles nem no log de operações (P-09).

### FR-006 (Must) [BEH]
**Cobre:** RF-03.1, RF-06.1
QUANDO um traço terminar, O SISTEMA DEVE:
1. Compor o overlay nos tiles da camada,
2. Calcular os hashes dos tiles alterados,
3. Criar Operation de tipo `raster.stroke` com payload (new hashes) e inverse (old hashes),
4. Persistir via SPEC-003 (`document-engine`) → SPEC-002 (`file-engine`).

### FR-007 (Must) [VIS]
**Cobre:** RF-02.3
Composição de dabs DEVE respeitar o espaço de trabalho do documento (ADR-013): sRGB ou Display P3, perceptual ou linear, com alfa pré-multiplicado.

### FR-008 (Must) [PERF]
**Cobre:** RNF-01.3
Latência de entrada até exibição p95 ≤ 30 ms com caneta no dispositivo de referência Tier 1.

### FR-009 (Must) [BEH]
**Cobre:** RF-03.4
Conjunto inicial de pincéis (R1): lápis, caneta, aerógrafo, marcador, borracha. Cada um com definição JSON e golden images de referência.

### FR-010 (Must) [BEH]
**Cobre:** RF-03.4
Borracha DEVE alterar o canal alfa dos pixels para 0 (ou valor proporcional à pressão) nos tiles afetados.

### FR-011 (Removido)
Movido para a **SPEC-007** (RF-03.7, Must). O ID é mantido como registro e não é reutilizado.

### FR-012 (Should) [BEH]
**Cobre:** RF-03.5
O SISTEMA DEVERIA suportar textura de papel como máscara de opacidade aplicada aos dabs.

### FR-013 (Must) [BEH]
**Cobre:** RF-06.2
Operação de traço DEVE guardar: amostras de entrada + hash da definição do pincel + semente aleatória. Tiles são autoridade (P-04): replay é informativo, não obrigatório.

## 7. Requisitos Não Funcionais

### NFR-001 [PERF]
**Cobre:** RNF-01.3
Latência entrada → tela p95 ≤ 30 ms com caneta Wacom no desktop de referência.

### NFR-002 [PERF]
**Cobre:** RNF-01.1
Frame time p95 ≤ 16,6 ms (60 fps sustentados) durante pintura em R-A.

### NFR-003 [VIS]
**Cobre:** RNF-03.4
Determinismo: traço de 1.000 amostras com mesmo pincel e mesma GPU = tiles idênticos (hash match).

### NFR-004 [PERF]
**Cobre:** RNF-02.1
Commit de traço (overlay → tiles → persist) p95 ≤ 100 ms.

## 8. Restrições

- Dabs são aplicados na GPU via compute shader WGSL (ADR-002).
- Overlay é textura transitória: nunca no tile store, nunca no oplog.
- Alfa pré-multiplicado em toda a pipeline (ADR-013).
- Nenhuma predição de traço persiste em qualquer camada de armazenamento.

## 9. Decisões de Produto

- **D-001:** Traço inteiro é uma operação atômica para Undo (não dab a dab).
- **D-002:** Pincéis do R1 são definições fixas. Sem customização pelo usuário no R1.
- **D-003:** Suavização de traço (input smoothing) ligada por padrão, configurável por pincel.

## 10. Pipeline de Pintura (detalhado)

```
Input (caneta/mouse/touch)
  │
  ├─ 1. Captura: (x, y, pressure, tilt, azimuth, timestamp)
  │
  ├─ 2. Filtro de suavização: moving average ou similar
  │     (remove jitter da digitalização)
  │
  ├─ 3. Predição: 1–3 pontos à frente (overlay APENAS)
  │
  ├─ 4. Geração de dabs:
  │     Para cada intervalo de espaçamento ao longo do traço:
  │     - Calcular posição, tamanho, opacidade, rotação via dinâmicas
  │     - Gerar dab (shape × opacity × texture)
  │
  ├─ 5. Stamping GPU:
  │     Compute shader aplica dabs no overlay texture
  │     Blend mode do pincel aplicado
  │
  ├─ 6. Composição de exibição:
  │     Overlay + camada atual → tela (shader de composição)
  │     Conversão do espaço de trabalho → perfil do monitor
  │
  └─ 7. Fim do traço:
        Overlay compostos nos tiles da camada
        Hashes calculados
        Operação criada e persistida (SPEC-003 → SPEC-002)
        Overlay limpo
```

## 11. Implementation FAQ

- **Q-001:** Quantos dabs por traço típico? **R:** ~200–500 para um traço de 1s a 60 fps. Espaçamento padrão = 25% do diâmetro.
- **Q-002:** Overlay é uma textura do tamanho do canvas? **R:** Não. Overlay é alocado por bounding box do traço (com margem), para economizar memória.
- **Q-003:** Qual o formato da ponta do pincel? **R:** Textura de opacidade (8 bits, single channel) + shape mask. Gerada na CPU, uploadada como textura GPU.
- **Q-004:** Suavização afeta a latência? **R:** Sim, ~2–5 ms adicionais. Configurável (desligável).
- **Q-005:** E se o traço cruzar o limite de um tile? **R:** O pipeline de stamping opera em coordenadas de canvas; tiles são recortados e atualizados independentemente.

## 12. Métricas de Sucesso

- Latência p95 ≤ 30 ms medida com timestamp de sistema (ou câmera de alta velocidade).
- 60 fps sustentados durante pintura em R-A.
- Determinismo: 100% de reprodutibilidade em mesma GPU.
- 5 pincéis do R1 com golden images validadas.

## 13. Riscos

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Latência acima de 30 ms | Experiência ruim | Reduzir suavização; otimizar shader; medir no spike (a) |
| Determinismo quebra entre GPUs | Impossível golden images universais | Tolerância ≤ 4/255 entre GPUs; determinismo exato apenas por GPU |
| Overlay grande em canvas grandes | OOM | Bounding box do traço, não canvas inteiro |
| Predição persistida por bug | Dados falsos no documento | Assert no commit: overlay vazio antes de persist |

## 14. Exemplos Concretos

### Definição do pincel "Lápis" (simplificada)

```json
{
  "schema_version": "1.0.0",
  "name": "Lápis",
  "id": "builtin:pencil",
  "tip": {
    "shape": "round",
    "hardness": 0.8,
    "texture": null
  },
  "spacing": 0.15,
  "size": { "base": 5, "min": 1, "max": 100, "unit": "px" },
  "opacity": { "base": 0.9 },
  "flow": { "base": 1.0 },
  "blend_mode": "Normal",
  "smoothing": 0.3,
  "dynamics": {
    "pressure": {
      "size": { "curve": "linear", "min": 0.3, "max": 1.0 },
      "opacity": { "curve": "linear", "min": 0.2, "max": 1.0 }
    },
    "tilt": {
      "rotation": { "curve": "linear", "min": 0, "max": 1.0 }
    }
  }
}
```
