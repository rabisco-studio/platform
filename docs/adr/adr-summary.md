# Resumo das ADRs (adr-summary)

Roteador das decisões de arquitetura: **uma linha por ADR**, com a decisão e o que a resolve. O status de cada ADR (Proposta, Aprovada...) está no [README.md](README.md) desta pasta, que é gerado; aqui não se repete.

**Como manter:** o `sdd-check` exige que toda `ADR-NNN-*.md` desta pasta apareça aqui. Ao criar uma ADR (template [adr-template.md](../templates/adr-template.md)), acrescente a linha e rode `make docs`.

| ADR | Decisão em uma linha | Resolvida por |
|---|---|---|
| [ADR-001](ADR-001-rust-core.md) | Rust como linguagem do core e de todos os engines (raster, vetor, cena, render, pincel, histórico, arquivo, sync) | Spike (a) |
| [ADR-002](ADR-002-wgpu-rendering.md) | wgpu como abstração de renderização, com shaders em WGSL | Spike (a) |
| [ADR-003](ADR-003-flutter-native-clients.md) | Flutter para os clientes nativos, condicionado ao spike (b), que testa três caminhos de integração de GPU | Spike (b) |
| [ADR-004](ADR-004-react-web.md) | Web em React + WebAssembly, condicionada ao spike (e); se o Flutter web bastar, adota-se UI única | Spike (e) |
| [ADR-005](ADR-005-modular-monolith.md) | Backend como modular monolith em Java + Spring Boot, com módulos de interface explícita | Baixo risco |
| [ADR-006](ADR-006-scene-graph.md) | Scene Graph com nós tipados e IDs estáveis como representação do documento | SPEC-001 |
| [ADR-007](ADR-007-rbsc-format.md) | Formato nativo `.rbsc`: SQLite em modo WAL para o trabalho local e bundle ZIP para troca | Spike (c) |
| [ADR-008](ADR-008-offline-first.md) | Offline-first: toda edição é salva localmente antes de qualquer sincronização | SPEC-003 |
| [ADR-009](ADR-009-operations-sync.md) | Sincronização por operações imutáveis e idempotentes com HLC, e regras de conflito por tipo de dado | SPEC-003 |
| [ADR-010](ADR-010-concurrent-collaboration.md) | Single-user com modelo preparado até a Fase 5; na Fase 6, bloqueio cooperativo por camada raster | Spike da Fase 6 |
| [ADR-011](ADR-011-document-versioning.md) | Versionamento por snapshots periódicos mais o log de operações, com retenção configurável | Fase 5 |
| [ADR-012](ADR-012-plugins.md) | Plugins em WebAssembly com sandbox e permissões por capacidade, com API versionada em `contracts/` | Spike da Fase 4 |
| [ADR-013](ADR-013-color-pipeline.md) | Espaço de trabalho com perfil ICC (padrão sRGB), RGBA com alfa pré-multiplicado, 8 ou 16 bits por canal | Spike (d) |
| [ADR-014](ADR-014-contracts-polyglot.md) | Servidor como autoridade de ordem e permissão (não interpreta a cena), worker Rust no backend e contratos como fonte única | Conformance suite |
| [ADR-015](ADR-015-brush-engine.md) | Pincel como definição JSON versionada, com dinâmicas ligadas a pressão, inclinação e velocidade | SPEC-005 |
| [ADR-016](ADR-016-interoperability.md) | Matriz de formatos de importação e exportação por release (PNG, JPEG, WebP, ORA, SVG, PDF) | SPEC-013 |
| [ADR-017](ADR-017-observability.md) | OpenTelemetry, SLIs de sincronização e auditoria separada dos logs de aplicação | Fase 5 |
| [ADR-018](ADR-018-privacy-compliance.md) | Privacidade desde o desenho (LGPD e GDPR): base legal por dado, direitos do titular, controladora e operadora | Revisão jurídica |

Decisões que **não** são de arquitetura (escopo, licença, hardware, nomes) ficam no [decision-log](../governance/decision-log.md), como `DEC-nnn`.
