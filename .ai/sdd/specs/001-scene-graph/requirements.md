# SPEC-001: Scene Graph — Representação do Documento

**Status:** requirements:draft
**Área:** core
**Release:** R1
**Rigor:** anchored
**Tags:** format, contract
**ADRs:** ADR-006, ADR-007, ADR-013
**Depende de:** — (spec piloto; sem dependências de outras specs)

---

## 1. Visão Geral

Esta spec define a estrutura de dados que representa um documento gráfico híbrido (raster + vetor) em memória e no formato de persistência `.rbsc`. O Scene Graph é a árvore que modela a hierarquia de elementos visuais: documento, páginas (artboards), grupos, camadas raster, nós vetoriais e masks.

## 2. Goals

- Representar documentos com elementos raster e vetoriais em uma hierarquia unificada.
- Permitir composição, agrupamento, ordenação e transformações arbitrárias.
- Servir como base para Undo/Redo (SPEC-003), renderização (SPEC futura) e sincronização (Fase 5).
- Ser serializável no formato `.rbsc` (ADR-007) sem perda.

## 3. Non-Goals

- Sem renderização: o pipeline de composição é de outra spec.
- Sem sincronização: os campos de sync estão no envelope de operação, mas esta spec não envia nada ao servidor.
- Sem colaboração concorrente: bloqueio de camada é da Fase 6.
- Sem UI de múltiplas pranchetas: a árvore já aceita N nós `Artboard` sob o `Document`; a operação de usuário (RF-05.8, Must do R1) é entregue pela SPEC-012 (Composição híbrida).
- Sem plugins de tipos de nós: a interface `Node` é fechada no R1.

## 4. Plataformas e Dispositivos de Referência

| Tier | Plataformas | Release |
|------|-------------|---------|
| 1    | Windows, macOS (Linux melhor esforço) | R1 |
| 2    | iPadOS, Android tablets | R4 |
| 3    | Smartphones, Web | R4 |

Documento de referência: **R-A** (4096×4096, 30 camadas RGBA8), **R-B** (8192×8192, 10 camadas RGBA8).

## 5. User Stories

### US-001 — Criar documento
**Como** artista, **quero** criar um novo documento definindo dimensões, resolução e perfil de cor, **para** começar a trabalhar.
- **AC-001 [BEH]:** Documento criado contém um nó raiz (Document), uma Artboard e uma RasterLayer vazia.
- **AC-002 [BEH]:** Dimensões, DPI e perfil ICC são persistidos e restaurados sem alteração.

### US-002 — Adicionar e organizar camadas
**Como** artista, **quero** criar, duplicar, reordenar e agrupar camadas raster e vetoriais, **para** organizar minha composição.
- **AC-003 [BEH]:** Nós podem ser movidos entre grupos sem perda de propriedades.
- **AC-004 [BEH]:** Reordenação reflete imediatamente na composição (testável com golden image).

### US-003 — Ocultar, bloquear e excluir
**Como** artista, **quero** ocultar, bloquear e excluir elementos, **para** isolar partes do trabalho.
- **AC-005 [BEH]:** Elemento oculto não aparece na composição. Elemento bloqueado não aceita edições.
- **AC-006 [BEH]:** Exclusão é uma operação reversível (Undo restaura o nó e seus descendentes).

### US-004 — Transformações
**Como** artista, **quero** aplicar translação, rotação, escala e espelhamento a qualquer nó, **para** posicionar elementos livremente.
- **AC-007 [BEH]:** Transformações são compostas em ordem (TRS) e herdadas do pai.
- **AC-008 [VIS]:** Composição de grupo com rotação 45° do pai e escala 2× do filho = golden image de referência (tolerância ≤ 2/255).

### US-005 — Modos de mesclagem e opacidade
**Como** artista, **quero** definir modo de mesclagem e opacidade por nó, **para** controlar a composição.
- **AC-009 [BEH]:** Todos os 19 modos de mesclagem do conjunto R1 (decisão D-003) são suportados e serializados sem perda.
- **AC-010 [VIS]:** Overlay de camada vermelha sobre azul = golden image de referência.

