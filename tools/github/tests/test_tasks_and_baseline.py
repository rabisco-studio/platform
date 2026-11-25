import contextlib
import datetime
import io
import json
import unittest
from unittest import mock

import support
import baseline_notes as BN
import ghlib as G
import tasks_to_issues as T

CATALOG = ('spec_id,slug,titulo,area,fase,release,rigor,estado\n'
           '099,fixture,Spec de teste,backend,5,R2,anchored,escrita\n'
           '098,draft-only,Spec em rascunho,core,1,R1,spec-first,escrita\n'
           '097,contracts-one,Contratos,contracts,1,R1,anchored,escrita\n')
TASKS = '''# SPEC-099 — Tasks

**Status:** tasks:approved

## 3. Tarefas

### T-001 — Criar o registro
**Requisito:** FR-001, NFR-001
**Prioridade:** Must | **Estimativa:** 2.5h
**Dependências:** nenhuma
**Checklist:**
- [ ] Criar o crate
- [ ] Escrever o teste
**AC:** feito.
**Verificação:** `cargo test -p x`

### T-002 — Tarefa comum
**Requisito:** FR-002
**Prioridade:** Must | **Estimativa:** 1h
**Dependências:** T-001
**Verificação:** `true`

### T-003 — Usa outra spec (Removida)
**Requisito:** FR-003
**Prioridade:** Should | **Estimativa:** 1h
**Dependências:** SPEC-001 T-004
**Verificação:** `true`
'''


def fixture(status='tasks:approved'):
    r = support.TmpRepo()
    r.write('docs/requirements/spec-catalog.csv', CATALOG)
    r.write('.ai/sdd/specs/099-fixture/.status', status + '\n')
    r.write('.ai/sdd/specs/099-fixture/tasks.md', TASKS)
    r.write('.ai/sdd/specs/098-draft-only/.status', 'tasks:draft\n')
    r.write('.ai/sdd/specs/098-draft-only/tasks.md', TASKS)
    r.write('.ai/sdd/specs/097-contracts-one/.status', 'review:done\n')
    r.write('.ai/sdd/specs/097-contracts-one/tasks.md', TASKS)
    return r


