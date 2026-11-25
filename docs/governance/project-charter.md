# Termo de Abertura do Projeto (Project Charter)

**Versão:** 0.1
**Data:** 2026-11-25
**Status:** Rascunho para aprovação
**Dono:** Patrocinador / PO

## 1. Propósito
Construir o **Rabisco**, uma plataforma de arte digital híbrida (raster + vetor) com núcleo em Rust, motor gráfico wgpu/WGSL, clientes Flutter (desktop/mobile) e React/WASM (web), backend Java/Spring Boot e armazenamento local SQLite. Fonte da visão: [product.md](../../.ai/steering/product.md).

## 2. Método
Desenvolvimento **waterfall por fases com portões formais**, executado via Spec-Driven Development (SDD). Nenhum código de produção é escrito antes da aprovação de requisitos, design e tarefas da spec correspondente ([constituição](../constitution.md); [fluxo da equipe](team-workflow.md)).

## 3. Escopo por release
| Release | Fases | Entrega |
|---|---|---|
| R1 Local Studio | 1–4 | Editor híbrido desktop, offline, formato `.hybrid`, undo, import/export |
| R2 Cloud | 5 | Contas, biblioteca, versões, sincronização |
| R3 Collab | 6 | Compartilhamento, colaboração em tempo real, comentários |
| R4 Everywhere | 7 | Mobile, web, acessibilidade, i18n |
| R5 Pro | 8 | Plugins, PSD, CMYK, editor de pincéis, filtros e tipografia avançados |

A Fase 0 (fundações + spikes a–e) precede todas. Cronograma: [schedule-wbs.md](schedule-wbs.md).

## 4. Fora do escopo desta baseline
Implementação de código, infraestrutura em nuvem, definição de preços, publicação em lojas. Estimativas de esforço são **hipóteses** até os spikes.

## 5. Critérios de sucesso (hipóteses a validar nos spikes)
Latência de caneta p95 ≤ 30 ms; 60 fps; abrir documento R-A em ≤ 2 s; commit p95 ≤ 100 ms; 0 corrupções em 1.000 interrupções forçadas. Detalhe: [quality.md](../../.ai/steering/quality.md).

## 6. Premissas e restrições
Hardware de referência ainda "a definir" (DEC-004); metas numéricas são hipóteses; o método-fonte exige atribuição ([ATTRIBUTION.md](../../ATTRIBUTION.md)).

## 7. Aprovações
| Papel | Nome | Data | Assinatura |
|---|---|---|---|
| Patrocinador / PO | _a preencher_ | | |
| Arquiteto-chefe | _a preencher_ | | |
