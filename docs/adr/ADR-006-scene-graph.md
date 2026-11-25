# ADR-006 — Scene Graph como representação documental

**Status:** Proposta
**Origem:** v1 (mantida)
**Data:** 2026-11-24
**Resolvida por:** SPEC-001
**Requisitos relacionados:** RF-05 (sistema híbrido)

## 1. Contexto e problema

O documento precisa de uma representação hierárquica que suporte pranchetas, grupos, camadas raster, paths vetoriais, texto e metadados, com IDs estáveis para operações e sincronização.

## 2. Alternativas consideradas

### Alternativa A — Árvore hierárquica (Scene Graph)
- Estrutura natural para composição gráfica. IDs estáveis por nó. Traversal para rendering e serialização.

### Alternativa B — Lista plana de camadas
- Mais simples.
- Desvantagem: não representa grupos, pranchetas nem hierarquia de composição.

## 3. Decisão proposta

Scene Graph com nós tipados (Document, Artboard, Group, RasterLayer, VectorLayer, EmbeddedImage), cada um com ID estável. Paths, formas e texto são objetos contidos em uma VectorLayer (não nós da árvore). Máscara e caminho de recorte são atributos do nó, posição, transformação, opacidade, blend mode, visibilidade e bloqueio.

## 4. Justificativas

A hierarquia é essencial para composição, máscaras de grupo, transformações aninhadas e operações semânticas.

## 5. Consequências

### Positivas
- Composição natural. Operações semânticas por nó. Serialização e sync por nó.

### Negativas
- Complexidade de traversal. Necessidade de proteger contra ciclos (SPEC-001 FR-003; regra de conflito de movimentação na ADR-009).

## 6. Critérios de reavaliação

- Se a serialização da árvore se tornar gargalo de desempenho (benchmark).