class TasksToIssuesTests(unittest.TestCase):
    def setUp(self):
        self.r = fixture()
        self.addCleanup(self.r.cleanup)

    def run_main(self, *args, gh=None):
        out, err = io.StringIO(), io.StringIO()
        patches = [contextlib.redirect_stdout(out), contextlib.redirect_stderr(err)]
        patches.append(mock.patch.object(T, 'WAIT_SECONDS', 0))
        if gh:
            patches.append(mock.patch.object(G, 'gh', gh))
        with contextlib.ExitStack() as st:
            for p in patches:
                st.enter_context(p)
            code = T.main(['--root', str(self.r.path), *args])
        return code, out.getvalue(), err.getvalue()

    def test_refuses_before_g3(self):
        code, _, err = self.run_main('098')
        self.assertEqual(code, 1)
        self.assertIn('só existem depois do gate G3', err)
        self.assertIn('tasks:draft', err)

    def test_accepts_later_stages(self):
        for status in ('tasks:approved', 'implementation:in-progress', 'review:done'):
            T.check_ready(status)
        for status in ('requirements:approved', 'design:approved', 'tasks:draft'):
            with self.assertRaises(T.Refusal):
                T.check_ready(status)

    def test_dry_run_builds_issue_and_creates_nothing(self):
        calls = []
        code, out, _ = self.run_main('099', gh=lambda *a, **k: calls.append(a) or (0, '[]', ''))
        self.assertEqual(code, 0)
        self.assertEqual(calls, [], 'o ensaio não pode chamar o gh')
        self.assertIn('[criar] [SPEC-099 T-001] Criar o registro', out)
        self.assertIn('labels: task, area:backend, rigor:anchored | milestone: R2 Cloud', out)
        self.assertIn('Total: criar 2, ignorar 0', out)  # T-003 está "Removida" e não entra
        self.assertNotIn('Usa outra spec', out)

    def test_body_follows_the_issue_form(self):
        spec_id, row, tasks = T.load_spec(self.r.path, '099')
        title, body, labels, ms = T.build(spec_id, row, tasks[0])
        for section in ('### Spec\n\nSPEC-099', '### ID da tarefa (igual ao tasks.md)\n\nT-001',
                        '### Requisitos (FR/NFR)\n\nFR-001, NFR-001', '### Estimativa\n\n3 h',
                        '### Dependências\n\nnenhuma', '- [ ] Criar o crate', '- [ ] Escrever o teste',
                        '### Verificação\n\n`cargo test -p x`', '<!-- task:SPEC-099:T-001 -->'):
            self.assertIn(section, body)

    def test_removed_tasks_are_skipped(self):
        spec_id, row, tasks = T.load_spec(self.r.path, '099')
        rows = T.plan(spec_id, row, tasks, set())
        self.assertEqual([r[1] for r in rows], ['T-001', 'T-002'])  # T-003 está "Removida"

    def test_idempotent_marker(self):
        spec_id, row, tasks = T.load_spec(self.r.path, '099')
        rows = T.plan(spec_id, row, tasks, {('SPEC-099', 'T-001')})
        self.assertEqual([(r[0], r[1]) for r in rows], [('ignorar', 'T-001'), ('criar', 'T-002')])

    def test_apply_creates_only_missing_issues(self):
        created = []

        def gh(args, payload=None, token=None):
            if args[0] == 'api' and '/issues?' in args[1]:
                return 0, json.dumps([{'body': 'x\n<!-- task:SPEC-099:T-001 -->\n'}]), ''
            if args[0] == 'api' and '/milestones' in args[1]:
                return 0, json.dumps([{'title': 'R2 Cloud'}]), ''
            if args[:2] == ['issue', 'create']:
                created.append(args)
                return 0, 'https://github.com/x/y/issues/9', ''
            raise AssertionError(args)
        code, out, _ = self.run_main('099', '--apply', gh=gh)
        self.assertEqual(code, 0, out)
        self.assertEqual(len(created), 1)
        self.assertIn('[SPEC-099 T-002] Tarefa comum', created[0])
        self.assertIn('R2 Cloud', created[0])

    def test_apply_waits_until_created_issues_are_listed(self):
        listed = []  # a listagem só passa a mostrar T-002 na terceira consulta (consistência eventual)

        def gh(args, payload=None, token=None):
            if args[0] == 'api' and '/issues?' in args[1]:
                listed.append(1)
                body = '<!-- task:SPEC-099:T-001 -->' + ('<!-- task:SPEC-099:T-002 -->' if len(listed) >= 3 else '')
                return 0, json.dumps([{'body': body}]), ''
            if args[0] == 'api' and '/milestones' in args[1]:
                return 0, json.dumps([{'title': 'R2 Cloud'}]), ''
            if args[:2] == ['issue', 'create']:
                return 0, 'https://github.com/x/y/issues/9', ''
            raise AssertionError(args)
        code, out, err = self.run_main('099', '--apply', gh=gh)
        self.assertEqual(code, 0, out)
        self.assertEqual(len(listed), 3)
        self.assertNotIn('AVISO', err)

    def test_apply_warns_when_created_issues_never_show_up(self):
        def gh(args, payload=None, token=None):
            if args[0] == 'api' and '/issues?' in args[1]:
                return 0, '[]', ''
            if args[0] == 'api' and '/milestones' in args[1]:
                return 0, json.dumps([{'title': 'R2 Cloud'}]), ''
            return 0, 'https://github.com/x/y/issues/9', ''
        code, _, err = self.run_main('099', '--apply', gh=gh)
        self.assertEqual(code, 0)
        self.assertIn('AVISO: ainda não aparecem', err)

    def test_apply_stops_without_milestone(self):
        def gh(args, payload=None, token=None):
            if '/milestones' in args[1]:
                return 0, '[]', ''
            if '/issues?' in args[1]:
                return 0, '[]', ''
            raise AssertionError('não deve criar issue')
        code, _, err = self.run_main('099', '--apply', gh=gh)
        self.assertEqual(code, 3)
        self.assertIn('milestone "R2 Cloud" não existe', err)

    def test_apply_without_permission(self):
        code, _, err = self.run_main('099', '--apply', gh=lambda *a, **k: (1, '', 'HTTP 403'))
        self.assertEqual(code, 3)
        self.assertIn('ERRO ao consultar o GitHub', err)

    def test_contracts_area_maps_to_platform_label(self):
        spec_id, row, tasks = T.load_spec(self.r.path, '097')
        self.assertEqual(T.build(spec_id, row, tasks[0])[2], ['task', 'area:platform', 'rigor:anchored'])

    def test_estimate_limits(self):
        self.assertEqual(T.estimate_label(1), '1 h')
        self.assertEqual(T.estimate_label(3.2), '4 h')
        for bad in (None, 0.5, 4.5, 6):
            with self.assertRaises(T.Refusal):
                T.estimate_label(bad)

    def test_unknown_spec(self):
        code, _, err = self.run_main('055')
        self.assertEqual(code, 1)
        self.assertIn('não existe no catálogo', err)


