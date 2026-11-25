# Relatório do Spike (d) — Pipeline de cor e 16 bits

**Data:** 2026-11-25
**Autor:** maria-brito15 (execução e texto com o Claude Code; revisão da autora pendente)
**Revisor:** pendente (precisa ser pessoa diferente do autor)
**Status:** Rascunho
**Plano:** [README.md](README.md)

## 1. Resultado em uma linha
**APROVADO COM RESSALVAS (parcial):** AC-2 e AC-4 passam em 16 bits; o AC-1 só vale com alfa direto ou com 16 bits pré-multiplicado (em 8 bits pré-multiplicado, como o texto da ADR-013 descreve, ele **não** vale para pixels semitransparentes); o AC-3 (duas GPUs) e o critério do iPad de referência **não foram medidos aqui**.

## 2. Ambiente
| Item | Valor |
|---|---|
| Dispositivo / GPU / SO | Notebook Intel Core i7-1355U (10 núcleos, 12 threads), 15,7 GB de RAM, Windows 11. Nenhuma GPU foi usada neste spike (só CPU) |
| Versões | Rust 1.100.0 (MSVC); `moxcms` 0.9.2 (Rust puro); `lcms2` 6.3.0 com Little CMS embutido (`lcms2-sys` 4.2.0); `png` 0.18.1; SQLite 3.54 (via `rusqlite` 0.43) |
| Commit do código do spike | Ver o PR deste relatório (branch `spike/d-color-pipeline`) |
| Código | [harness/](harness/) (testes e medições) e [crosscheck/](crosscheck/) (compilação cruzada); dados em [results/](results/) |
| Licenças | moxcms BSD-3-Clause OU Apache-2.0; lcms2 (crate) MIT e lcms2-sys MIT (Little CMS é MIT); png MIT OU Apache-2.0. Nenhuma é copyleft |

## 3. Números medidos
| Critério (do plano) | Meta | Medido | Passou? |
|---|---|---|---|
| AC-1: sRGB 8 bits importado e exportado sem edição | idêntico bit a bit | **Alfa direto: 0 pixels diferentes.** Pré-multiplicado em 16 bits: idêntico, exceto a cor escondida sob alfa 0 (131.606 pixels). **Pré-multiplicado em 8 bits: 231.669 pixels semitransparentes alterados (22,1% da imagem de teste), além da cor sob alfa 0.** Pixels opacos: sempre idênticos. A biblioteca sRGB→sRGB é identidade nas 65.536 cores testadas | **Parcial** |
| AC-2: Display P3 → sRGB, ΔE00 no gamut | ≤ 1 | 16 bits: `moxcms` máx 0,05; `lcms2` máx 0,92. 8 bits: `lcms2` máx 0,92; `moxcms` máx 1,26 (5 de 121.138 cores) ou 1,09 (3 de 121.138) com ponto flutuante, só em tons escuros. Piso teórico da quantização em 8 bits: máx 0,84 | **Sim em 16 bits; 8 bits: `lcms2` sim, `moxcms` quase** |
| AC-3: mesma composição em duas GPUs | tolerância visual | **Não medido** (sem GPU neste spike; depende do wgpu, spike a) | Pendente |
| AC-4: reabrir mantém perfil, profundidade e espaço de mesclagem | iguais | Perfil ICC (600 bytes) idêntico; `bit_depth=16`; `blend_space='linear'`; tile RGBA16 de 512 KiB idêntico; o schema recusa `bit_depth=12` e `blend_space='hsl'` | Sim |
| R-A em 16 bits cabe no iPad de referência com remoção de tiles | cabe | **Não avaliável:** o iPad de referência não existe (DEC-004 está Aberta). Aritmética abaixo | Pendente |
| Biblioteca compila para WASM e iOS | compila | `moxcms`: compila para `wasm32`, `aarch64-apple-ios` e `aarch64-linux-android`. `lcms2`: **falhou aqui por falta de `clang`/NDK/SDK**, o que não prova inviabilidade | Sim (`moxcms`); inconclusivo (`lcms2`) |

