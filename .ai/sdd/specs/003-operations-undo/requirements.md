# SPEC-003: Modelo de Operações e Undo/Redo

**Status:** requirements:draft
**Área:** core
**Release:** R1
**Rigor:** anchored
**Tags:** format, contract
**ADRs:** ADR-009, ADR-008
**Depende de:** SPEC-001 (nós e tiles); SPEC-002 (persistência). Spec de fronteira com a SPEC-002 (dois arquitetos aprovadores)

---

## 1. Visão Geral

Esta spec define o envelope de operação, o modelo de Undo/Redo e as regras de persistência. O modelo é preparado para sincronização (Fase 5) mas nesta spec opera somente localmente.

## 2. Goals

- Representar toda alteração como uma operação imutável e idempotente.
- Oferecer Undo/Redo ilimitado na sessão.
- Garantir que operações são persistidas atomicamente (SPEC-002).
- Preparar o envelope para sync futura (campos de relógio e device_id presentes desde o R1).

## 3. Non-Goals

- Sem envio ao servidor: a sincronização é da Fase 5. Os campos de sync estão no envelope mas nenhum código os transmite.
- Sem colaboração: Undo é local ao autor.
- Sem compactação do log de operações (spec futura).
- Sem tratamento de operações remotas, de outros autores ou fora de ordem (D-004).
- Sem operações em lote do usuário (macro de operações): spec futura.

## 4. Plataformas e Dispositivos de Referência

Mesmas de SPEC-001.

## 5. User Stories

### US-001 — Desfazer última ação
**Como** artista, **quero** desfazer minha última ação, **para** corrigir um erro.
- **AC-001 [BEH]:** Undo reverte visualmente a operação. O documento volta ao estado anterior.
- **AC-002 [BEH]:** Operação original permanece no log. Undo é uma nova operação inversa.

### US-002 — Refazer ação desfeita
**Como** artista, **quero** refazer uma ação que desfiz, **para** restaurá-la.
- **AC-003 [BEH]:** Redo aplica novamente a operação desfeita.
- **AC-004 [BEH]:** Se uma nova ação for feita após Undo, o Redo stack é descartado.

### US-003 — Desfazer operação complexa
**Como** artista, **quero** que ao desfazer um "mover grupo", todos os filhos voltem à posição, **para** não ter efeitos parciais.
- **AC-005 [BEH]:** Operações compostas (múltiplos nós afetados) são desfeitas atomicamente.

### US-004 — Idempotência
**Como** sistema de sync (futuro), **quero** que reaplicar a mesma operação não mude o documento, **para** garantir convergência.
- **AC-006 [BEH]:** Operação com op_id já presente é ignorada silenciosamente.

### US-005 — Recuperação do histórico
**Como** artista, **quero** reabrir o documento e ver meu histórico de Undo, **para** continuar desfazendo.
- **AC-007 [BEH]:** O oplog persiste entre sessões. Undo funciona após fechar e reabrir.

## 6. Requisitos Funcionais (EARS + MoSCoW)

### FR-001 (Must) [BEH]
**Cobre:** RF-06.2
O SISTEMA DEVE representar toda alteração como uma operação com envelope: `op_id` (UUID v7), `author_id`, `device_id`, `hlc` (Hybrid Logical Clock), `base_seq` (sequência local), `schema_version`, `op_type`, `targets` (lista de node_ids), `payload`, `inverse`.

### FR-002 (Must) [BEH]
**Cobre:** RF-06.2
Operações DEVEM ser imutáveis: uma vez persistidas, não são alteradas nem removidas do log.

### FR-003 (Must) [BEH]
**Cobre:** RNF-02.5
QUANDO chegar uma operação cujo `op_id` já existe no log, O SISTEMA DEVE ignorá-la sem alterar o documento.

### FR-004 (Must) [BEH]
**Cobre:** RF-06.1
QUANDO o usuário acionar Undo, O SISTEMA DEVE criar uma nova operação contendo o `inverse` da operação mais recente do autor, e aplicá-la.

