# Tech Stack — Rabisco

> Toda escolha é uma hipótese até a ADR correspondente ser aprovada com evidência de spike.
> Leia o motivo antes de propor troca. Se o motivo não se sustenta mais, abra o processo de ADR.

## Stack principal

| Camada | Tecnologia | Motivo (hipótese) | ADR | Status |
|--------|-----------|-------------------|-----|--------|
| Core e motor gráfico | Rust | Um único core para seis alvos, com desempenho previsível e segurança de memória em código de tiles e pincéis | ADR-001 | Proposta |
| Renderização | wgpu + WGSL | Abstração única sobre Metal, Vulkan, DX12 e WebGPU | ADR-002 | Proposta |
| UI nativa (desktop e mobile) | Flutter | UI nativa para desktop e mobile com um código | ADR-003 | Proposta |
| UI web | React + TypeScript + WebAssembly | Web sobre o mesmo core, condicionada ao spike (e) | ADR-004 | Proposta, condicional |
| Backend | Java + Spring Boot (modular monolith) | Familiaridade, ecossistema e contratação | ADR-005 | Proposta |
| Formato local | SQLite (modo WAL) | Transações atômicas e carga parcial de tiles | ADR-007 | Proposta |
| Banco relacional | PostgreSQL | Metadados, permissões e versões exigem garantias ACID | ADR-011 | Proposta |
| Object storage | S3-compatible / Cloudflare R2 | Blobs grandes por hash, separados do banco relacional | ADR-011 | Proposta |
| Contratos | OpenAPI, AsyncAPI, JSON Schema | Fonte única de contratos entre quatro linguagens | ADR-014 | Proposta |
| Geometria vetorial | kurbo + lyon | Curvas e tesselação — a avaliar licença e maturidade | — | A avaliar |
| Texto | cosmic-text | Layout e renderização tipográfica — a avaliar | — | A avaliar |
| Cache | Redis | Apenas quando necessário para coordenação | — | Adiado |
| Mensageria | RabbitMQ | Apenas quando necessário para processamento assíncrono | — | Adiado |
| Infraestrutura | Docker | Empacotamento e implantação | — | — |

## Versões mínimas

A definir após os spikes. Os spikes devem registrar as versões usadas.

## Regras

1. **Nenhuma biblioteca entra sem verificação de licença.** Código GPL não pode ser copiado para um core proprietário. Manter lista de dependências com licença verificada no CI.
2. **Avaliação antes de adoção:** maturidade, licença, manutenção ativa, compatibilidade com WebAssembly e plataformas móveis.
3. **A seleção de bibliotecas gráficas (kurbo, lyon, cosmic-text) é condicional aos spikes.** Alternativas em Rust puro podem ser necessárias para WebAssembly e iOS.
4. **Redis e RabbitMQ são introduzidos apenas quando houver necessidade concreta.** Evitar complexidade operacional prematura.
