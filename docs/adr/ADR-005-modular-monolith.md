# ADR-005 — Arquitetura modular para o backend

**Status:** Proposta
**Origem:** v1 (mantida)
**Data:** 2026-11-24
**Resolvida por:** Baixo risco
**Requisitos relacionados:** RNF-05 (escalabilidade)

## 1. Contexto e problema

O backend precisa ser organizado, mas a complexidade operacional de microsserviços é prematura antes de haver escala real.

## 2. Alternativas consideradas

### Alternativa A — Modular monolith
- Módulos com limites claros dentro de um único deploy. Extração futura quando justificada.

### Alternativa B — Microsserviços desde o início
- Escala independente por serviço.
- Desvantagem: complexidade operacional, latência de rede entre serviços, overhead de deploy.

## 3. Decisão proposta

Modular monolith em Java + Spring Boot. Módulos com interfaces explícitas, permitindo extração futura.

## 4. Justificativas

Simplicidade operacional. A extração é possível quando houver necessidade comprovada.

## 5. Consequências

### Positivas
- Deploy simples. Transações locais. Debug mais fácil.

### Negativas
- Risco de acoplamento se os limites de módulo não forem respeitados.

## 6. Critérios de reavaliação

- Quando um módulo precisar escalar independentemente.
- Quando o tempo de deploy do monolito se tornar problemático.