### FR-005 (Must) [BEH]
**Cobre:** RF-06.1
QUANDO o usuário acionar Redo, O SISTEMA DEVE reaplicar a operação original que havia sido desfeita. SE uma nova operação for executada após Undo, o Redo stack DEVE ser descartado.

### FR-006 (Must) [BEH]
**Cobre:** RF-06.4, RNF-02.1
QUANDO um traço terminar, O SISTEMA DEVE persistir a operação e os tiles alterados em uma única transação local ANTES de informar que o documento foi salvo (referência: SPEC-002 FR-004).

### FR-007 (Must) [BEH]
**Cobre:** RF-06.3
Cada operação DEVE carregar seu `inverse`: dados suficientes para reconstruir o estado anterior sem percorrer o log.

### FR-008 (Must) [BEH]
**Cobre:** RF-06.4, RF-02.8
SE o processo for encerrado durante uma transação, O SISTEMA DEVE reabrir o documento na última transação confirmada (referência: SPEC-002 FR-005).

### FR-009 (Should) [BEH]
**Cobre:** RF-06.3, RF-06.5
ONDE uma operação agrupar múltiplas sub-alterações (ex: mover grupo = mover N nós), O SISTEMA DEVERIA aplicar e desfazer todas atomicamente.

### FR-010 (Must) [CONF]
**Cobre:** RNF-07.4
O schema do envelope de operação DEVE estar em `contracts/document-format/operation.json` e o CI DEVE validar conformidade.

### FR-011 (Must) [BEH]
**Cobre:** RNF-02.5
O Hybrid Logical Clock (HLC) DEVE avançar monotonicamente por device_id. O SISTEMA DEVE rejeitar com erro `StaleHLC` uma operação **nova** (op_id ainda não visto) cujo HLC seja ≤ ao último HLC registrado para o mesmo device_id. A verificação de duplicata (FR-003) é sempre executada antes da verificação de HLC.

## 7. Requisitos Não Funcionais

### NFR-001 [PERF]
**Cobre:** RNF-02.1
Confirmação local p95 ≤ 100 ms após o fim do traço no dispositivo de referência.

### NFR-002 [BEH]
**Cobre:** RNF-02.5
0 operações confirmadas perdidas em qualquer cenário de falha.

### NFR-003 [BEH]
**Cobre:** RF-06.1
Undo de operação de traço raster: restaurar tiles anteriores em ≤ 50 ms (troca de referência no tile store).

## 8. Restrições

- O log de operações é append-only. Nenhuma operação é removida.
- O inverse DEVE conter snapshot dos dados afetados (ex: tiles antigos, propriedades anteriores), não uma referência relativa.
- Tiles referenciados pelo inverse DEVEM ser mantidos no tile store enquanto a operação estiver no log.

## 9. Decisões de Produto

- **D-001:** Undo/Redo ilimitado na sessão (limitado apenas pelo espaço em disco).
- **D-002:** Histórico persiste entre sessões (oplog no SQLite).
- **D-003:** Compactação do log (purge de operações antigas) é spec futura — requer política de retenção.
- **D-004:** As regras desta spec valem para operações geradas **localmente** por um único autor. Chegada de operações remotas (fora de ordem, de outros autores ou dispositivos) é tratada na spec de sincronização (Fase 5).

## 10. Tipos de Operação (R1)

