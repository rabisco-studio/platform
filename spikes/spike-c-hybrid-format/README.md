# Spike (c) — Formato .hybrid (SQLite + bundle)

**Hipótese:** SQLite com WAL atende os requisitos de atomicidade, carga parcial e resistência a queda.

**Duração estimada:** 1 semana

## Objetivos
1. Criar arquivo SQLite com schema proposto (SPEC-001/002).
2. Preencher com R-A (4096×4096, 30 camadas).
3. Executar teste de crash safety: 1.000 interrupções forçadas (kill -9) durante escrita.
4. Medir tempo de abertura com carga progressiva.
5. Testar SQLite compilado para WASM com OPFS backend.
6. Testar compressão de tiles (zstd vs lz4).

## Critérios de Aprovação
- 0 corrupções em 1.000 interrupções.
- Abertura de R-A ≤ 2 s com carga progressiva.
- SQLite em WASM com OPFS funcional (read + write).
- zstd level 3 comprime tile RGBA8 256×256 em ≤ 5 ms.

## Se reprovar
- ZIP com journaling próprio, ou outro contêiner (ex: Arrow IPC).

## Entregáveis
- Binário de teste com harness de crash.
- Resultados: tabela de corrupções, tempos de abertura, tamanhos com cada compressor.
- Recomendação para ADR-007.
