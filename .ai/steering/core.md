# Core — Convenções do Core Rust e Motor Gráfico

## Organização dos crates

| Crate | Responsabilidade |
|-------|-----------------|
| `core-domain` | Entidades e regras do domínio (IDs, tipos primitivos, erros) |
| `document-engine` | Documento, pranchetas e estrutura de alto nível |
| `scene-engine` | Árvore de elementos (Scene Graph) e composição |
| `raster-engine` | Pintura, tiles e manipulação de pixels |
| `vector-engine` | Geometria, paths, formas e texto |
| `render-engine` | Renderização GPU via wgpu e shaders WGSL (composição, overlay, conversão de cor na saída) |
| `brush-engine` | Pincéis, dabs, dinâmica de caneta e predição |
| `input-engine` | Eventos de mouse, toque e caneta; filtro e estabilização |
| `history-engine` | Modelo de operações, Undo/Redo e log |
| `file-engine` | Formato `.rbsc`, serialização, migração e I/O |
| `sync-engine` | Sincronização, reconciliação e protocolo (a partir da Fase 5) |
| `plugin-engine` | Extensibilidade via WASM (esqueleto até Fase 4) |
| `color-engine` | Pipeline de cor, conversão de perfis, espaço de trabalho |

## Regras de dependência

Fonte única: **`docs/architecture/crates.toml`** (arestas permitidas, verificadas no CI por P-01 e pelo `sdd-check` nas specs). Em resumo, de baixo para cima:

| Camada | Crates | Podem depender de |
|--------|--------|-------------------|
| 0 | `core-domain` | nada |
| 1 | `color-engine`, `input-engine`, `scene-engine` | camada 0 |
| 2 | `history-engine`, `raster-engine`, `vector-engine`, `file-engine` | camadas 0–1 (conforme `crates.toml`) |
| 3 | `brush-engine` | `core-domain`, `color-engine`, `input-engine`, `raster-engine` |
| 4 | `render-engine` | camadas 0–3 (exceto `file-engine`, `history-engine`) |
| 5 | `document-engine` | todos os acima: orquestra edição, histórico, render e persistência |
| 6 | `sync-engine` (Fase 5), `plugin-engine` (Fase 8) | conforme `crates.toml` |

Regras adicionais:

- Dependências são acíclicas; uma aresta nova exige alterar `crates.toml` em PR de arquitetura.
- Quem persiste (`file-engine`) não conhece operações nem composição: recebe registros e DTOs de `core-domain` (`NodeRecord`, `OpRecord`).
- Quem edita (`brush-engine`, `history-engine`) não conhece disco nem GPU. A orquestração ocorre em `document-engine`.
- `input-engine`: eventos de entrada, `InputSample`, filtro e estabilização. `brush-engine`: pincéis, dabs, dinâmicas e predição.
- `plugin-engine` depende apenas da interface `Tool` de `core-domain` (dono da interface: ver DEC-013).
- Nenhum crate depende de Flutter, React, Spring Boot, PostgreSQL ou provedor de nuvem (P-01).

## Modelo de erro

- Erros como `enum` tipados em cada crate: `RasterError`, `VectorError`, etc.
- O crate de domínio define o trait `RabiscoError`.
- Na ponte para Dart (flutter_rust_bridge) e WASM (wasm-bindgen): conversão em códigos + mensagens serializadas.
- Nunca `unwrap()` em código de produção. Usar `expect()` somente onde a invariante é provada pelo tipo.

## Tiles

- Tamanho padrão: 256 × 256 pixels (hipótese; confirmada ou ajustada pelos spikes (a) e (c) antes da aprovação do `.rbsc` v1.0.0).
- Hash: blake3, 32 bytes (SPEC-001 TD-002).
- Tipos primitivos de tile (`TileHash`, `TileRef`, `TileData`, trait `TileStore`) vivem em `core-domain`; política de cache e memória em `raster-engine` (SPEC-006).
- Identificados pelo hash do conteúdo (content-addressable).
- Imutáveis: um novo traço gera novos tiles; os antigos são retidos até compactação.
- Formato de pixel: RGBA com alfa pré-multiplicado. Profundidade (8 ou 16 bits) declarada pelo documento.
- Compressão: zstd nível 3 para armazenamento local (hipótese a validar no spike (c); alternativa lz4). Decisão em SPEC-002 TD-002.

## Shaders (WGSL)

- Um shader por estágio: composição de camadas, conversão de cor, dabs de pincel, transformações.
- Precisão: `f32` na GPU. Conversão para `f16` somente se o benchmark exigir em mobile.
- Tolerância visual entre GPUs: ≤ 2/255 por canal (sem pincel), ≤ 4/255 (com pincel).

## FFI e bridges

- **Dart (Flutter):** `flutter_rust_bridge` — a confirmar no spike (b).
- **WebAssembly:** `wasm-bindgen` — a confirmar no spike (a).
- **Java (worker no backend):** JNI ou grpc-bridge — a confirmar na Fase 5.
- Regra: os tipos de fronteira (structs que cruzam a bridge) vivem em `core-domain` e têm `Serialize`/`Deserialize`.

## Testes

- **Unitários:** lógica de domínio, geometria, operações, serialização.
- **Golden images:** composição, cor, blend modes. Tolerância declarada por teste.
- **Benchmarks:** frame time, latência de traço, uso de memória. Executados em runners dedicados.
- **Conformance:** vetores de teste em `contracts/conformance/`.
- **Compatibilidade:** corpus de arquivos `.rbsc` em `tests/compat/`.
