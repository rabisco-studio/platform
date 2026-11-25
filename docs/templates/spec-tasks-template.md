# SPEC-NNN — Tasks

**Status:** tasks:draft | tasks:approved
**Design:** design:approved em AAAA-MM-DD

## 1. Verificação de prontidão

- [ ] `requirements:approved` em main.
- [ ] `design:approved` em main.
- [ ] Todas as perguntas `Q-*` respondidas (nenhuma `aberta`).
- [ ] Contratos afetados revisados pelos donos.

## 2. Cobertura

| FR/NFR | Tarefa(s) |
|--------|-----------|
| FR-001 | T-001 |
| FR-002 | T-002, T-003 |
| NFR-001 | T-004 |

> Todo FR *Must* deve aparecer nesta tabela. Se não aparece, há uma lacuna.

## 3. Tarefas

### T-001 — Título
**Requisito coberto:** FR-001
**Prioridade:** Must | Should | Could
**Estimativa:** 2–4 h
**Dependências:** nenhuma | T-xxx
**Checklist:**
- [ ] —
- [ ] —

**Critérios de aceitação:**
- AC: Given ... When ... Then ...

**Arquivos prováveis:**
- `core/rust/crate-name/src/module.rs`

**Comando de verificação:**
```bash
cargo test -p crate-name -- test_name
```

### T-002 — Título
...

### T-003 — Título
...

## 4. Ordem de execução

```
T-001 → T-002 → T-003
              ↘ T-004
```

## 5. Riscos de implementação

| Risco | Tarefa afetada | Mitigação |
|-------|---------------|-----------|
| — | — | — |
