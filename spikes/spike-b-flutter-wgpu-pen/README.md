# Spike (b) — Flutter + wgpu + caneta

**Hipótese:** Flutter como shell de UI não adiciona latência perceptível ao pipeline de pintura com caneta.

**Duração estimada:** 2 semanas

## Objetivos
1. Integrar o core Rust (wgpu) em um app Flutter desktop.
2. Testar três caminhos de integração GPU:
   - (i) Texture (render para textura compartilhada).
   - (ii) PlatformView (superfície nativa embutida no Flutter).
   - (iii) Shell nativo puro com Flutter apenas nos painéis.
3. Medir latência caneta → tela com Wacom e Apple Pencil.
4. Medir overhead do bridge Dart ↔ Rust (FFI).

## Critérios de Aprovação
- Overhead p95 ≤ 8 ms sobre a linha de base nativa (sem Flutter) em pelo menos um caminho.
- Pressão e inclinação recebidas sem perda.
- FFI call < 1 ms para operações típicas.

## Se reprovar
- Canvas hospedado por shell nativo em cada plataforma, com Flutter apenas nos painéis de UI.

## Entregáveis
- App Flutter com canvas Rust + pipeline de caneta.
- Tabela comparativa dos 3 caminhos: latência, complexidade, limitações.
- Recomendação para ADR-003.