**Método e amostras.**
- **Referência de cor:** conversão P3 → sRGB em ponto flutuante de 64 bits (matrizes oficiais e curva sRGB), com ΔE2000 próprio, validado antes das medições contra os pares publicados por Sharma, Wu e Dalal (2,0425 e 2,8615; ver [results/deltae-selftest.txt](results/deltae-selftest.txt)).
- **AC-2:** 235.937 cores P3 (grade 33³ mais 200.000 aleatórias); 51,3% caem dentro do gamut sRGB. O ΔE00 é entre a saída da biblioteca e a referência exata para a mesma entrada quantizada, só nas cores dentro do gamut. Nas cores fora do gamut (114.826) a conversão exata não tem representação e a biblioteca recorta; o recorte da biblioteca difere do recorte ideal em no máximo ΔE00 0,95.
- **AC-1:** imagem sintética de 1024×1024 com alfa de todos os tipos (50% opaco, alfa 0, alfa 1 a 8, aleatório, 254), codificada e decodificada com o crate `png`; três caminhos de armazenamento comparados.
- **Memória:** aritmética exata sobre o tamanho do tile (256 KiB em RGBA8, 512 KiB em RGBA16); nenhuma medição em aparelho.
- **Composição:** CPU escalar, 30 camadas em um viewport de 2048×1536, "normal" com alfa pré-multiplicado, mediana de 7 execuções, 1 e 12 threads.

**Memória (aritmética).**
| Cenário | 8 bits | 16 bits |
|---|---|---|
| R-A (4096², 30 camadas) 100% preenchido, 7.680 tiles | 1.920 MiB | 3.840 MiB |
| R-B (8192², 10 camadas) 100% preenchido, 10.240 tiles | 2.560 MiB | 5.120 MiB |
| Viewport de tablet (48 tiles) com 5 camadas visíveis | 60 MiB | 120 MiB |
| … com 10 camadas visíveis | 120 MiB | 240 MiB |
| … com 30 camadas visíveis | 360 MiB | 720 MiB |
| Orçamento de cache de tablet da SPEC-002 (256 MiB) | 1.024 tiles | 512 tiles |

**Composição em CPU (30 camadas, 2048×1536).**
| Threads | RGBA8 perceptual | RGBA16 perceptual | RGBA16 linear (com tabelas) |
|---|---|---|---|
| 1 | 847,8 ms | 977,6 ms (+15%) | 1.328,1 ms (+57%) |
| 12 | 120,3 ms | 125,5 ms (+4%) | 356,3 ms (+196%) |

## 4. O que funcionou e o que não funcionou
**Funcionou**
- Importação e exportação de PNG sem conversão de cor é **bit a bit idêntica** com alfa direto.
- A conversão sRGB→sRGB da biblioteca é identidade (nenhuma cor mudou), então importar uma imagem sRGB para um espaço de trabalho sRGB não introduz erro.
- P3 → sRGB em 16 bits ficou muito abaixo do limite (`moxcms` máx 0,05) com ΔE00 contra a referência matemática.
- O perfil ICC, a profundidade e o espaço de mesclagem sobrevivem a fechar e reabrir o arquivo `.rbsc`, e o schema rejeita valores inválidos.
- O `moxcms` (Rust puro) compila para WASM, iOS e Android sem nenhuma ferramenta extra.
- Compor 30 camadas em 16 bits custa pouco mais que em 8 bits na CPU (+4% a +15%).

