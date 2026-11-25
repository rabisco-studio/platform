## Escolha o template do tipo de PR
Este é o template geral. Para cada tipo, abra o PR acrescentando `?template=<arquivo>` ao endereço de criação:

| Tipo | Template |
|---|---|
| Requirements, design ou tasks de uma spec | `?template=spec.md` |
| Aprovação de gate (altera o .status) | `?template=gate.md` |
| ADR | `?template=adr.md` |
| Contratos ou crates.toml | `?template=contract.md` |
| Governança, catálogos, tooling, documentação | `?template=governance.md` |
| Código (após o G3) | `?template=code.md` |

Se este template geral for usado, preencha o que segue.

## O que muda
<um assunto por PR; prefixo do título: SPEC-NNN: / ADR-NNN: / GOV: / contracts:>

## Checklist (obrigatório)
- [ ] make verify passou localmente
- [ ] Não editei arquivos gerados à mão
- [ ] Não alterei documento de outra pessoa ou área sem o dono (ver CODEOWNERS)
- [ ] Se alterei documento aprovado: há Change Request vinculada e o .status foi reaberto
- [ ] Fatos novos apontam para a fonte única
- [ ] Sem TBD; perguntas abertas têm responsável e prazo

Issue ou CR: #
