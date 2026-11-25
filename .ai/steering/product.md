# Product — Rabisco

## Visão

Plataforma profissional de criação visual híbrida que integra pintura raster e ilustração vetorial em um único ambiente, com sincronização em nuvem e colaboração em tempo real.

## Proposta de valor

- Criação raster e vetorial no mesmo documento.
- Ferramentas profissionais de pintura e ilustração.
- Interface adaptável a desktop, tablet, smartphone e navegador.
- Sincronização automática entre dispositivos.
- Colaboração em tempo real.
- Edição não destrutiva.
- Biblioteca pessoal de projetos na nuvem.
- Funcionamento offline completo.
- Extensibilidade por plugins.

## Público-alvo

| Segmento | Necessidades principais |
|----------|------------------------|
| Iniciantes | Interface acessível, ferramentas simples, aprendizagem contextual |
| Ilustradores | Pincéis, camadas, máscaras, controle artístico |
| Designers gráficos | Vetores, tipografia, formas, composição |
| Artistas profissionais | Performance, precisão, gerenciamento de cores, recursos avançados |
| Estudantes | Organização, acessibilidade, sincronização |
| Equipes criativas | Compartilhamento, comentários, colaboração |

## Personas

### Ana — Ilustradora freelancer
- 28 anos, trabalha com ilustração editorial e pessoal.
- Usa Procreate no iPad e Krita no desktop.
- Precisa: pincéis responsivos, camadas, exportação profissional, sincronização entre dispositivos.
- Frustração: alternar entre apps perde contexto e consistência.

### Carlos — Designer gráfico em agência
- 35 anos, cria identidade visual, peças gráficas e layouts.
- Usa Illustrator e Figma.
- Precisa: vetores precisos, tipografia, colaboração, compartilhamento com clientes.
- Frustração: ferramentas vetoriais não têm pintura raster integrada.

### Lia — Estudante de design
- 20 anos, aprendendo ilustração digital.
- Orçamento limitado, usa celular e laptop básico.
- Precisa: interface simples, tutoriais, funcionamento offline, preço acessível.
- Frustração: ferramentas profissionais são caras e complexas demais.

## Referências de mercado

| Referência | Capacidades a estudar |
|------------|----------------------|
| Procreate | Experiência de desenho, pincéis e interação com caneta |
| Krita | Pintura digital profissional e gerenciamento de camadas |
| Adobe Illustrator | Geometria vetorial, precisão e tipografia |
| Affinity Designer | Fluxo de trabalho raster e vetorial integrado |
| Figma | Colaboração, documentos compartilhados e experiência em nuvem |

**Atenção:** estas são fontes de inspiração e comparação, não uma intenção de reproduzir suas interfaces ou funcionalidades.

## Releases

| Release | Nome | Fases | Conteúdo |
|---------|------|-------|----------|
| R1 | Local Studio | 1–4 | Editor híbrido local, sem conta, nas plataformas Tier 1 |
| R2 | Cloud | 5 | Conta, biblioteca, autosave e sincronização entre dispositivos |
| R3 | Collab | 6 | Compartilhamento, permissões e edição simultânea |
| R4 | Everywhere | 7 | Tablets, smartphones e web |
| R5 | Pro | 8 | Plugins, ferramentas avançadas, PSD e CMYK |

**Plataformas:**
- Tier 1 (R1): Windows e macOS, com Linux em melhor esforço.
- Tier 2 (R4): iPadOS e tablets Android.
- Tier 3 (R4): smartphones e web.

## MVP (R1 — Local Studio)

O produto mínimo é um editor local que prova a viabilidade do motor híbrido:

- Documento com prancheta, camadas raster e vetoriais.
- Pincéis básicos (lápis, caneta, aerógrafo, borracha) com pressão de caneta.
- Paths vetoriais com Bézier, formas geométricas e preenchimentos.
- Composição híbrida com blend modes e grupos.
- Undo/Redo com modelo de operações.
- Formato `.rbsc` com autosave e recuperação.
- Importação de imagens raster; exportação PNG, JPEG, WebP, SVG.
- Interface desktop adaptável.

## Escopo negativo (o que NÃO é)

- Não é um clone completo de Photoshop ou Illustrator.
- Sem CMYK nem exportação PSD antes do R5.
- Sem criptografia ponta a ponta prometida.
- Sem microsserviços no início: backend como modular monolith.
- Sem colaboração raster concorrente na mesma camada antes do spike da Fase 6.
- Sem billing e planos antes do R2.
- Sem editor visual de pincéis antes do R5.

## Modelo de negócio

A definir antes do R2. Até lá, apenas quotas de armazenamento. Opções a avaliar:
- Freemium com limite de armazenamento em nuvem.
- Assinatura mensal/anual para recursos cloud e colaboração.
- Licença única para o editor local (R1).

## Perguntas de produto em aberto

| # | Pergunta | Padrão recomendado | Impacto |
|---|----------|-------------------|---------|
| 1 | Quais plataformas no R1? | Windows e macOS (Linux em melhor esforço) | Foco dos spikes e do CI |
| 2 | A web é prioridade de lançamento? | Não: entra no R4 | Libera a Fase 1 para o core |
| 3 | Política sobre uso do conteúdo para IA | Nunca usar para treino; acesso humano só com consentimento, suporte ou obrigação legal | Termos de uso e ADR-018 |
| 4 | Modelo de negócio e planos | Decidir antes do R2; até lá só quotas | Módulo Billing |
| 5 | Região principal dos dados | Região na UE e, se houver público no Brasil, outra no Brasil | Residência de dados e custos |
| 6 | Licença do core | Decidir antes de escolher dependências. Código GPL não pode ser copiado para core proprietário | Escolha de bibliotecas |
| 7 | Escopo do PSD | Somente importação, no R5 | Esforço de interoperabilidade |
| 8 | Quem aprova specs | Revisão humana obrigatória em formato, sync, segurança e privacidade | Governança do SDD |
