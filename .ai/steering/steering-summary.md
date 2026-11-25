# Resumo do steering (steering-summary)

Roteador de `.ai/steering/`: o contexto técnico permanente do projeto, lido por pessoas e por agentes de IA. **Uma linha por documento.**

**Como manter:** o `sdd-check` exige que todo `.md` desta pasta apareça aqui. Mudar o steering é decisão de arquitetura (CODEOWNERS: arquitetos).

| Documento | O que é | Quando consultar |
|---|---|---|
| [product.md](product.md) | Visão, público-alvo, personas, releases, MVP e escopo negativo | Para entender o que o produto é e o que não é |
| [principles.md](principles.md) | Resumo dos princípios inegociáveis (P-01 a P-11); a versão completa é a [constituição](../../docs/constitution.md) | Antes de qualquer decisão de arquitetura |
| [tech-stack.md](tech-stack.md) | Stack tecnológica, cada escolha com o motivo e a ADR correspondente, e as regras de adoção de bibliotecas | Antes de propor uma tecnologia ou dependência |
| [conventions.md](conventions.md) | Nomenclatura, direção das dependências, commits, PRs, `make verify` e quando uma mudança precisa de spec | Ao escrever código ou abrir PR |
| [core.md](core.md) | Convenções do core Rust e do motor gráfico: crates, arestas permitidas e regras | Ao trabalhar em `core/` |
| [backend.md](backend.md) | Convenções do backend Java: modular monolith em Spring Boot | Ao trabalhar em `backend/` (a partir do R2) |
| [clients.md](clients.md) | Convenções de Flutter, React e pontes: UIs finas sobre o core Rust | Ao trabalhar em `clients/` |
| [quality.md](quality.md) | Golden images, benchmarks, dispositivos de referência e corpus de compatibilidade | Ao definir testes e metas de desempenho |

O arquivo [AGENTS.md](../../AGENTS.md), na raiz, resume as regras que valem em toda sessão e aponta para estes documentos.