## 6. Requisitos Funcionais (EARS + MoSCoW)

### FR-001 (Must) [BEH]
**Cobre:** RF-02.7, RF-05.1, RF-05.2
O SISTEMA DEVE representar o documento como uma árvore de nós tipados: Document, Artboard, Group, RasterLayer, VectorLayer, EmbeddedImage. Mask é um atributo de nó (FR-007), não um nó da árvore.

### FR-002 (Must) [BEH]
**Cobre:** RF-05.3, RF-05.4, RF-05.9
Cada nó DEVE possuir: `node_id` (UUID v7), `parent_id`, `order` (índice fracionário), `name`, `visible`, `locked`, `opacity` (0.0–1.0), `blend_mode`, `transform` (matriz afim 2D 3×2).

### FR-003 (Must) [BEH]
**Cobre:** RF-05.2
QUANDO um nó for movido para dentro de um de seus descendentes, O SISTEMA DEVE rejeitar a operação com erro `CycleDetected`.

### FR-004 (Must) [BEH]
**Cobre:** RF-02.2, RF-02.3
Cada Document DEVE declarar: `width`, `height` (pixels), `dpi`, `color_profile` (ICC embutido ou referência), `bit_depth` (8 ou 16), `blend_space` (perceptual ou linear).

### FR-005 (Must) [BEH]
**Cobre:** RF-03.10, RNF-01.6
RasterLayer DEVE referenciar tiles por coordenada (col, row) e hash de conteúdo. Tiles são 256×256 pixels, RGBA, alfa pré-multiplicado. O tamanho 256×256 é hipótese de engenharia; só pode mudar antes da aprovação do formato `.rbsc` v1.0.0 (spikes (a) e (c)) e, depois dela, apenas com novo `schema_version` maior e migração.

### FR-006 (Must) [BEH]
**Cobre:** RF-04.1, RF-04.5
VectorLayer DEVE conter uma lista ordenada de objetos vetoriais. Cada objeto vetorial DEVE possuir: `shape` (path, rect, ellipse, polygon), `fill`, `stroke`, `transform`.

### FR-007 (Must) [BEH]
**Cobre:** RF-03.8, RF-05.5
Mask DEVE ser aplicável a qualquer nó não-Document. Mask pode ser raster (via tiles) ou vetorial (via shape).

### FR-008 (Must) [BEH]
**Cobre:** RF-05.5
Group DEVE compor seus filhos isoladamente quando possuir blend_mode diferente de PassThrough (isolamento de grupo).

### FR-009 (Must) [CONF]
**Cobre:** RNF-07.4
O schema da árvore DEVE estar em `contracts/document-format/scene.json` e o CI DEVE validar que toda serialização/deserialização Rust e toda representação futura Java estejam em conformidade com o schema.

### FR-010 (Should) [BEH]
**Cobre:** RF-05.5
O SISTEMA DEVERIA suportar clipping paths vetoriais em qualquer nó.

### FR-011 (Should) [BEH]
**Cobre:** RF-07.3
O SISTEMA DEVERIA permitir referência a assets externos (imagens incorporadas) como nós `EmbeddedImage` com hash e dimensões.

### FR-012 (Could) [BEH]
**Cobre:** RF-05.6
O SISTEMA PODE suportar adjustment layers (nós que aplicam filtro aos nós abaixo) como tipo futuro.

## 7. Requisitos Não Funcionais

### NFR-001 [PERF]
**Cobre:** RNF-01.1
Travessia completa da árvore para composição de R-A (30 camadas) DEVE completar em ≤ 1 ms no desktop de referência.

### NFR-002 [PERF]
**Cobre:** RNF-01.5
Abertura e deserialização de R-A DEVE completar em ≤ 500 ms (parsing da árvore, sem decodificação de tiles).

### NFR-003 [BEH]
**Cobre:** RNF-07.6
O schema DEVE ser versionado (`schema_version` semver). Versões antigas DEVEM ser legíveis por código atual. Incompatibilidades DEVEM gerar erro legível, nunca corrupção silenciosa.

## 8. Restrições

