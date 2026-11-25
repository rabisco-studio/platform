# Principles — Hybrid Digital Art Platform

> Frases declarativas e curtas que previnem erros de categoria.
> O texto completo com verificações está em `docs/constitution.md`.

- **P-01:** O core não depende de UI, backend ou provedor de nuvem.
- **P-02:** Uma alteração só é "salva" depois de persistida localmente.
- **P-03:** Operações são imutáveis e idempotentes. Undo é uma nova operação.
- **P-04:** Tiles são a autoridade do pixel. A repetição de traços nunca é a fonte do pixel.
- **P-05:** O servidor ordena, autoriza e distribui. Não interpreta a cena.
- **P-06:** Todo contrato público tem schema em `contracts/` e teste de conformidade.
- **P-07:** Toda mudança do formato `.hybrid` traz versão, migração e arquivo no corpus de compatibilidade.
- **P-08:** A composição acontece no espaço de trabalho declarado do documento.
- **P-09:** A entrada prevista é transitória e nunca é persistida.
- **P-10:** Permissões são verificadas no servidor em toda operação sensível.
- **P-11:** Se há dúvida sobre estar no escopo, não está.
