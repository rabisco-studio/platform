# SPEC-NNN — Design

**Status:** design:draft | design:approved
**Requisitos:** requirements:approved em AAAA-MM-DD

## 1. Resumo executivo

A arquitetura desta feature em duas ou três frases.

## 2. Requirements Mapping

> Seção mais importante. Um FR sem destino no design é uma lacuna que vira lacuna no código.

| FR/NFR | Decisão de design | Crate/módulo | TD |
|--------|-------------------|-------------|-----|
| FR-001 | — | — | TD-001 |
| FR-002 | — | — | — |
| NFR-001 | — | — | — |

## 3. Arquitetura

Diagrama e descrição da arquitetura da feature. Crates e módulos envolvidos, fluxo de dados, pontos de integração.

```
[diagrama aqui]
```

## 4. Modelo de dados

Estruturas de dados, tabelas, schemas. Incluir tipos Rust quando relevante.

## 5. Contratos afetados

| Contrato | Arquivo em `contracts/` | Mudança |
|----------|------------------------|---------|
| — | — | — |

> Se nenhum contrato é afetado, declarar explicitamente.

## 6. Crates e módulos impactados

| Crate | Módulo | Tipo de mudança |
|-------|--------|----------------|
| — | — | Novo / Alterado / — |

## 7. Compatibilidade e migração

(Para specs que tocam formato ou protocolo.)

- Versão anterior do schema: —
- Estratégia de migração: —
- Teste de compatibilidade: —

## 8. Segurança e privacidade

(Obrigatório para specs com tags `security` ou `privacy`.)

- Dados sensíveis envolvidos: —
- Verificação de permissão: —
- Auditoria: —

## 9. Casos de borda

| Caso | Comportamento |
|------|--------------|
| — | — |

## 10. Estratégia de verificação

| FR/NFR | Tipo | Estratégia |
|--------|------|-----------|
| FR-001 | `[BEH]` | Teste unitário em `crate::module::test` |
| NFR-001 | `[PERF]` | Benchmark com R-A no dispositivo X |

## 11. Decisões técnicas

### TD-001 — Título
**Contexto:** —
**Alternativas:** A, B, C.
**Decisão:** —
**Motivo:** —

> Se a decisão afeta duas ou mais specs ou um contrato público, promover a ADR em `docs/adr/`.

## 12. Riscos

| Risco | Mitigação |
|-------|-----------|
| — | — |