- A árvore NÃO DEVE ter ciclos (FR-003).
- Os nós NÃO DEVEM conter referência ao pipeline de renderização.
- A árvore DEVE ser serializável em JSON e em SQLite (ADR-007).
- Tiles NÃO DEVEM ser duplicados: identificação por hash (content-addressable).

## 9. Decisões de Produto

- **D-001:** Índices fracionários para ordenação, compatíveis com a estratégia de merge (ADR-009).
- **D-002:** Alfa pré-multiplicado em todos os pixels raster (ADR-013).
- **D-003:** Conjunto R1 de modos de mesclagem = 16 modos do W3C Compositing and Blending Level 1 (Normal, Multiply, Screen, Overlay, Darken, Lighten, ColorDodge, ColorBurn, HardLight, SoftLight, Difference, Exclusion, Hue, Saturation, Color, Luminosity) + `DestinationIn` e `DestinationOut` (necessários para máscaras) + `PassThrough` (modo de grupo não isolado). O mapeamento exato para os valores `composite-op` do OpenRaster é definido e testado na SPEC-013 (Import/Export). Modos fora deste conjunto (Plus, Dissolve, LinearBurn, VividLight etc.) ficam fora do R1.

## 10. Implementation FAQ

- **Q-001:** E se a árvore ficar muito profunda? **R:** Limite prático de 64 níveis. Acima disso, a operação de agrupamento retorna erro.
- **Q-002:** Como ordenar nós que acabaram de ser criados entre dois irmãos? **R:** Índice fracionário calculado como ponto médio dos vizinhos. Se atingir precisão mínima, rebalancear toda a lista de irmãos.
- **Q-003:** EmbeddedImage é uma camada ou um nó em VectorLayer? **R:** Nó próprio no nível da árvore (como RasterLayer), não dentro de VectorLayer.
- **Q-004:** E os efeitos (sombra, brilho)? **R:** Fora do R1. A árvore tem campo `effects: Vec<Effect>` reservado mas vazio.
- **Q-005:** Qual é o conjunto de modos de mesclagem do R1 e de onde ele vem? **R:** Ver D-003. A base é o W3C Compositing and Blending Level 1, no qual o OpenRaster define seus `composite-op`; a SPEC-013 valida o mapeamento contra a especificação OpenRaster vigente.
- **Q-006:** O que acontece com um `node_id` no corte de limite de profundidade ao importar documento externo? **R:** A importação rejeita árvores com profundidade > 64 e informa no relatório de importação (ADR-016); nenhum nó é descartado em silêncio.

## 11. Métricas de Sucesso

- 100% dos documentos do corpus de teste abrem sem erro.
- 0 falhas de round-trip (serializar → deserializar → serializar = idêntico).
- Conformance suite Rust passa 100%.

## 12. Riscos

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Schema evolui e quebra documentos existentes | Perda de dados do usuário | Versionamento + migração + corpus de compatibilidade |
| Árvore muito grande para mobile | OOM em tablets | Lazy loading de subárvores + limite de profundidade |
| Índices fracionários perdem precisão | Ordenação incorreta | Rebalanceamento periódico |

## 13. Exemplos Concretos

### Documento mínimo
```json
{
  "schema_version": "1.0.0",
  "document": {
    "node_id": "019...",
    "width": 4096,
    "height": 4096,
    "dpi": 300,
    "color_profile": "sRGB IEC61966-2.1",
    "bit_depth": 8,
    "blend_space": "perceptual",
    "children": [
      {
        "type": "Artboard",
        "node_id": "019...",
        "name": "Prancheta 1",
        "children": [
          {
            "type": "RasterLayer",
            "node_id": "019...",
            "name": "Background",
            "order": "a0",
            "opacity": 1.0,
            "blend_mode": "Normal",
            "visible": true,
            "locked": false,
            "tiles": {}
          }
        ]
      }
    ]
  }
}
```

### Detecção de ciclo
| Ação | Resultado |
|------|-----------|
| Mover grupo A para dentro do grupo B (B não é descendente de A) | Aceito |
| Mover grupo A para dentro do grupo C (C é filho de A) | Rejeitado: CycleDetected |
| Mover grupo A para dentro de si mesmo | Rejeitado: CycleDetected |
