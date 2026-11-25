# Revisão de gate — SPEC-NNN <slug> — G<n>

**Data:** AAAA-MM-DD
**Autor da spec:** <pessoa>
**Revisor / aprovador:** <pessoa, diferente do autor>
**Gate:** G1 Requisitos | G2 Design | G3 Tarefas | G4 Implementação | G5 Revisão
**PR do .status:** #<n>

## Resultado
APROVADO | APROVADO COM CONDIÇÕES | REPROVADO

## Checklist comum (todos os gates)
- [ ] make verify passa
- [ ] Cabeçalho do documento correto (status, área, release, rigor, tags, ADRs, depende de)
- [ ] Sem TBD, sem pergunta Q- aberta sem dono e prazo
- [ ] Nenhuma duplicação de fatos que já têm fonte única (catálogos, crates.toml, DDL, contratos)

## G1 Requisitos
- [ ] Cada FR em EARS, com prioridade MoSCoW e tag de verificação
- [ ] Cada FR tem a linha Cobre: com RF/RNF existentes no catálogo
- [ ] Critérios de aceite testáveis (AC-)
- [ ] Rigor e tags coerentes (format, contract, security, privacy exigem anchored)

## G2 Design
- [ ] Todo FR mapeado a um componente; nenhum crate fora de crates.toml
- [ ] Contratos e ADRs citados existem e estão coerentes
- [ ] Riscos e alternativas registrados; decisões D- justificadas

## G3 Tarefas
- [ ] Tarefas de 1 a 4 h, com Requisito, Dependências e Verificação
- [ ] Todo FR coberto na tabela de cobertura; dependências sem ciclo
- [ ] Ordem de execução e esforço total coerentes

## G4 Implementação
- [ ] Todas as tarefas concluídas e testes verdes
- [ ] Contratos atualizados e conformance passando
- [ ] Metas de desempenho medidas no hardware de referência

## G5 Revisão
- [ ] Critérios de aceite verificados um a um
- [ ] Rastreabilidade fechada (requisito, FR, tarefa, teste)

## Observações e condições
<itens obrigatórios antes do próximo gate, com responsável e prazo>
