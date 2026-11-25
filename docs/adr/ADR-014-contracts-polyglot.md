# ADR-014 — Contratos e estratégia polyglot (worker Rust no backend)

**Status:** Proposta
**Origem:** Nova na v2
**Data:** 2026-11-24
**Resolvida por:** Conformance suite
**Requisitos relacionados:** RNF-07.4 (documentação de contratos)

## 1. Contexto e problema
Rust, Java, TypeScript e Dart podem divergir silenciosamente em protocolo e formato. O risco é proporcional ao número de linguagens.

## 2. Decisão proposta
- **Servidor como autoridade de ordem e permissão**, não intérprete da cena (P-05).
- **Worker Rust no backend** para tudo que exige o core: miniaturas, exportação, validação de formato, compactação e verificação de integridade.
- **Contratos como fonte única** em `contracts/`:
  - `api/`: OpenAPI 3.1 → gera interfaces Spring Boot e clientes TS/Dart.
  - `events/`: AsyncAPI + JSON Schema para WebSocket e envelope de operação.
  - `document-format/`: schema do manifesto, cena e operações.
  - `conformance/`: vetores de teste compartilhados.
- **Conformance suite no CI:** Rust e Java executam os mesmos vetores. Divergência quebra o build.
- **Compatibilidade:** verificação de breaking changes nos schemas a cada PR.

## 3. Consequências
- Positivas: fonte única de verdade, divergência detectada automaticamente.
- Negativas: overhead de manter contratos e geração de código.

## 4. Critérios de reavaliação
Se a geração automática não suportar um caso de uso específico.
