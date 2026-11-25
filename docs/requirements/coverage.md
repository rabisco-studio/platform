<!-- GERADO por tools/sdd/generate.py. NÃO EDITAR. Rode `make docs`. -->

# Cobertura de especificação

Gerado a partir de `requirements-catalog.csv`, `spec-catalog.csv` e das specs escritas. Mostra **quanto do produto está de fato especificado**.

## Resumo

- Requisitos catalogados: **132** (81 RF + 51 RNF)
- Specs no plano: **37**; escritas: **4**; planejadas: **33**
- Requisitos com cobertura em spec escrita: **42** de 132

## Por release

| Release | Requisitos | Cobertos por spec escrita | Specs no plano | Specs escritas |
|---|---|---|---|---|
| R1 | 78 | 41 | 17 | 4 |
| R2 | 32 | 1 | 5 | 0 |
| R3 | 10 | 0 | 3 | 0 |
| R4 | 10 | 0 | 5 | 0 |
| R5 | 2 | 0 | 7 | 0 |

## Por spec

| Spec | Título | Fase | Release | Rigor | Estado | `.status` | FRs | Tarefas | Horas |
|---|---|---|---|---|---|---|---|---|---|
| SPEC-001 | Scene Graph | 1 | R1 | anchored | escrita | requirements:draft | 12 | 10 | 29 |
| SPEC-002 | Formato .hybrid e ciclo de vida do documento | 1 | R1 | anchored | escrita | requirements:draft | 13 | 10 | 34 |
| SPEC-003 | Modelo de operações e Undo/Redo | 1 | R1 | anchored | escrita | requirements:draft | 11 | 9 | 30 |
| SPEC-004 | Render de camadas raster e vetor no mesmo canvas | 1 | R1 | anchored | planejada | - | - | - | - |
| SPEC-005 | Pincéis e pintura raster | 2 | R1 | anchored | escrita | requirements:draft | 12 | 9 | 28 |
| SPEC-006 | Tiles e orçamento de memória | 2 | R1 | anchored | planejada | - | - | - | - |
| SPEC-007 | Seleção e transformação de regiões | 2 | R1 | spec-first | planejada | - | - | - | - |
| SPEC-008 | Máscaras raster, transparência e máscaras de grupo | 2 | R1 | spec-first | planejada | - | - | - | - |
| SPEC-009 | Paths, Bézier, preenchimentos e transformação | 3 | R1 | spec-first | planejada | - | - | - | - |
| SPEC-010 | Formas, contornos e operações booleanas | 3 | R1 | spec-first | planejada | - | - | - | - |
| SPEC-011 | Texto vetorial editável | 3 | R1 | spec-first | planejada | - | - | - | - |
| SPEC-012 | Composição híbrida: grupos, ordem, pranchetas, não destrutivo, vetor para raster | 4 | R1 | anchored | planejada | - | - | - | - |
| SPEC-013 | Importação e exportação | 4 | R1 | anchored | planejada | - | - | - | - |
| SPEC-014 | Filtros e ajustes básicos | 4 | R1 | spec-first | planejada | - | - | - | - |
| SPEC-015 | Pipeline de cor e perfis | 1 | R1 | anchored | planejada | - | - | - | - |
| SPEC-016 | Interface desktop | 4 | R1 | spec-first | planejada | - | - | - | - |
| SPEC-017 | Mistura de cores básica | 2 | R1 | spec-first | planejada | - | - | - | - |
| SPEC-018 | Identidade e autenticação | 5 | R2 | anchored | planejada | - | - | - | - |
| SPEC-019 | Documentos, biblioteca, versões, quotas e backup na nuvem | 5 | R2 | anchored | planejada | - | - | - | - |
| SPEC-020 | Upload e download por URLs pré-assinadas | 5 | R2 | anchored | planejada | - | - | - | - |
| SPEC-021 | Protocolo de sincronização | 5 | R2 | anchored | planejada | - | - | - | - |
| SPEC-022 | Fundação do backend: segurança, observabilidade, privacidade, escalabilidade | 5 | R2 | anchored | planejada | - | - | - | - |
| SPEC-023 | Compartilhamento e permissões | 6 | R3 | anchored | planejada | - | - | - | - |
| SPEC-024 | Colaboração em tempo real | 6 | R3 | anchored | planejada | - | - | - | - |
| SPEC-025 | Comentários e revisão | 6 | R3 | spec-first | planejada | - | - | - | - |
| SPEC-026 | iPadOS e Android; gestos multitouch | 7 | R4 | spec-first | planejada | - | - | - | - |
| SPEC-027 | Cliente web | 7 | R4 | anchored | planejada | - | - | - | - |
| SPEC-028 | Interface responsiva entre dispositivos | 7 | R4 | spec-first | planejada | - | - | - | - |
| SPEC-029 | Plugins WASM | 8 | R5 | anchored | planejada | - | - | - | - |
| SPEC-030 | Importação de PSD | 8 | R5 | anchored | planejada | - | - | - | - |
| SPEC-031 | CMYK | 8 | R5 | anchored | planejada | - | - | - | - |
| SPEC-032 | Editor de pincéis e mistura úmida | 8 | R5 | spec-first | planejada | - | - | - | - |
| SPEC-033 | Filtros avançados | 8 | R5 | spec-first | planejada | - | - | - | - |
| SPEC-034 | Vetorização de raster | 8 | R5 | spec-first | planejada | - | - | - | - |
| SPEC-035 | Tipografia avançada | 8 | R5 | spec-first | planejada | - | - | - | - |
| SPEC-036 | Painéis personalizáveis | 7 | R4 | spec-first | planejada | - | - | - | - |
| SPEC-037 | Acessibilidade e internacionalização | 7 | R4 | spec-first | planejada | - | - | - | - |

## Requisitos Must do R1 ainda sem spec escrita

| Requisito | Spec dona | Descrição |
|---|---|---|
| RF-03.7 | SPEC-007 | Seleção e transformação de regiões |
| RF-04.2 | SPEC-009 | Ferramenta Pen com curvas Bézier |
| RF-04.3 | SPEC-010 | Formas geométricas |
| RF-04.4 | SPEC-009 | Edição de pontos de controle |
| RF-04.9 | SPEC-009 | Transformação de objetos |
| RF-05.8 | SPEC-012 | Múltiplas pranchetas |
| RF-07.1 | SPEC-013 | Exportar PNG, JPEG e WebP (TIFF no R5) |
| RF-07.2 | SPEC-013 | Exportar SVG (PDF como Should; ORA como Should) |
| RF-07.5 | SPEC-013 | Configurações de resolução e qualidade |
| RF-07.6 | SPEC-013 | Exportação de elementos individuais e pranchetas |
| RF-10.1 | SPEC-016 | Interface adaptável ao dispositivo |
| RF-10.3 | SPEC-016 | Atalhos de teclado |
| RNF-01.4 | SPEC-004 | Operações gráficas intensivas preferencialmente na GPU |
| RNF-02.3 | SPEC-002 | Não depender da nuvem para abrir documentos locais |
| RNF-03.1 | SPEC-016 | Versões para Windows, macOS e Linux |
| RNF-03.5 | SPEC-016 | Adaptar a interface às características de cada dispositivo |
| RNF-03.6 | SPEC-005 | Suportar mouse, touchscreen e canetas digitais |
| RNF-06.1 | SPEC-016 | Adaptar a interface a diferentes tamanhos de tela |
| RNF-06.3 | SPEC-016 | Navegação por teclado |
