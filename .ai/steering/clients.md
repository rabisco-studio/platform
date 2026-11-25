# Clients — Convenções de Flutter, React e Pontes

## Princípio

As UIs são **finas**: o `application core` em Rust expõe estado de ferramentas, modelos de painéis, comandos e consultas. As interfaces só desenham e encaminham eventos. Quanto mais comportamento no Rust, menos duplicação.

## Flutter (desktop e mobile)

### Plataformas
- Tier 1 (R1): Windows e macOS.
- Tier 2 (R4): iPadOS e tablets Android.
- Linux: melhor esforço.

### Ponte com o core
- `flutter_rust_bridge` — a confirmar no spike (b).
- Tipos de fronteira definidos em `core-domain` com `Serialize`/`Deserialize`.
- Nenhuma lógica de domínio no Dart.

### Integração GPU
- O core renderiza via wgpu. O Flutter exibe a textura resultante.
- Três caminhos a testar no spike (b):
  1. Textura compartilhada entre wgpu e Flutter.
  2. Superfície nativa embutida no Flutter (PlatformView).
  3. Shell nativo puro com Flutter apenas nos painéis.
- **Critério de aprovação:** sobrecarga p95 ≤ 8 ms sobre a linha de base nativa.

### Entrada de caneta
- Eventos de pressão, inclinação, azimute e velocidade encaminhados ao `input-engine`.
- Latência total p95 ≤ 30 ms (meta 20 ms em tablets de ponta).
- O caminho de eventos Flutter → Rust é o gargalo a medir no spike (b).

### Interface
- Painéis, menus e diálogos em Flutter.
- Canvas é a textura do core — Flutter não desenha sobre ela.
- Design tokens compartilhados em JSON (`contracts/design-tokens/`).
- Adaptação por dispositivo: desktop prioriza painéis e atalhos; tablet prioriza canvas e gestos.

## React + TypeScript (web)

### Decisão condicional (ADR-004)
A web entra no R4. A decisão final entre Flutter web e React depende do spike (e):
- Se Flutter web atender aos critérios (tamanho, TTI, latência, acessibilidade): **UI única** com Flutter.
- Caso contrário: **React** sobre o core em WebAssembly.

### Critérios do spike (e)
- Tamanho do bundle inicial.
- Tempo até interação (TTI).
- Latência de entrada.
- Acessibilidade (teclado, screen readers).
- Entrada por teclado e atalhos.

### Core na web
- WebAssembly via `wasm-bindgen`.
- WebGPU (preferido) com fallback WebGL2 reduzido.
- SQLite em WebAssembly com OPFS (ou IndexedDB como alternativa).
- Threads em WASM exigem cabeçalhos COOP e COEP.

### Três níveis de suporte web
1. **Completo:** WebGPU disponível — experiência completa.
2. **Reduzido:** WebGL2 — sem algumas features avançadas de rendering.
3. **Sem edição:** abaixo de WebGL2 — somente visualização.

## Design tokens compartilhados

Cores, espaçamentos e tipografia em JSON em `contracts/design-tokens/`, usados por Flutter e React.

## Testes de UI

- Specs de comportamento únicas: os mesmos critérios de aceitação valem para as duas UIs.
- Testes E2E verificam cada UI contra a spec.
- O build de **todas as plataformas-alvo** fica verde no CI desde a Fase 1, mesmo sem UI completa.
