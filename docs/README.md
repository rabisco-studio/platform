# Mapa da documentação

Roteador dos roteadores: de onde sair para achar cada assunto. Cada pasta com muitos documentos tem um resumo de **uma linha por documento**; as pastas pequenas têm o próprio README.

| Quero... | Vá para |
|---|---|
| Entender o projeto e o fluxo de trabalho | [README.md](../README.md) (guia de entrada) |
| Ver as specs, uma linha cada | [spec-summary.md](../.ai/sdd/specs/spec-summary.md) |
| Ver o estágio de cada spec | [INDEX.md](../.ai/sdd/INDEX.md) (gerado) |
| Ver o roadmap por releases e fases | [PLAN.md](../.ai/sdd/PLAN.md) |
| Ver as decisões de arquitetura | [adr-summary.md](adr/adr-summary.md) |
| Ver processo, decisões do projeto, riscos e papéis | [governance-summary.md](governance/governance-summary.md) |
| Ler o contexto técnico permanente (steering) | [steering-summary.md](../.ai/steering/steering-summary.md) |
| Ver catálogos, cobertura e rastreabilidade | [requirements-summary.md](requirements/requirements-summary.md) |
| Ver os experimentos da Fase 0 | [spike-summary.md](../spikes/spike-summary.md) |
| Saber o que cada script faz | [tools-summary.md](../tools/tools-summary.md) |
| Saber o que cada workflow do GitHub faz | [workflows/README.md](../.github/workflows/README.md) |
| Escolher um template de documento | [templates/README.md](templates/README.md) (já funciona como roteador) |
| Ver os contratos legíveis por máquina | [contracts/README.md](../contracts/README.md) (já funciona como roteador) |
| Ver quem é dono de cada contrato, tipo e crate | [ownership-matrix.md](architecture/ownership-matrix.md) |
| Ler os princípios inegociáveis | [constitution.md](constitution.md) |
| Ler o diário do projeto | [journal/README.md](../journal/README.md) |

**Regra:** os resumos apontam, não copiam. Status, fase, rigor e cobertura moram nos arquivos de origem (catálogos e arquivos gerados). O `sdd-check` falha se um documento novo não aparecer no resumo da sua pasta.
