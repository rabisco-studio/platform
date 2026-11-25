# ADR-008 — Persistência local e estratégia offline-first

**Status:** Proposta
**Origem:** v1 (mantida)
**Data:** 2026-11-24
**Resolvida por:** SPEC-003
**Requisitos relacionados:** RF-08.4 (cópias locais), RNF-02 (confiabilidade)

## 1. Contexto e problema
A experiência de desenho não pode depender de conexão. Alterações são persistidas localmente primeiro (P-02) e sincronizadas depois.

## 2. Decisão proposta
Offline-first: toda edição é salva localmente em SQLite (ADR-007) antes de qualquer tentativa de sync. O app funciona integralmente sem internet. A sync é assíncrona e retomável.

## 3. Consequências
- Positivas: experiência sem interrupções, resiliência a falhas de rede.
- Negativas: necessidade de reconciliação quando voltar online (ADR-009).

## 4. Critérios de reavaliação
Se o modelo de operações não suportar reconciliação eficiente (SPEC-003).