**Não funcionou / surpreendeu**
- **O AC-1 conflita com "alfa pré-multiplicado em 8 bits".** O texto da ADR-013 diz "RGBA com alfa pré-multiplicado" e levanta a hipótese de 8 bits em mobile e web. Nessa combinação, 22% dos pixels da imagem de teste (os semitransparentes) mudam ao importar e exportar. Em 16 bits pré-multiplicado a ida e volta é exata, exceto a cor escondida sob alfa 0 (que o formato pré-multiplicado descarta por definição).
- **`moxcms` 8 bits tem uma cauda acima de ΔE00 1** em tons escuros (por exemplo P3 `[29,24,18]` → sRGB `[30,23,18]`, ΔE00 1,30). O `lcms2` não tem. As opções padrão do `moxcms` usam ponto fixo e a intenção "Perceptual"; para esse perfil (matriz e curva) a intenção não muda o resultado, e o modo ponto flutuante reduz o pior caso para 1,09. Em 16 bits o problema desaparece.
- Mesclar em espaço **linear** custa ~3× mais que em perceptual com 12 threads na CPU (356 ms contra 125 ms), por causa da conversão de curva em cada camada.
- 30 camadas visíveis em um viewport de tablet pedem 720 MiB em 16 bits (360 MiB em 8 bits), acima do orçamento de 256 MiB da SPEC-002 nos dois casos; só funcionaria com caches de composição por grupo.

## 5. Recomendação
1. **Biblioteca de cor:** considerar o `moxcms` (Rust puro) como candidato principal por compilar em todos os alvos sem ferramentas de C; usar a conversão em **16 bits** (ou o modo ponto flutuante) para a exportação P3 → sRGB, onde passa o AC-2 com folga. Manter o `lcms2` como alternativa em desktop, e **repetir a tentativa de compilar o `lcms2` com `clang` e os SDKs de cada plataforma** antes de descartá-lo.
2. **Reescrever o AC-1 na ADR-013** para dizer exatamente o que vale: "idêntico bit a bit para todo pixel com alfa > 0; a cor sob alfa 0 não é preservada em formato pré-multiplicado". E decidir entre: (a) armazenar raster importado com alfa direto, (b) profundidade interna de 16 bits mesmo em mobile, ou (c) preservar os bytes originais da imagem importada em `assets` para exportação sem edição.
3. **Profundidade em mobile (hipótese "8 bits"):** só vale se a escolha do item 2 for a (a) ou a (c), por causa do AC-1. Decidir **depois** de definir os dispositivos de referência (DEC-004) e de medir na GPU (spike a).
4. **Mesclagem linear:** tratar como opção de custo real; medir na GPU antes de decidir o padrão.
5. **ADRs a atualizar:** ADR-013 (critérios, biblioteca, profundidade) e, se a decisão for alterar o formato de pixel, ADR-007 e SPEC-002. Este spike **não altera o status de nenhuma ADR**.

## 6. Riscos novos e perguntas abertas
- **Risco:** AC-1 como está escrito é inatingível com o formato descrito na ADR-013 (pré-multiplicado em 8 bits). Para o `risk-register`.
- **Risco:** o conjunto de trabalho de um viewport com muitas camadas excede o orçamento de tablet; exige cache de composição.
- **Pergunta:** qual é o iPad (e o tablet Android) de referência? Sem isso, "cabe no iPad de referência" não é testável (DEC-004).
- **Pendente neste spike:** AC-3 (duas GPUs) será medido no spike a com o wgpu.
- **Limites deste spike:** composição só em CPU (a GPU muda os números); conversão de cor só entre sRGB e Display P3 com perfis de matriz e curva (não testei perfis ICC com tabelas, como os de impressora ou os de monitores profissionais); imagem de teste sintética; nada rodou em iOS ou Android (só compilou, e só o `moxcms`); o resultado em WASM foi só compilado, não executado.

## 7. Anexos
- Dados brutos: [results/](results/) (`ac1.txt`, `ac2.txt`, `ac4.txt`, `mem.txt`, `compose.txt`, `crosscheck.txt`, `probe-moxcms-8bit.txt`, `deltae-selftest.txt`).
- Como reproduzir (a partir de `spikes/spike-d-color-pipeline/harness`, com Rust instalado e `CARGO_TARGET_DIR` fora do OneDrive): `cargo build --release`; depois `spike-d-harness deltae-selftest | ac1 | ac2 | ac4 | mem | compose | probe`. Compilação cruzada: em `crosscheck/`, `rustup target add wasm32-unknown-unknown aarch64-apple-ios aarch64-linux-android` e `cargo build --release --target <alvo>` (com `--no-default-features --features lcms2` para o `lcms2`).
