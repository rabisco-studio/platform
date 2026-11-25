# ADR-012 — Sistema de plugins e extensibilidade

**Status:** Proposta
**Origem:** Revisada na v2
**Data:** 2026-11-24
**Resolvida por:** Spike da Fase 4
**Requisitos relacionados:** RNF-07.5 (extensibilidade)

## 1. Contexto e problema
Extensibilidade é essencial para longevidade, mas plugins inseguros comprometem dados e estabilidade.

## 2. Decisão proposta
- Plugins em **WebAssembly com sandbox** e permissões por capacidade (ler documento, criar camada, acessar rede, etc.), concedidas pelo usuário.
- Sem bibliotecas nativas carregadas dinamicamente.
- API estável e versionada em `contracts/plugin-api/`.
- Todas as ferramentas internas usam a mesma interface `Tool` desde a Fase 2.
- API desenhada na Fase 4, entregue na Fase 8. Crate `plugin-engine` como esqueleto até lá.

## 3. Consequências
- Positivas: segurança por sandbox, portabilidade.
- Negativas: WASM interpretado em iOS. Desempenho limitado vs. nativo.

## 4. Critérios de reavaliação
Se WASM em iOS se provar inviável. Se a performance do sandbox comprometer a experiência.
