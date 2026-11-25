# Conventions — Rabisco

## Idioma

- Texto das specs e documentação: **português**.
- Identificadores canônicos, nomes de arquivos, caminhos, estados de gate e código: **inglês**.
- Exemplos: `US-001`, `FR-001`, `requirements:approved`, `scene-engine`, `op_id`.

## Nomenclatura

### Crates Rust
- Nomes em `kebab-case`: `document-engine`, `raster-engine`.
- Módulos internos em `snake_case`.
- Tipos públicos em `PascalCase`, funções e métodos em `snake_case`.
- Erros como enums tipados, nunca strings soltas.

### Módulos Java (backend)
- Packages em `com.rbsc.platform.<modulo>`.
- Classes em `PascalCase`, métodos em `camelCase`.
- DTOs gerados a partir dos contratos em `contracts/api/`.

### Flutter e React
- Componentes em `PascalCase`.
- Arquivos em `snake_case` (Flutter/Dart) e `kebab-case` (React/TypeScript).
- Nenhuma lógica de domínio nas UIs: tudo vem do core via bridge.

## Dependências

### Direção obrigatória

```
UI (Flutter/React) → Application Core → Engines → Core Domain
                                                       ↑
                                              Sem dependência para cima
```

- O core **nunca** importa Flutter, React, Spring Boot, PostgreSQL ou provedor de nuvem (P-01).
- Arestas permitidas: [crates.toml](../../docs/architecture/crates.toml) (fonte única). Verificação automatizada no CI com `cargo deny` ou script equivalente lendo esse arquivo.

### Clientes gerados

- Clientes REST e WebSocket são **gerados** a partir dos contratos em `contracts/`.
- Clientes gerados **nunca** são editados à mão.

## Commits e PRs

### Mensagens de commit

```
<tipo>(<escopo>): <descrição curta>

[corpo opcional]

[referências: SPEC-NNN, ADR-NNN]
```

Tipos: `feat`, `fix`, `refactor`, `docs`, `test`, `perf`, `ci`, `spike`, `chore`.

### Pull Requests

- Título: `<tipo>(<escopo>): <descrição>`.
- Corpo: referência à spec (`SPEC-NNN`) ou ao spike.
- PR de código de produção **obrigatoriamente** referencia uma spec em `tasks:approved`.
- Checklist obrigatória no modelo de PR:
  - [ ] Spec atualizada se o comportamento mudou.
  - [ ] Testes adicionados/atualizados.
  - [ ] Golden images atualizadas (se aplicável).
  - [ ] Contratos atualizados (se aplicável).
  - [ ] `make verify` passa.

## Verificação do projeto

```bash
make verify
```

Inclui:
1. Formatação e lint sem avisos (`cargo fmt --check`, `cargo clippy`, equivalentes em Java/TS/Dart).
2. Testes unitários e de integração.
3. Conformance suite em Rust e Java.
4. Golden images com tolerância declarada.
5. Regra de dependências do core (P-01).
6. Verificação de licenças.
7. Corpus de compatibilidade do formato.
8. `sdd-check` (gates de spec).

## SDD — Quando uma mudança precisa de spec

| Tipo de mudança | Precisa de spec? |
|----------------|-----------------|
| Feature nova | Sim |
| Mudança em formato, contrato, sync, permissão | Sim (nível anchored) |
| Mudança que afeta mais de uma área (core + backend) | Sim |
| Correção descritível em uma frase | Não — PR com testes |
| Refatoração sem mudança de comportamento | Não — PR com testes |
| Atualização de dependência sem impacto | Não — PR com testes |
| Documentação | Não |
| Spike / experimento | Não — vai em `spikes/`, resultado vira ADR |

**Regra de dúvida:** se toca formato, contrato, segurança, privacidade ou mais de uma área, é spec anchored.

## Quem aprova cada gate

| Gate | Aprovadores |
|------|-------------|
| requirements | Product Owner + arquiteto da área |
| design | Arquiteto de cada área impactada + donos de contrato |
| tasks | Arquiteto da área |
| implementation (PR) | Code owner do código alterado |
| review | Revisor independente + arquiteto da área |

**Regra absoluta:** quem escreve um documento não o aprova. O agente nunca aprova.
