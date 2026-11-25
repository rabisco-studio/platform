# Resumo das specs (spec-summary)

Roteador das 37 specs do plano: **uma linha por spec** e os links para os documentos. Aqui não há status, fase nem rigor: isso é fato de outro arquivo (fonte única). Para o estágio de cada spec veja o [INDEX.md](../INDEX.md) (gerado), para o catálogo o [spec-catalog.csv](../../../docs/requirements/spec-catalog.csv) e para a cobertura o [coverage.md](../../../docs/requirements/coverage.md).

**Como manter:** o `sdd-check` exige uma linha para cada spec do catálogo e o link da pasta de cada spec escrita. `make new-spec N=018` preenche a coluna "Documentos" sozinho; a linha de resumo já existe e é ajustada à mão quando a spec for escrita.

| Spec | O que é | Documentos |
|---|---|---|
| SPEC-001 | Estrutura em memória que representa o documento: pranchetas, grupos, camadas raster, vetor e máscaras; base do formato `.rbsc` | [requirements](001-scene-graph/requirements.md) · [design](001-scene-graph/design.md) · [tasks](001-scene-graph/tasks.md) |
| SPEC-002 | Como o usuário cria, abre, salva e recupera documentos `.rbsc`: autosave, proteção contra queda, migração e dono único do DDL | [requirements](002-rbsc-format/requirements.md) · [design](002-rbsc-format/design.md) · [tasks](002-rbsc-format/tasks.md) |
| SPEC-003 | Envelope de operação, Undo/Redo e regras de persistência; preparado para sincronização, mas local nesta fase | [requirements](003-operations-undo/requirements.md) · [design](003-operations-undo/design.md) · [tasks](003-operations-undo/tasks.md) |
| SPEC-004 | Render de camadas raster e vetor no mesmo canvas: contexto de GPU, composição e modos de mesclagem | — |
| SPEC-005 | Pipeline de pintura raster: da entrada de caneta ou mouse ao commit dos tiles no log de operações (pincel, stamping na GPU, predição de traço) | [requirements](005-brush-painting/requirements.md) · [design](005-brush-painting/design.md) · [tasks](005-brush-painting/tasks.md) |
| SPEC-006 | Tiles e orçamento de memória das camadas raster | — |
| SPEC-007 | Seleção e transformação de regiões | — |
| SPEC-008 | Máscaras raster, transparência e máscaras de grupo | — |
| SPEC-009 | Paths vetoriais: Bézier, preenchimentos e transformação | — |
| SPEC-010 | Formas geométricas, contornos e operações booleanas | — |
| SPEC-011 | Texto vetorial editável | — |
| SPEC-012 | Composição híbrida: grupos, ordem, pranchetas, edição não destrutiva e conversão de vetor para raster | — |
| SPEC-013 | Importação e exportação de PNG, JPEG, WebP, ORA, SVG e PDF | — |
| SPEC-014 | Filtros e ajustes básicos | — |
| SPEC-015 | Pipeline de cor e perfis (ADR-013) | — |
| SPEC-016 | Interface desktop em Flutter: painéis, atalhos, temas, tutoriais e biblioteca local | — |
| SPEC-017 | Mistura de cores básica (smudge) | — |
| SPEC-018 | Identidade e autenticação de usuários | — |
| SPEC-019 | Documentos, biblioteca, versões, quotas e backup na nuvem | — |
| SPEC-020 | Upload e download de arquivos por URLs pré-assinadas | — |
| SPEC-021 | Protocolo de sincronização, como contrato (ADR-008 e ADR-009) | — |
| SPEC-022 | Fundação do backend: segurança, observabilidade, privacidade e escalabilidade | — |
| SPEC-023 | Compartilhamento de documentos e permissões | — |
| SPEC-024 | Colaboração em tempo real (ADR-010) | — |
| SPEC-025 | Comentários e revisão | — |
| SPEC-026 | Clientes iPadOS e Android, com gestos multitouch | — |
| SPEC-027 | Cliente web (ADR-004) | — |
| SPEC-028 | Interface responsiva entre dispositivos | — |
| SPEC-029 | Plugins em WebAssembly com sandbox (ADR-012) | — |
| SPEC-030 | Importação de PSD (ADR-016) | — |
| SPEC-031 | Suporte a CMYK | — |
| SPEC-032 | Editor de pincéis e mistura úmida | — |
| SPEC-033 | Filtros avançados | — |
| SPEC-034 | Vetorização de imagens raster | — |
| SPEC-035 | Tipografia avançada | — |
| SPEC-036 | Painéis personalizáveis | — |
| SPEC-037 | Acessibilidade e internacionalização | — |

"—" na coluna Documentos significa que a spec ainda é **planejada**: não existe pasta. As linhas das specs planejadas descrevem só o que o título do catálogo diz; o escopo real nasce em cada `requirements.md`.
