# Relatório do Spike (c) — Formato .rbsc (SQLite + bundle)

**Data:** 2026-11-25
**Autor:** maria-brito15 (execução e texto com o Claude Code; revisão da autora pendente)
**Revisor:** pendente (precisa ser pessoa diferente do autor)
**Status:** Rascunho
**Plano:** [README.md](README.md)

## 1. Resultado em uma linha
**APROVADO COM RESSALVAS:** o SQLite em modo WAL cumpriu os 3 critérios nativos com folga (0 corrupções em 1.000 interrupções, abertura em ~50 ms, zstd 3 em ≤ 2,6 ms), mas **no navegador o WAL não está disponível** (o SQLite em WASM cai para o diário de reversão), o que obriga a ADR-007 a tratar a web como um modo diferente.

## 2. Ambiente
| Item | Valor |
|---|---|
| Dispositivo / GPU / SO | Notebook Intel Core i7-1355U (10 núcleos, 12 threads), 15,7 GB de RAM, SSD NVMe, Windows 11 Home 10.0.26200, NTFS, Microsoft Defender com proteção em tempo real ativa |
| Versões | Rust 1.100.0 (MSVC), SQLite 3.54.1 (embutido via `rusqlite` 0.43 / `libsqlite3-sys` 0.40), `zstd` 0.14.5 (zstd 1.6.0), `lz4_flex` 0.14.2, `blake3` 1.8.7; `@sqlite.org/sqlite-wasm` 3.54.1-build1; `puppeteer-core` 25.19.0; Chrome 158.0.8127.38 |
| Commit do código do spike | Ver o PR deste relatório (branch `spike/c-rbsc-format`) |
| Código | [harness/](harness/) (Rust) e [wasm/](wasm/) (Node + Chrome); dados em `results/` |
| Licenças das dependências | rusqlite MIT; libsqlite3-sys MIT (SQLite: domínio público); zstd BSD-3-Clause; lz4_flex MIT; blake3 CC0-1.0 OU Apache-2.0; sqlite-wasm Apache-2.0; puppeteer-core Apache-2.0. Nenhuma é copyleft |

O schema usado é o de [rbsc-schema-v1.sql](../../contracts/document-format/rbsc-schema-v1.sql) (sem alterações).

## 3. Números medidos
| Critério (do plano) | Meta | Medido | Passou? |
|---|---|---|---|
| Corrupções em interrupções forçadas, `synchronous=NORMAL` | 0 em 1.000 | **0 em 1.000** (970 reaberturas com WAL pendente) | Sim |
| Idem, `synchronous=FULL` | 0 em 1.000 | **0 em 1.000** (991 reaberturas com WAL pendente) | Sim |
| Abertura de R-A com carga progressiva | ≤ 2 s | Árvore pronta em 4–6 ms; viewport (50 tiles, 12,5 MiB) pronto em 45–65 ms, em arquivo de 238 MiB (misto) e 419 MiB (denso: 30 camadas × 256 tiles) | Sim |
| SQLite em WASM com OPFS (leitura e escrita) | funcional | Funcional nos 2 VFS testados; 600 tiles (37,5 MiB) gravados, navegador fechado e reaberto, 600 lidos, 0 hashes divergentes, `integrity_check` ok. **Mas `journal_mode=WAL` é recusado (fica `delete`)** | Sim, com ressalva |
| zstd nível 3 comprime um tile RGBA8 256×256 | ≤ 5 ms | p95 de 0,08 a 1,82 ms; máximo 2,61 ms (classe "fundo") | Sim |

**Método e amostras.**
- **Queda:** processo filho grava transações sem parar (cada uma: 2 tiles `zstd` + 2 `tile_refs` + 1 linha em `oplog` + atualização de `nodes.extra`, tudo no mesmo `COMMIT`). O pai o mata com `TerminateProcess` (equivalente ao `kill -9`: sem flush e sem handlers) após 30–500 ms aleatórios, reabre o arquivo e confere: `integrity_check = ok`; `foreign_key_check` vazio; `oplog` sem buracos (`count = max(seq)`); estado materializado igual ao `oplog` (`nodes.extra = max(seq)`); os tiles citados nas últimas 20 operações existem e o BLAKE3 do conteúdo descomprimido bate com o hash. O arquivo é recriado a cada 50 interrupções (20 arquivos por modo). Tempo: 723 s (NORMAL) e 650 s (FULL).
- **Abertura:** 5 repetições por arquivo, processo novo a cada uma. Fase 1 = conexão + `document_meta` + `nodes` + todos os `tile_refs`; fase 2 = 50 tiles da região 8×7 do canto, descomprimidos; fase 3 (resto, em sequência na mesma thread): 3,0–3,2 s para 4.179 tiles (misto) e 5,3–5,6 s para 7.341 (denso). `quick_check`: 0,23 s (misto) e 0,40 s (denso); `integrity_check`: 0,42–0,45 s (misto) e 0,78–1,07 s (denso).
- **Compressão:** 300 tiles por classe, tempo medido por chamada. Resumo (zstd 3 vs lz4, tamanho médio): fundo 70,7 vs 117,5 KiB; pinceladas 41,0 vs 52,3 KiB; pinceladas+grão 68,5 vs 87,6 KiB; ruído puro 256 vs 257 KiB (incompressível). Tabela completa em [results/compress.txt](results/compress.txt).
- **WASM:** [wasm/run.mjs](wasm/run.mjs) abre o Chrome instalado (headless) com um perfil novo, grava 600 tiles de 64 KiB em uma transação, **fecha o navegador**, abre outro com o mesmo perfil e lê tudo conferindo SHA-256. Testados o VFS `opfs` (exige `COOP/COEP`; escrita 2,9 s, leitura 0,9 s) e o `opfs-sahpool` (não exige; escrita 0,8 s, leitura 0,3 s). Dados em [results/wasm-opfs.json](results/wasm-opfs.json). O campo `opfsVfsAvailable` do JSON está **errado** (a propriedade `sqlite3.opfs` não é exposta nesta build); o `OpfsDb` foi construído e usado com sucesso, o que prova que o VFS existe.