class BaselineTests(unittest.TestCase):
    def test_tag_format(self):
        self.assertEqual(BN.parse_tag('baseline-R1-v1'), ('R1', 1))
        self.assertEqual(BN.parse_tag('baseline-R5-v12'), ('R5', 12))
        for bad in ('baseline-R0-v1', 'baseline-R6-v1', 'baseline-R1', 'baseline-R1-v0', 'v1.0.0', 'baseline-r1-v1', ''):
            with self.assertRaises(ValueError, msg=bad):
                BN.parse_tag(bad)

    def test_notes_for_real_repo(self):
        notes = BN.render('baseline-R1-v1', datetime.date(2026, 11, 25), support.ROOT, strict_ok=True)
        for needle in ('# Baseline R1 v1 — notas', '**Tag:** baseline-R1-v1', '| SPEC-001 |', '| SPEC-017 |',
                       '[x] make strict passa', '[ ] Todas as ADRs', 'Decisões abertas', 'Riscos com exposição 12',
                       '## Assinaturas', 'Pre-release gerado automaticamente'):
            self.assertIn(needle, notes)
        self.assertNotIn('| SPEC-018 |', notes)  # R2 fica de fora do escopo do R1
        self.assertRegex(notes, r'\*\*\d+ de \d+\*\*')

    def test_notes_without_strict_flag_leave_box_unchecked(self):
        notes = BN.render('baseline-R2-v1', datetime.date(2026, 11, 25), support.ROOT)
        self.assertIn('[ ] make strict passa', notes)
        self.assertIn('| SPEC-018 |', notes)

    def test_previous_baseline_is_used_for_changes(self):
        r = support.TmpRepo()
        self.addCleanup(r.cleanup)
        for rel, txt in (('.ai/sdd/INDEX.md', '| Spec | T | Release | Fase | Rigor | Estado | Gate |\n'),
                         ('docs/requirements/coverage.md', ''),
                         ('docs/governance/risk-register.md', ''), ('docs/governance/decision-log.md', '')):
            r.write(rel, txt)
        r.commit('primeiro')
        r.git('tag', 'baseline-R1-v1')
        r.write('x.md', 'x')
        r.commit('GOV: depois da baseline')
        r.git('tag', 'baseline-R1-v2')
        notes = BN.render('baseline-R1-v2', datetime.date(2026, 11, 25), r.path)
        self.assertIn('Baseline anterior: baseline-R1-v1', notes)
        self.assertIn('GOV: depois da baseline', notes)
        self.assertNotIn(' primeiro', notes)

    def test_cli_validate_exit_codes(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(BN.main(['--validate', 'baseline-R1-v1']), 0)
            self.assertEqual(BN.main(['--validate', 'qualquer']), 1)


if __name__ == '__main__':
    unittest.main()
