# SPEC-002: Formato `.hybrid` e Ciclo de Vida do Documento — Criação, Abertura, Salvamento, Recuperação e Migração

**Status:** requirements:draft
**Área:** core
**Release:** R1
**Rigor:** anchored
**Tags:** format, contract
**ADRs:** ADR-007, ADR-008, ADR-013
**Depende de:** SPEC-001 (registros de cena); SPEC-003 (DTO `OpRecord`). Spec de fronteira com a SPEC-003 (dois arquitetos aprovadores)

---

## 1. Visão Geral

Esta spec define como o usuário cria, abre, salva e recupera documentos no formato `.hybrid`. Abrange o autosave, a proteção contra queda abrupta e o ciclo completo de persistência local — sem nuvem (Fase 5).

## 2. Goals

- Garantir que nenhum trabalho confirmado seja perdido, mesmo com queda abrupta (kill -9, falta de energia).
- Autosave transparente: o usuário nunca precisa "salvar" manualmente durante a edição.
- Abertura rápida: primeiro quadro visível de R-A ≤ 2 s.
- Suportar o formato `.hybrid` como SQLite (edição) e ZIP bundle (compartilhamento).

## 3. Non-Goals

- Sem sincronização com a nuvem: cópias locais apenas.
- Sem versionamento de snapshots na nuvem: entra no R2.
- Sem exportação para outros formatos (PNG, SVG, ORA etc.): coberta na SPEC-013 (Import/Export).
- Sem política de cache e remoção de tiles sob pressão de memória: SPEC-006. Esta spec entrega apenas a leitura progressiva e um cache limitado simples.
- Sem coleta de lixo de tiles e assets: spec futura de compactação.
- Sem "Save As" para renomear o SQLite em uso (cópia + abertura do novo).

## 4. Plataformas e Dispositivos de Referência

Mesmas de SPEC-001.

## 5. User Stories

### US-001 — Criar documento novo
**Como** artista, **quero** criar um documento com dimensões, DPI e perfil de cor, **para** começar a trabalhar.
- **AC-001 [BEH]:** Arquivo `.hybrid` é criado no sistema de arquivos com schema válido.
- **AC-002 [BEH]:** Documento abre imediatamente após criação com uma camada raster vazia.

### US-002 — Abrir documento existente
**Como** artista, **quero** abrir um arquivo `.hybrid` previamente salvo, **para** continuar a edição.
- **AC-003 [PERF]:** Primeiro quadro de R-A visível em ≤ 2 s no desktop de referência.
- **AC-004 [BEH]:** Schema version verificada. Documento com versão futura exibe erro legível.

### US-003 — Autosave
**Como** artista, **quero** que minhas alterações sejam salvas automaticamente, **para** não perder trabalho.
- **AC-005 [PERF]:** Confirmação local p95 ≤ 100 ms após o fim do traço.
- **AC-006 [BEH]:** Nenhum prompt de "deseja salvar?" ao fechar — o documento está sempre salvo.

### US-004 — Recuperação após queda
**Como** artista, **quero** reabrir meu documento intacto após uma queda do aplicativo, **para** não perder nada.
- **AC-007 [BEH]:** 0 corrupções em 1.000 interrupções forçadas (kill -9 durante escrita).
- **AC-008 [BEH]:** Ao reabrir, documento está na última transação confirmada.

### US-005 — Exportar como bundle (.hybrid.zip)
**Como** artista, **quero** exportar meu documento como um pacote para enviar a alguém, **para** compartilhar offline.
- **AC-009 [BEH]:** Bundle contém SQLite + tiles + manifesto. Destinatário abre sem erro.
- **AC-010 [BEH]:** Importar bundle recria o SQLite localmente.

### US-006 — Salvar em fundo de tela (mobile)
**Como** artista em tablet, **quero** que ao sair do app minhas alterações estejam salvas, **para** não perder o traço em andamento.
- **AC-011 [BEH]:** Ao ir para background, commit imediato das operações pendentes antes de ceder controle.

## 6. Requisitos Funcionais (EARS + MoSCoW)

### FR-001 (Must) [BEH]
**Cobre:** RF-02.1
O SISTEMA DEVE criar um arquivo SQLite em modo WAL com o schema de `contracts/document-format/hybrid-schema-v1.sql` (tabelas `file_meta`, `document_meta`, `nodes`, `tiles`, `tile_refs`, `assets`, `oplog`) ao criar um documento novo.

### FR-002 (Must) [BEH]
**Cobre:** RF-02.4, RNF-02.6
QUANDO o usuário abrir um arquivo `.hybrid`, O SISTEMA DEVE verificar `schema_version` e `PRAGMA integrity_check` antes de exibir o conteúdo.

### FR-003 (Must) [BEH]
**Cobre:** RNF-02.2, RNF-02.6
SE `integrity_check` falhar, O SISTEMA DEVE tentar recuperar via WAL replay. SE a recuperação falhar, O SISTEMA DEVE informar o usuário com mensagem legível e sugerir o backup mais recente.

### FR-004 (Must) [BEH]
**Cobre:** RNF-02.1, RF-06.4
QUANDO um traço terminar (ou qualquer operação for confirmada), O SISTEMA DEVE persistir a operação e os tiles alterados em uma única transação SQLite ANTES de informar que o documento foi salvo.

