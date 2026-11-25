# Spike (e) — UI web (Flutter web vs React + WASM)

**Hipótese:** Flutter web ou React + WebAssembly atende como frontend do editor web.

**Duração estimada:** 2 semanas

## Objetivos
1. Prototipar o editor web em Flutter web.
2. Prototipar o editor web em React + TypeScript + WASM bridge.
3. Comparar: tamanho do bundle, Time to Interactive, latência de input, acessibilidade (ARIA), SEO.
4. Testar 3 níveis de suporte:
   - Completo com WebGPU.
   - Reduzido com WebGL2.
   - Sem edição abaixo disso (viewer only).

## Critérios de Aprovação
Definir antes do spike:
- Bundle ≤ X MB (gzip).
- TTI ≤ Y s.
- Latência de input ≤ Z ms.
- Acessibilidade: navegação por teclado funcional.

## Se reprovar
- Abandonar Flutter web. Usar React + WASM para a web.

## Entregáveis
- Dois protótipos (Flutter e React).
- Tabela comparativa com todos os critérios.
- Recomendação para ADR-004.

## Nota
Threads em WASM exigem cabeçalhos COOP/COEP (isolamento de origem cruzada). Verificar impacto em hospedagem e conteúdo incorporado.