## 4. O que funcionou e o que não funcionou
**Funcionou**
- 2.000 interrupções forçadas (1.000 por modo) sem nenhuma corrupção, perda de atomicidade entre `oplog` e estado materializado, ou tile referenciado inexistente. Em 97–99% das reaberturas havia WAL pendente, ou seja, a recuperação automática foi de fato exercitada, não só ignorada.
- Abertura em duas fases: a árvore inteira de R-A cabe em poucos milissegundos; o viewport abre em ~50 ms.
- A deduplicação por hash apareceu mesmo com conteúdo sintético: 339 de 7.680 refs (4,4%) apontam para tiles repetidos.
- Todos os níveis de zstd testados ficaram abaixo de 5 ms por tile; o nível 9 chega a 18 ms só na classe "fundo" (não usado).

**Não funcionou / surpreendeu**
- **Sem WAL no navegador.** Nos dois VFS, `PRAGMA journal_mode=WAL` devolveu `delete`. O WAL precisa de memória compartilhada entre conexões, que o SQLite em WASM não oferece nesses VFS. Consequência para a SPEC-002/ADR-007: no web, `autosave + render concorrente` (TD-001) não tem leitores simultâneos à escrita no mesmo arquivo; a atomicidade vem do diário de reversão (e o `synchronous` passa a importar mais).
- O `opfs-sahpool` é 2,5 a 3,6× mais rápido e dispensa `COOP/COEP`, mas é de **uma conexão exclusiva por perfil/aba** (limitação do próprio VFS), o que importa para "duas abas do mesmo documento".
- A compressão praticamente não ajuda em ruído puro (1,00×), esperado.

## 5. Recomendação
1. **Manter o SQLite com WAL como formato nativo** (desktop e, por extensão, mobile): critérios cumpridos. Registrar na ADR-007 as evidências desta seção.
2. **Alterar a ADR-007 e a SPEC-002 para tratar a web como modo "sem WAL"** (diário de reversão): definir qual VFS (`opfs` ou `opfs-sahpool`), qual `synchronous` e como lidar com aba dupla. Isto é mudança de formato/sync: **exige revisão humana** (decisão em aberto nº 8 do produto) e, se a ADR já estiver aprovada, Change Request.
3. **Confirmar TD-002 (zstd nível 3):** 22% a 40% menor que o lz4 nos tiles com conteúdo, com tempos de compressão e descompressão muito abaixo do orçamento.
4. **Sobre `synchronous`:** o contrato [rbsc-schema-v1.sql](../../contracts/document-format/rbsc-schema-v1.sql) diz "NORMAL (WAL), a validar". Para **interrupção do processo** (o que foi testado), NORMAL e FULL se comportaram igual (0 corrupções). A diferença entre eles só aparece em **queda de energia ou do sistema operacional**, que este spike **não testou**; manter NORMAL é uma escolha de desempenho a validar antes do R1.
5. **ADRs a atualizar:** ADR-007 (evidência e modo web); TD-001 e TD-002 na SPEC-002. Este spike **não altera o status de nenhuma ADR**; quem aprova é o arquiteto.

## 6. Riscos novos e perguntas abertas
- **Risco novo:** ausência de WAL no web (item 4 acima). Para o `risk-register`.
- **Pergunta:** o web precisa mesmo de escrita concorrente com leitura/render? Se a UI web não precisar, o diário de reversão basta; se precisar, avaliar outra estratégia (uma única conexão em um Worker dono do arquivo e mensagens para o resto).
- **Limites deste spike (não superar na leitura dos números):**
  - A queda foi **de processo** (`TerminateProcess`), não de energia; nenhum teste de queda real ou de disco cheio.
  - Tiles **sintéticos** (gradientes, pinceladas e granulação gerados por código). A razão de compressão e o tamanho do arquivo com arte real podem diferir bastante.
  - Abertura com **cache do sistema operacional quente**; não medi abertura fria (exige reinício ou ferramenta para esvaziar o cache).
  - **Uma máquina só** (Windows/NTFS/NVMe) e Defender ativo. Nada foi medido em macOS, Linux, iPadOS ou Android.
  - Apenas **Chrome** testado no WASM (Firefox e Safari não); cota e despejo de OPFS não testados.
  - R-B (8192² × 10 camadas) e abertura concorrente do mesmo arquivo por dois processos **não** foram testados.
  - A hipótese "o processo morreu no meio de um `COMMIT`" não é provada individualmente por iteração: o indício é o WAL pendente na reabertura.

## 7. Anexos
- Dados brutos: [results/](results/) (`compress.txt`, `fill.txt`, `fill-dense.txt`, `open.txt`, `crash-normal.txt`, `crash-full.txt`, `wasm-opfs.json`).
- Como reproduzir (a partir de `spikes/spike-c-rbsc-format/harness`, com Rust instalado): `cargo build --release`; depois `spike-c-harness compress`, `fill <arquivo> normal [dense]`, `open <arquivo>`, `crash-run <pasta> 1000 normal|full 50`. Para o WASM, em `wasm/`: `npm install` e `node run.mjs 600` (precisa do Chrome instalado). Defina `CARGO_TARGET_DIR` fora do OneDrive.
