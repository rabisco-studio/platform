# Constitution — Rabisco

> Princípios inegociáveis do projeto. Nenhuma spec, ADR ou PR pode contradizê-los.
> Alterações exigem aprovação unânime dos arquitetos e do Product Owner.

## Princípios

### P-01 — Independência do core

O core Rust **não** depende de UI (Flutter, React), backend (Spring Boot, PostgreSQL) ou de qualquer provedor de nuvem. Verificável por análise de dependências no CI.

### P-02 — Persistência local primeiro

Uma alteração do usuário só é considerada "salva" depois de persistida localmente. A confirmação visual de salvamento **nunca** antecede a escrita em disco.

### P-03 — Operações imutáveis e idempotentes

Toda alteração é representada como uma operação imutável com identificador único. Reaplicar a mesma operação não tem efeito. Undo é uma nova operação inversa — nunca trunca nem altera o log.

### P-04 — Tiles como autoridade do pixel

Os tiles armazenados são a fonte definitiva do conteúdo raster. A repetição de traços (replay) **nunca** é usada como fonte do pixel. Resultados podem diferir entre GPUs; os tiles resolvem essa ambiguidade.

### P-05 — Servidor como ordenador, não como intérprete

O servidor ordena operações (atribui sequência), verifica permissões e distribui. Ele **não** interpreta a cena, não aplica semântica gráfica e não renderiza. A lógica do documento vive exclusivamente no core Rust.

### P-06 — Contratos como fonte única

Todo contrato público (API, eventos, formato do documento, plugin API) tem schema em `contracts/` e teste de conformidade executado no CI. Divergência entre implementações quebra o build.

### P-07 — Evolução controlada do formato

Toda mudança no schema do `.rbsc` traz versão explícita, migração para frente e um arquivo no corpus de compatibilidade (`tests/compat/`). Nenhuma versão anterior do formato pode deixar de abrir.

### P-08 — Composição no espaço declarado

A composição de camadas acontece no espaço de trabalho (color space) declarado pelo documento. O perfil ICC é embutido e preservado em todas as operações de salvar, exportar e reabrir.

### P-09 — Entrada prevista é transitória

A predição de entrada (input prediction) é desenhada em overlay transitório e **nunca** persiste em tiles, no log de operações ou no formato do documento. Pontos previstos são descartados e substituídos pelos reais.

### P-10 — Permissões verificadas no servidor

Toda operação sensível (criar, editar, compartilhar, excluir) tem permissão verificada no servidor. O cliente **nunca** é a autoridade de permissão em cenários online.

### P-11 — Na dúvida, está fora do escopo

Se há dúvida sobre uma feature estar ou não no escopo da release atual, ela está fora. Escopo cresce por decisão explícita, com spec, e não por interpretação generosa de um requisito existente.

---

## Verificação no CI

| Princípio | Verificação automatizada |
|-----------|--------------------------|
| P-01 | Análise de dependências dos crates do core (`deny.toml` ou script equivalente) |
| P-02 | Teste de falha durante salvamento: interrupção forçada não perde dados confirmados |
| P-06 | Conformance suite em Rust e Java; diff de schemas no PR |
| P-07 | Corpus em `tests/compat/` aberto a cada build |
| P-08 | Golden images com perfis diferentes (sRGB, Display P3) |
| P-09 | Nenhum campo de predição no schema de operações ou tiles |

Princípios sem verificação automatizada direta (P-03, P-04, P-05, P-10, P-11) são verificados por revisão de código e pelo `sdd-check`.

---

**Atribuição:** Princípios extraídos e formalizados a partir da proposta v1 e da avaliação SDD do projeto.
