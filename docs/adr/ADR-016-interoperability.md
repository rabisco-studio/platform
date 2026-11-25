# ADR-016 — Interoperabilidade de formatos

**Status:** Proposta
**Origem:** Nova na v2
**Data:** 2026-11-24
**Resolvida por:** SPEC-013 (Import/Export)
**Requisitos relacionados:** RF-07 (importação/exportação)

## 1. Contexto e problema
Para adoção profissional, o editor precisa importar e exportar formatos padrão da indústria.

## 2. Decisão proposta

| Formato | Importar | Exportar | Release |
|---------|----------|----------|---------|
| PNG, JPEG, WebP | Sim | Sim | R1 |
| ORA (OpenRaster) | Sim | Sim | R1 |
| SVG | Subconjunto definido | Sim | R1 |
| PDF | Vetorial e página rasterizada | Sim | R1 (export) / R5 (import) |
| TIFF | — | Sim | R5 |
| PSD | Leitura (camadas/máscaras básicas) | Não prometido | R5 |

- **Matriz de fidelidade** publicada: o que é preservado, aproximado ou descartado.
- **Relatório de importação** exibido ao usuário. Nenhuma perda silenciosa.
- PSD é publicamente documentado, mas cobertura completa é projeto à parte.

## 3. Consequências
Escopo de R1 factível (PNG, JPEG, WebP, ORA, SVG, PDF export). PSD adiado.

## 4. Critérios de reavaliação
Se a comunidade exigir PSD antes do R5.
