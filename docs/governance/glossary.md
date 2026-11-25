# Glossário

**Versão:** 0.1
**Data:** 2026-11-25
**Status:** Rascunho para aprovação
**Dono:** PMO

| Termo | Definição |
|---|---|
| Artboard (prancheta) | Área de composição dentro de um documento; um documento pode ter várias. Substitui "page" |
| Camada / nó | Elemento da árvore de cena (raster, vetor, grupo, texto, máscara…) |
| Tile | Bloco 256×256 de um raster, RGBA premultiplicado (hipótese a confirmar) |
| Dab | Carimbo individual de um pincel; um traço é uma sequência de dabs |
| Op / OpRecord | Operação imutável e idempotente registrada no oplog; undo é uma op inversa |
| HLC | Hybrid Logical Clock: relógio lógico híbrido que ordena operações |
| Oplog | Tabela/log de operações do documento |
| `.rbsc` | Extensão do formato nativo de documento do Rabisco (SQLite em modo WAL + bundle) |
| Gate / portão | Aprovação humana que libera a fase seguinte; `*:draft` nunca libera |
| Spec | Pasta `NNN-slug` com requirements, design, tasks e `.status` |
| Spec-anchored | Rigor máximo (contratos, formatos, sync, segurança) |
| Spec-first | Rigor menor (UI, ferramentas, pincéis, filtros) |
| EARS | Sintaxe de requisitos "quando/enquanto/se … o sistema deve …" |
| MoSCoW | Must / Should / Could / Won't |
| RF / RNF | Requisito funcional / não funcional **globais** (catálogo); FR/NFR são locais a uma spec |
| R-A / R-B | Documentos de referência de desempenho (4096², 30 camadas RGBA8 / 8192², 10 camadas) |
| Spike | Experimento curto e limitado que produz decisão, não produto |
| ADR | Registro de decisão de arquitetura |
| CR | Change Request (controle de mudanças) |
| Baseline | Conjunto de documentos aprovados e marcados por tag |
| WBS | Estrutura analítica do projeto |