| op_type | Descrição | Payload | Inverse |
|---------|-----------|---------|---------|
| `node.add` | Adicionar nó à árvore | NodeData + parent_id + position | Referência ao nó adicionado (para remoção) |
| `node.remove` | Remover nó (e descendentes) | node_id | Snapshot da subárvore removida |
| `node.move` | Mover nó para outro pai/posição | node_id, new_parent, new_position | parent_id e position antigos |
| `node.set_property` | Alterar propriedade de nó | node_id, prop, new_value | prop, old_value |
| `raster.stroke` | Aplicar traço raster | layer_id, affected_tiles: [(col,row,new_hash)] | affected_tiles: [(col,row,old_hash)] |
| `raster.fill` | Preencher região | layer_id, affected_tiles | affected_tiles antigos |
| `vector.add_object` | Adicionar objeto vetorial | layer_id, VectorObject | object_id (para remoção) |
| `vector.remove_object` | Remover objeto vetorial | layer_id, object_id | Snapshot do VectorObject |
| `vector.modify_object` | Modificar objeto vetorial | layer_id, object_id, changes | changes anteriores |
| `mask.set` | Definir mask | node_id, MaskData | MaskData anterior (ou None) |
| `mask.remove` | Remover mask | node_id | MaskData removida |
| `document.set_meta` | Alterar metadados do doc | changes | valores anteriores |

## 11. Implementation FAQ

- **Q-001:** E se o usuário desfizer duas vezes e fizer uma nova ação? **R:** O Redo stack é descartado. A nova operação é acrescentada ao log. As operações anteriores (incluindo as inversas) permanecem.
- **Q-002:** Duas operações com o mesmo HLC? **R:** Impossível para o mesmo device_id (HLC é monotônico). Para device_ids diferentes (futuro sync), desempate pelo device_id maior.
- **Q-003:** O que acontece com o Undo de uma operação cujo alvo foi excluído por outro usuário? **R:** Decisão: fora do escopo desta spec, porque no R1 há um único autor (ver Non-Goals e D-004). Será especificado na spec de sincronização (Fase 5), que parte do princípio de que a operação inversa restaura o nó e a exclusão do outro usuário permanece no log.
- **Q-004:** O que acontece com tiles antigos referenciados pelo inverse? **R:** Mantidos no tile store. GC futuro (spec de compactação) remove tiles sem referência.
- **Q-005:** Qual o tamanho do inverse de um traço raster? **R:** Referências aos tile hashes antigos (não os pixels). Os tiles antigos já estão no store (content-addressable = nunca duplicados).

## 12. Exemplos Concretos

### Sequência Undo/Redo

| Passo | Ação | Oplog | Undo stack | Redo stack |
|-------|------|-------|------------|------------|
| 1 | Traço A | [stroke_A] | [stroke_A] | [] |
| 2 | Traço B | [stroke_A, stroke_B] | [stroke_A, stroke_B] | [] |
| 3 | Undo | [stroke_A, stroke_B, inv_B] | [stroke_A] | [stroke_B] |
| 4 | Undo | [stroke_A, stroke_B, inv_B, inv_A] | [] | [stroke_B, stroke_A] |
| 5 | Redo | [... , redo_A] | [stroke_A] | [stroke_B] |
| 6 | Traço C | [... , redo_A, stroke_C] | [stroke_A, stroke_C] | [] (descartado) |

### Idempotência

| Cenário | Resultado |
|---------|-----------|
| Operação op_id="abc" aplicada pela primeira vez | Aplicada normalmente |
| Mesma operação op_id="abc" chega novamente | Ignorada. Documento inalterado |
| Operação nova (op_id inédito) com HLC ≤ último HLC do device_id | Rejeitada com erro `StaleHLC` |
| Operação repetida (op_id já visto), mesmo com HLC ≤ último | Ignorada sem erro (duplicata vence a checagem de HLC) |

## 13. Métricas de Sucesso

- 100% das operações do R1 têm inverse testado.
- Undo/Redo round-trip: aplicar → undo → redo = estado idêntico (bit a bit para raster).
- 0 operações perdidas em teste de crash.

## 14. Riscos

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Inverse de traço raster grande | Muitos tiles antigos retidos | GC futuro; tiles são deduplicated |
| Oplog cresce indefinidamente | Arquivo SQLite grande | Spec futura de compactação |
| HLC drift entre dispositivos (futuro) | Ordenação incorreta | NTP + limite de drift no sync (Fase 5) |
