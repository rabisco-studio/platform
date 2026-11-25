# Spikes — Fase 0

Cada spike é um experimento com hipótese, critério de aprovação e plano B. Spikes **nunca fecham tarefas** e nenhum código de spike entra em produção. Produzem relatório e atualizam as ADRs relacionadas.

| Spike | Hipótese | Critério | ADRs |
|---|---|---|---|
| [a](spike-a-rust-wgpu/README.md) | Rust + wgpu renderiza raster e vetor em desktop e web | FT p95 ≤ 16,6 ms em R-A | 001, 002 |
| [b](spike-b-flutter-wgpu-pen/README.md) | Flutter não adiciona latência perceptível | Overhead p95 ≤ 8 ms | 003 |
| [c](spike-c-hybrid-format/README.md) | SQLite atende atomicidade e carga parcial | 0 corrupções em 1.000 kills | 007 |
| [d](spike-d-color-pipeline/README.md) | 16 bits cabe nos orçamentos de memória | AC-1 a AC-4 | 013 |
| [e](spike-e-web-ui/README.md) | Flutter web ou React atende ao editor web | Tamanho, TTI, latência | 004 |

Os dispositivos de referência dependem de DEC-004 (ver [decision-log](../docs/governance/decision-log.md)).
