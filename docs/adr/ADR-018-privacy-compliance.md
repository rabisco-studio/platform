# ADR-018 — Privacidade e conformidade (LGPD/GDPR)

**Status:** Proposta
**Origem:** Nova na v2
**Data:** 2026-11-24
**Resolvida por:** Revisão jurídica
**Requisitos relacionados:** RNF-04 (segurança), RNF-09

## 1. Contexto e problema
Para um produto de arte, a postura sobre o uso do conteúdo dos usuários é decisão de confiança.

## 2. Decisão proposta
- **LGPD e GDPR desde o desenho:** base legal por tipo de dado, minimização, finalidade explícita.
- **Direitos do titular:** acesso, portabilidade, exclusão, correção.
- **Papéis:** controladora para dados de conta; operadora para conteúdo dos documentos.
- **Subprocessadores:** lista pública com acordos de tratamento.
- **Residência de dados:** região por workspace.
- **Retenção e exclusão:** prazos documentados. Exclusão de conta remove documentos dentro de prazo definido.
- **Incidentes:** procedimento com prazos (GDPR: 72h; LGPD: conforme ANPD).
- **Conteúdo do usuário e IA:** conteúdo dos documentos **não** é usado para treinar modelos. Acesso humano só com consentimento, suporte solicitado ou obrigação legal.
- **DPIA** antes do R2.
- **E2EE:** adiada. Só entra com arquitetura própria.

## 3. Consequências
- Positivas: confiança, conformidade legal, diferencial competitivo.
- Negativas: custo de implementação e manutenção de compliance.

## 4. Critérios de reavaliação
Mudanças regulatórias. Expansão para novas jurisdições.
