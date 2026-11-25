# Resumo dos spikes (spike-summary)

Roteador de `spikes/`: os cinco experimentos da Fase 0, **uma linha por spike**. Spikes produzem decisões e números, nunca código de produto. A tabela com critérios de aprovação e as ADRs que cada um resolve está no [README.md](README.md) desta pasta.

**Como manter:** o `sdd-check` exige que toda pasta `spike-*` apareça aqui. O resultado de um spike vira relatório (template [spike-report-template.md](../docs/templates/spike-report-template.md)) e atualiza a ADR correspondente.

| Spike | Pergunta que responde | Resolve | Plano |
|---|---|---|---|
| a | O mesmo core Rust com wgpu renderiza raster e vetor em desktop (Metal, Vulkan, DX12) e na web (WebGPU)? | ADR-001, ADR-002 | [spike-a-rust-wgpu](spike-a-rust-wgpu/README.md) |
| b | O Flutter como UI adiciona latência perceptível ao pipeline de pintura com caneta? | ADR-003 | [spike-b-flutter-wgpu-pen](spike-b-flutter-wgpu-pen/README.md) |
| c | O SQLite em modo WAL atende atomicidade, carga parcial e resistência a queda no formato `.rbsc`? | ADR-007 | [spike-c-rbsc-format](spike-c-rbsc-format/README.md) |
| d | Os 16 bits por canal cabem nos orçamentos de memória e a pipeline de cor (sRGB e Display P3) é viável? | ADR-013 | [spike-d-color-pipeline](spike-d-color-pipeline/README.md) |
| e | Flutter web ou React com WebAssembly serve como frontend do editor web? | ADR-004 | [spike-e-web-ui](spike-e-web-ui/README.md) |

Ordem de dependência: o spike (b) e o spike (e) dependem do (a); (c) e (d) são independentes. Detalhes em [PLAN.md](../.ai/sdd/PLAN.md).
