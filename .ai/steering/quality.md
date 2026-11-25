# Quality — Golden Images, Benchmarks e Dispositivos de Referência

## Documentos de referência

| Nome | Dimensão | Camadas | Profundidade | Uso |
|------|----------|---------|-------------|-----|
| R-A | 4096 × 4096 | 30 camadas raster RGBA | 8 bits | Benchmarks de composição, abertura, memória |
| R-B | 8192 × 8192 | 10 camadas raster RGBA | 8 bits | Stress test de tiles e memória |

## Dispositivos de referência

> A definir antes do primeiro spike. Um dispositivo por categoria:

| Categoria | Exemplo (a confirmar) | Uso |
|-----------|----------------------|-----|
| Desktop | — | Benchmarks de FPS, latência, memória |
| Tablet com caneta | — | Latência de caneta, integração Flutter |
| Android | — | Memória, GPU mobile |
| Navegador | — | WebGPU/WebGL2, WASM |

## Tolerâncias visuais

| Contexto | Tolerância máxima por canal |
|----------|---------------------------|
| Composição sem pincel (blend modes, máscaras) | ≤ 2/255 |
| Composição com pincel (dabs, stamps) | ≤ 4/255 |
| Conversão de cor (sRGB ↔ Display P3, dentro do gamut) | ΔE00 ≤ 1 |

## Metas de desempenho (hipóteses)

| Métrica | Meta | Como medir |
|---------|------|-----------|
| FPS em pan/zoom/pintura | 60 fps sustentados (frame time p95 ≤ 16,6 ms) | Benchmark automatizado |
| FPS em 120 Hz | p95 ≤ 8,3 ms (onde suportado) | Benchmark em tablet de referência |
| Latência caneta → tela | p95 ≤ 30 ms (meta 20 ms em tablets de ponta) | Câmera de alta velocidade ou timestamps |
| Abertura de R-A | ≤ 2 s no desktop de referência | Benchmark de abertura |
| Memória de trabalho R-A | ≤ 1,5 GB com remoção de tiles sob pressão | Perfil de RAM e VRAM |
| Autosave local | Confirmação p95 ≤ 100 ms após fim do traço | Instrumentação do log |
| Queda abrupta | ≤ 1 traço em andamento perdido; 0 corrupções em 1.000 interrupções | Teste de injeção de falha |
| Sync online | Propagação p95 ≤ 500 ms na mesma região | Teste de integração |
| Sync offline | Reconciliação de 1.000 operações ≤ 10 s | Teste de integração |
| Consistência visual | Dentro das tolerâncias acima | Golden images |
| Compatibilidade | Todas as versões anteriores do `.rbsc` abrem | Corpus em `tests/compat/` |
| Recuperação na nuvem | RPO ≤ 5 min, RTO ≤ 4 h | Exercício de restauração |

## Golden images

### Processo
1. O documento de referência é renderizado pelo motor.
2. O resultado é comparado pixel a pixel com a golden image armazenada.
3. Se a diferença excede a tolerância, o teste falha.
4. Golden images são atualizadas **somente** por PR explícito, com justificativa.

### Armazenamento
- Git LFS ou object storage dedicado (decisão a tomar no bootstrap).
- Convenção de nomes: `tests/graphics/<spec>/<caso>-<plataforma>.png`.
- Uma golden por plataforma/GPU quando houver diferença esperada.

### Cobertura mínima
- Blend modes (multiply, screen, overlay, soft light, difference, pelo menos).
- Composição com transparência e máscaras.
- Conversão de cor (sRGB, Display P3).
- Dabs de pincel com diferentes parâmetros.
- Texto e formas vetoriais compostos com raster.

## Benchmarks

### Execução
- Runners dedicados por dispositivo de referência.
- Runners compartilhados são ruidosos: usar repetições e margens definidas na spec.
- Resultados publicados como artefatos do CI.

### Regressão
- O CI falha se uma métrica regredir além da margem definida.
- Regressões são tratadas como bugs, não como "melhoria futura".

## Tipos de verificação

| Tipo | Tag | Evidência exigida |
|------|-----|------------------|
| Comportamental | `[BEH]` | Teste automatizado e saída do comando |
| Visual | `[VIS]` | Golden image com tolerância declarada e diff |
| Desempenho | `[PERF]` | Números no dispositivo de referência e limite da spec |
| Conformance | `[CONF]` | Execução da conformance suite em Rust e Java |
