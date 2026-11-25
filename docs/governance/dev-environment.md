# Ambiente de desenvolvimento

**Versão:** 0.1
**Data:** 2026-11-25
**Status:** Rascunho para aprovação
**Dono:** PMO

O que instalar para trabalhar no Rabisco, por papel, e as armadilhas conhecidas. Complementa o [tech-stack.md](../../.ai/steering/tech-stack.md), que diz **por que** cada tecnologia foi escolhida; este documento diz **o que baixar**.

> **Versões.** O tech-stack manda registrar as versões usadas nos spikes e só então definir os mínimos. Enquanto os spikes não rodam, a coluna "Versão" mostra a que **foi usada** em 2026-11-25 (ou "a definir"), nunca um mínimo garantido. Ao fechar cada spike, atualize a linha e a seção "Versões mínimas" do tech-stack no mesmo PR.

## 1. Para todas as pessoas (documentação e governança)
Basta isto para escrever specs, abrir PRs e rodar `make verify`.

| Ferramenta | Versão usada | Para quê | Instalar |
|---|---|---|---|
| Git | 2.48 | Controle de versão | [git-scm.com](https://git-scm.com) |
| GitHub CLI (`gh`) | 2.103 | PRs, issues, rulesets e scripts de `tools/github/` | `winget install GitHub.cli` · `brew install gh` |
| Python 3 | 3.14 local; **o CI usa 3.12** | Todos os scripts de `tools/` | [python.org](https://www.python.org) |
| actionlint | 1.7.12 | Valida os workflows (`make lint-workflows`; o CI também roda) | `winget install rhysd.actionlint` · `brew install actionlint` |
| shellcheck | 0.11 | Usado pelo actionlint nos scripts `run:` | `winget install koalaman.shellcheck` · `brew install shellcheck` |
| `make` | qualquer | Atalhos (`make verify`, `make new-spec`, `make new-entry`) | macOS e Linux já trazem. **No Windows não há `make`**: use os comandos `python` da seção 5 |

Todos usam só a biblioteca padrão do Python; não há `pip install`.

## 2. Core e spikes (Rust)
| Ferramenta | Versão | Para quê | Instalar |
|---|---|---|---|
| Rust (via `rustup`) | rustup 1.29; toolchain *stable*, a definir | Core, motor gráfico, spikes a, c e d | `winget install Rustlang.Rustup` · [rustup.rs](https://rustup.rs) |
| Compilador C/C++ | a definir | O Rust precisa de um *linker* | **Windows:** Visual Studio Build Tools 2022 com a carga "Desenvolvimento para desktop com C++" (`winget install Microsoft.VisualStudio.2022.BuildTools --override "--passive --wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"`). **macOS:** `xcode-select --install`. **Linux:** `build-essential` |
| GPU com driver recente | — | Spike a (wgpu): DX12 e Vulkan no Windows, Metal no macOS | Atualize o driver do fabricante |
| Navegador com WebGPU | Chrome 158 usado | Spikes a, c (SQLite WASM com OPFS) e e | [google.com/chrome](https://www.google.com/chrome) |

## 3. Clientes (Flutter) e web
| Ferramenta | Versão | Para quê | Instalar |
|---|---|---|---|
| Flutter SDK | a definir pelo spike b | UI desktop e mobile | [docs.flutter.dev](https://docs.flutter.dev/get-started/install) |
| Mesa digitalizadora ou tablet com caneta | — | Spike b (latência de caneta) | Hardware; sem ele o spike b não fecha |
| Node.js | 24 (LTS em uso) | Spike e e, futura UI web (React + TypeScript) | `winget install OpenJS.NodeJS.LTS` · [nodejs.org](https://nodejs.org) |

## 4. Backend (Java + Spring Boot)
| Ferramenta | Versão | Para quê | Instalar |
|---|---|---|---|
| JDK | 21 LTS (instalado: 21 e 25); a SPEC-022 define o mínimo | Backend modular monolith | [adoptium.net](https://adoptium.net) |
| Maven | a definir pela SPEC-022 | Build do backend | [maven.apache.org](https://maven.apache.org) |
| Docker | a definir | PostgreSQL e demais serviços locais | [docker.com](https://www.docker.com) |

PostgreSQL, Redis e RabbitMQ **não** se instalam direto: o PostgreSQL entra via Docker; Redis e RabbitMQ estão adiados (tech-stack, regra 4).

## 5. Armadilhas conhecidas
- **Sem `make` no Windows.** Equivalentes: `python tools/sdd/generate.py`, `python tools/sdd/sdd_check.py --strict`, `python -m unittest discover -s tools/github/tests` e `-s tools/sdd/tests`, `python tools/sdd/new_entry.py`.
- **UTF-8.** No Windows, rode com `PYTHONUTF8=1`; sem isso, os testes de `tools/sdd` falham por codificação do console.
- **Python do CI é o 3.12.** Não use APIs do 3.13 em diante (por exemplo, `Path.read_text(newline=...)` já quebrou o CI).
- **Instaladores que pedem administrador** (Build Tools do Visual Studio) mostram um aviso do Windows (UAC). Se ele for ignorado, o instalador sai com o código `1602` (cancelado): rode o comando você mesma, num terminal, e aceite o aviso.
- **PATH.** Depois de instalar uma ferramenta, abra um terminal novo; o terminal aberto antes não a enxerga.
- **Finais de linha.** Com `core.autocrlf=true` (padrão do Git para Windows), os arquivos ficam CRLF na pasta e LF no repositório. Ao editar scripts, preserve o final de linha do arquivo.
- **Licenças.** Nenhuma biblioteca entra sem verificação de licença (tech-stack, regra 1). Ferramentas de desenvolvimento acima são só utilitários e não entram no produto.

## 6. Como manter
- Uma pessoa nova segue o [checklist de onboarding](../templates/onboarding-checklist-template.md) e instala só o que o seu papel pede (seções 1 a 4).
- Mudou uma versão, uma ferramenta ou um passo de instalação? Atualize a tabela no mesmo PR. O que for decisão técnica (trocar uma tecnologia) vai para ADR, não para cá.
