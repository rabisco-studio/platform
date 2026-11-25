# ADR-009 — Sincronização baseada em operações

**Status:** Proposta
**Origem:** Revisada na v2
**Data:** 2026-11-24
**Resolvida por:** SPEC-003
**Requisitos relacionados:** RF-06 (histórico), RF-08 (nuvem), RF-09 (colaboração)

## 1. Contexto e problema
O modelo de operações serve Undo/Redo, histórico, autosave e sincronização. Precisa existir na Fase 1 para evitar reescrita na Fase 5.

## 2. Alternativas consideradas

### Alternativa A — Operações imutáveis com relógio lógico híbrido (HLC)
- Operação: `{op_id, doc_id, author_id, device_id, hlc, base_seq, schema_version, type, targets, payload, inverse}`.
- Imutáveis e idempotentes. Undo como operação inversa. Servidor atribui sequência.

### Alternativa B — CRDT (Yrs, Automerge, Loro)
- Convergência automática sem servidor.
- Desvantagem: overhead de memória em documentos grandes, complexidade em raster.

### Alternativa C — Substituição de estado (snapshot diff)
- Simples.
- Desvantagem: sem Undo granular, sem histórico, diffs pesados em raster.

## 3. Decisão proposta
Operações imutáveis e idempotentes com HLC. Regras de conflito:
- Propriedade de nó: LWW por propriedade, empate por device_id.
- Ordem de camadas: índices fracionários.
- Mover nó: servidor rejeita ciclos; vence maior relógio.
- Excluir vs. editar: exclusão vence; edição permanece no log.
- Raster: bloqueio cooperativo por camada (Fase 6).
- Presença/cursores: efêmeros.
- Permissões: autoridade do servidor.

CRDTs comparados com LWW+índices fracionários em spike futuro. Hipótese: implementação própria basta.

## 4. Consequências
- Positivas: modelo unificado para Undo, histórico e sync. Operações auditáveis.
- Negativas: complexidade de reconciliação. Compactação periódica necessária.

## 5. Critérios de reavaliação
Se testes de propriedades mostrarem não-convergência. Se reconciliação de 1.000 ops exceder 10 s.

## Nota de implementação (2026-11-25)

No R1 (um autor, sem sync) valem apenas as regras locais: idempotência por `op_id` (checada antes do HLC) e HLC monotônico por `device_id` para operações geradas localmente. A chegada de operações remotas, fora de ordem ou de outros autores é definida na spec de sincronização (Fase 5). Ver SPEC-003, decisão D-004.
