# Registro de Riscos

**Versão:** 0.1
**Data:** 2026-11-25
**Status:** Rascunho para aprovação
**Dono:** PMO

Probabilidade (P) e Impacto (I): 1 baixo – 5 alto. Exposição = P × I. Revisão a cada gate.

| ID | Risco | P | I | Exp. | Mitigação | Dono | Gatilho |
|---|---|---|---|---|---|---|---|
| RSK-01 | Latência de caneta acima da meta no Flutter com wgpu (ADR-003) | 3 | 5 | 15 | Spike B antes de fixar a arquitetura; plano B nativo por plataforma | ARQ | Spike B > 30 ms p95 |
| RSK-02 | Rust + wgpu inviável em algum alvo (ADR-001/002) | 2 | 5 | 10 | Spike A em Windows/macOS primeiro; web depois | ARQ | Spike A falha |
| RSK-03 | Formato `.rbsc` sofre corrupção sob queda de energia | 2 | 5 | 10 | WAL, CommitBatch atômico, teste de 1.000 kills (spike C) | TL core | > 0 corrupções |
| RSK-04 | Explosão de escopo: ~37 specs previstas, só 4 escritas | 4 | 4 | 16 | Cobertura medida em `coverage.md`; escrever specs por fase; gate por release | PMO | Spec atrasada > 2 semanas |
| RSK-05 | Merge conflicts em documentos compartilhados | 3 | 3 | 9 | CODEOWNERS, arquivos gerados, uma spec por PR, `sdd-check` | PMO | Conflito recorrente |
| RSK-06 | Metas numéricas sem hardware de referência | 4 | 3 | 12 | DEC-004 no início da Fase 0 | ARQ | Spike sem baseline |
| RSK-07 | Ambiguidade de fidelidade ORA/SVG/PDF/PSD | 3 | 3 | 9 | Matriz de fidelidade na SPEC-013; PSD só no R5 | TL core | Spec 013 |
| RSK-08 | Sincronização/colaboração (HLC, ADR-008/009/010) mais difícil que o previsto | 3 | 4 | 12 | Modelo de operações imutáveis já na SPEC-003; spike antes da Fase 5 | ARQ | Fim do R1 |
| RSK-09 | Conformidade LGPD/GDPR e políticas de loja (login Apple/Google) | 2 | 4 | 8 | ADR-018; DPIA antes do R2; DEC-006 | SEC | Antes do R2 |
| RSK-10 | Dependência de pessoas-chave e baixa redundância de revisão | 3 | 3 | 9 | DEC-002 (≥2 pessoas por área) | PMO | Revisor indisponível |
| RSK-11 | Método-fonte com licença CC BY-NC-SA: uso comercial dos textos adaptados | 2 | 3 | 6 | Manter atribuição; ver DEC-003; revisão jurídica | PO | Antes de distribuir |
