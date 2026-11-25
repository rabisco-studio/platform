# ADR-011 — Versionamento de documentos

**Status:** Proposta
**Origem:** v1 (mantida)
**Data:** 2026-11-24
**Resolvida por:** Fase 5
**Requisitos relacionados:** RF-08.6 (histórico de versões)

## 1. Contexto e problema
Usuários precisam acessar versões anteriores de um documento para restauração e comparação.

## 2. Decisão proposta
- Versionamento baseado em snapshots periódicos + oplog (ADR-007/009).
- Cada snapshot tem ID, checksum, referência ao documento e autor.
- Política de retenção configurável por workspace.
- Blobs (tiles, assets) no object storage, identificados por hash — deduplicação natural.
- RPO ≤ 5 min, RTO ≤ 4 h.

## 3. Consequências
- Positivas: restauração confiável, auditoria.
- Negativas: custo de armazenamento proporcional ao volume de edições.

## 4. Critérios de reavaliação
Se o custo de armazenamento se tornar proibitivo antes de definir o modelo de negócio.
