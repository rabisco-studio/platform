# ADR-017 — Observabilidade

**Status:** Proposta
**Origem:** Nova na v2
**Data:** 2026-11-24
**Resolvida por:** Fase 5
**Requisitos relacionados:** RNF-02 (confiabilidade), RNF-04.8 (auditoria), RNF-10

## 1. Contexto e problema
Sem observabilidade, problemas de sincronização são invisíveis até o usuário reportar perda de dados.

## 2. Decisão proposta
- **OpenTelemetry** para traces, métricas e logs no backend e worker Rust.
- **SLIs de sincronização:** latência de confirmação, atraso por dispositivo, taxa de conflitos, falhas de upload, fila pendente.
- **Auditoria** separada dos logs de aplicação, com retenção própria.
- **Telemetria do cliente opt-in:** desempenho (frame time, latência, memória) e crash reports, sem conteúdo do documento.
- Endpoints de saúde, alertas e painéis por ambiente.

## 3. Consequências
- Positivas: visibilidade operacional, detecção proativa.
- Negativas: complexidade de infraestrutura, custo de armazenamento de telemetria.

## 4. Critérios de reavaliação
Se o volume de telemetria se tornar custoso antes da escala justificar.
