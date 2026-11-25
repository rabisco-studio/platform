# Hybrid Digital Art Platform

Editor gráfico híbrido (raster + vetor), offline-first, multiplataforma.
Contexto completo: @.ai/steering/product.md

## Stack

Resumo e motivos: @.ai/steering/tech-stack.md (leia antes de decisões técnicas)

## Fluxo de desenvolvimento

Este projeto usa **Spec-Driven Development**.

1. Toda feature tem spec em `.ai/sdd/specs/NNN-nome/`.
2. Leia o `.status` da spec **ANTES** de implementar qualquer coisa.
3. Nunca escreva código de produção antes de `tasks:approved`.
4. Ambiguidade: **PARE e pergunte**. A resposta volta para a spec.
5. Spikes ficam em `spikes/` e nunca fecham tarefas de produção.

## Regras que valem em toda sessão

- O core Rust **NUNCA** depende de UI, backend ou provedor de nuvem (P-01).
- Persistir localmente **ANTES** de confirmar qualquer alteração (P-02).
- Contratos públicos só mudam em `contracts/`, com versão e teste de conformidade (P-06).
- O servidor **NUNCA** interpreta a cena: só ordena, autoriza e distribui (P-05).
- Entrada prevista (predição) **NUNCA** vai para tiles nem para o log (P-09).
- Rodar `make verify` antes de declarar uma tarefa concluída.

## Estrutura

```
.ai/steering/     → verdade para o projeto inteiro
.ai/sdd/specs/    → uma spec por feature
contracts/        → schemas e conformance (fonte única)
docs/adr/         → decisões arquiteturais transversais
docs/constitution.md → princípios inegociáveis (P-01 a P-11)
spikes/           → experimentos rotulados; nunca produção
```

## Convenções

Detalhes: @.ai/steering/conventions.md