### FR-005 (Must) [BEH]
**Cobre:** RF-02.8, RNF-02.2
SE o processo for encerrado durante uma transação SQLite, O SISTEMA DEVE, ao reabrir, recuperar na última transação confirmada pelo WAL, sem tiles corrompidos.

### FR-006 (Must) [PERF]
**Cobre:** RNF-01.5
Abertura de R-A: primeiro quadro visível ≤ 2 s. Carregamento progressivo: tiles visíveis no viewport primeiro, restantes em background.

### FR-007 (Must) [PERF]
**Cobre:** RNF-02.1
Confirmação local p95 ≤ 100 ms após o fim do traço no dispositivo de referência desktop.

### FR-008 (Must) [BEH]
**Cobre:** RF-02.8
QUANDO a aplicação receber sinal de ida para segundo plano (mobile), O SISTEMA DEVE commitar todas as operações pendentes antes de ceder controle ao sistema operacional.

### FR-009 (Should) [BEH]
**Cobre:** RNF-02.4
O SISTEMA DEVERIA manter um backup periódico do arquivo SQLite (cópia de segurança a cada N minutos, configurável).

### FR-010 (Should) [BEH]
**Cobre:** RF-02.5
O SISTEMA DEVERIA suportar "Save As" como cópia do arquivo SQLite atual para novo caminho, seguida de abertura do novo arquivo.

### FR-011 (Must) [BEH]
**Cobre:** RF-07.7
Exportação para bundle: O SISTEMA DEVE gerar um arquivo ZIP contendo o SQLite (snapshot sem WAL), manifesto JSON com schema_version, e todos os tiles referenciados.

### FR-012 (Must) [BEH]
**Cobre:** RF-07.7
Importação de bundle: O SISTEMA DEVE extrair o ZIP, validar a integridade e abrir o SQLite como novo documento local.

### FR-013 (Must) [BEH]
**Cobre:** RNF-07.6
QUANDO o usuário abrir um `.hybrid` cuja `schema_version` for anterior à atual, O SISTEMA DEVE criar uma cópia de segurança do arquivo original, executar as migrações registradas em sequência dentro de uma única transação e só então abrir o documento. SE qualquer migração falhar, O SISTEMA DEVE manter o arquivo original intacto e informar o erro.

## 7. Requisitos Não Funcionais

### NFR-001 [BEH]
**Cobre:** RNF-02.5
0 operações confirmadas perdidas em qualquer cenário de falha testável.

### NFR-002 [PERF]
**Cobre:** RNF-01.6
Memória de trabalho para R-A ≤ 1,5 GB com remoção de tiles sob pressão (a política de remoção é da SPEC-006; esta spec garante o limite do cache de leitura).

### NFR-003 [BEH]
**Cobre:** RNF-07.6
Compatibilidade retroativa: todo `.hybrid` de versão anterior DEVE abrir na versão atual.

## 8. Restrições

- SQLite modo WAL obrigatório (ADR-007).
- Nenhuma escrita fora da transação.
- Tiles comprimidos com zstd no armazenamento.

## 9. Decisões de Produto

- **D-001:** Sem prompt "deseja salvar?" — autosave sempre.
- **D-002:** Bundle = ZIP com extensão `.hybrid.zip`.
- **D-003:** Backup local desligado por padrão. Ativável nas preferências.

## 10. Implementation FAQ

- **Q-001:** O que acontece se o disco encher durante a escrita? **R:** A transação falha, SQLite reverte, e o app exibe erro com espaço disponível.
- **Q-002:** E se o WAL file ficar muito grande? **R:** Checkpoint automático quando o WAL exceder 10 MB. Configurável.
- **Q-003:** Qual compressor para tiles? **R:** zstd level 3 (balanço velocidade/tamanho). Avaliado no spike (c).
- **Q-004:** E na web (WASM + OPFS)? **R:** SQLite compilado para WASM via sqlite-wasm com OPFS backend. Validado no spike (c).
- **Q-005:** O formato prevê mipmaps de tiles? **R:** Não no R1. `tile_refs` já inclui a coluna `mip` (sempre 0 no R1), para que mipmaps não exijam migração destrutiva (ADR-007).
- **Q-006:** Quem é dono do DDL? **R:** Somente esta spec. Outras specs definem registros em memória (`NodeRecord`, `OpRecord`) e referenciam o arquivo `hybrid-schema-v1.sql`.

## 11. Métricas de Sucesso

- 0 corrupções no teste de 1.000 interrupções.
- Abertura de R-A ≤ 2 s.
- Autosave p95 ≤ 100 ms.
- Round-trip de bundle: exportar → importar → exportar = idêntico.

## 12. Riscos

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| WAL file growth em edições longas | Lentidão | Checkpoint periódico |
| OPFS não disponível em todos os navegadores | Web não funciona | Verificar no spike (c); fallback: download/upload |
| zstd lento em mobile | Autosave excede 100 ms | Testar nos spikes (b) e (c); alternativa: lz4 |
| Migração de schema falha em arquivo real do usuário | Perda de acesso ao documento | Backup pré-migração obrigatório (FR-013) e corpus em `tests/compat/` |
