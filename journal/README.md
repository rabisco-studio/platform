# Diário do projeto (journal)

Registro do que foi feito em cada dia de trabalho: um diário, não uma fonte da verdade. Quem precisa saber **o que foi decidido** lê o [decision-log](../docs/governance/decision-log.md), as ADRs e as specs; quem quer saber **como o dia foi** lê aqui.

## Onde fica

```
journal/<usuario-github>/<AAAA-MM-DD>/entry.md
```

Exemplo: `journal/maria-brito15/2026-11-25/entry.md`. Uma entrada por pessoa por dia, sempre com o nome `entry.md`. O `<usuario-github>` é o login da pessoa no GitHub, e a data usa o formato ISO (AAAA-MM-DD).

## Como escrever
1. Copie o [template](../docs/templates/journal-entry-template.md) para o caminho acima.
2. Preencha o cabeçalho (`**Data:**` e `**Autor:**` precisam bater com a pasta; o `make verify` confere).
3. Conte o que aconteceu, com fatos: PRs, issues, decisões (`DEC-nnn`, `ADR-nnn`), problemas e o que ficou pendente.
4. Abra um PR de governança (`?template=governance.md`) com título `GOV: diário de <usuário> em <data>`.

## Regras
- **Não é fonte da verdade.** Cada fato mora em um lugar só (README, seção 3). Se a entrada cita uma decisão, aponte para o `DEC-nnn`; não copie o texto.
- **O repositório é público.** Nunca escreva segredos, tokens, valores de variáveis, dados pessoais de terceiros nem conteúdo que você não publicaria.
- **Escreva só o que aconteceu**, inclusive o que deu errado e o que ficou sem fazer. Não reescreva entradas de dias anteriores; se algo estava errado, corrija na entrada do dia seguinte e aponte para a anterior.
- **Entrada escrita com ajuda de IA** deve dizer isso no cabeçalho, e quem assina (o autor) revisa antes do PR.
- O `make verify` rejeita arquivos fora do padrão em `journal/` e cabeçalhos que não batem com a pasta.
