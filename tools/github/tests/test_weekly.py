import contextlib
import datetime
import io
import json
import unittest
from unittest import mock

import support
import ghlib as G
import nudge_blocked as N
import overdue as O
import weekly_report as W

LOG = '''| ID | Decisão | Opções | Padrão recomendado | Dono | Prazo | Status |
|---|---|---|---|---|---|---|
| DEC-001 | Velha | a/b | a | PO | 2026-11-01 | Aberta |
| DEC-002 | Futura | a/b | a | PO | 2026-12-30 | Aberta |
| DEC-003 | Sem data | a/b | a | ARQ | Início da Fase 0 | Aberta |
| DEC-004 | Fechada | a/b | a | ARQ | 2026-01-01 | Decidida |
'''
TODAY = datetime.date(2026, 11, 25)


class OverdueTests(unittest.TestCase):
    def test_decisions_only_open(self):
        self.assertEqual([d[0] for d in O.decisions(LOG)], ['DEC-001', 'DEC-002', 'DEC-003'])

    def test_classify(self):
        items = [('decision-log', i, t, p) for i, t, p in O.decisions(LOG)]
        overdue, undated = O.classify(items, TODAY)
        self.assertEqual([r['id'] for r in overdue], ['DEC-001'])
        self.assertEqual([r['id'] for r in undated], ['DEC-003'])

    def test_open_questions(self):
        r = support.TmpRepo()
        self.addCleanup(r.cleanup)
        r.write('.ai/sdd/specs/001-a/requirements.md',
                '- **Q-001:** fechada? **R:** sim\n- **Q-002 (aberta, prazo 2026-11-01):** e agora?\n- **Q-003:** outra TBD\n')
        qs = O.open_questions(r.path)
        self.assertEqual([q[1] for q in qs], ['Q-002', 'Q-003'])
        overdue, undated = O.classify([(s, q, t, t) for s, q, t in qs], TODAY)
        self.assertEqual([x['id'] for x in overdue], ['Q-002'])
        self.assertEqual([x['id'] for x in undated], ['Q-003'])

    def test_real_repo_runs(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(O.main(['--today', '2026-11-25']), 0)
        self.assertIn('Vencidos', buf.getvalue())


class WeeklyTests(unittest.TestCase):
    def test_week_title_uses_monday(self):
        self.assertEqual(W.week_start(datetime.date(2026, 11, 25)), datetime.date(2026, 11, 23))
        self.assertEqual(W.title_for(datetime.date(2026, 11, 29)), 'Relatório de status — semana de 2026-11-23')

    def test_render_fills_template(self):
        body = W.render(TODAY)
        self.assertIn('semana de 2026-11-23', body)
        self.assertIn('| SPEC-001 |', body)
        self.assertNotIn('AAAA-MM-DD', body)
        self.assertNotIn('<item com link>', body)

    def test_issue_not_duplicated(self):
        created = []

        def fake(args, payload=None, token=None):
            if args[:2] == ['issue', 'list']:
                return 0, json.dumps([{'number': 9, 'title': W.title_for(TODAY)}]), ''
            created.append(args)
            return 0, 'url', ''
        with mock.patch.object(G, 'gh', fake), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(W.main(['--today', '2026-11-25', '--issue']), 0)
        self.assertEqual(created, [])
        self.assertIn('#9', out.getvalue())

    def test_issue_created_with_label(self):
        created = []

        def fake(args, payload=None, token=None):
            if args[:2] == ['issue', 'list']:
                return 0, '[]', ''
            created.append(args)
            return 0, 'https://x/issues/1', ''
        with mock.patch.object(G, 'gh', fake), contextlib.redirect_stdout(io.StringIO()):
            W.main(['--today', '2026-11-25', '--issue'])
        self.assertEqual(len(created), 1)
        self.assertIn('status-report', created[0])

    def test_missing_label_falls_back_without_label(self):
        calls = []

        def fake(args, payload=None, token=None):
            calls.append(args)
            if args[:2] == ['issue', 'list']:
                return 0, '[]', ''
            if '--label' in args:
                return 1, '', "could not add label: 'status-report' not found"
            return 0, 'url', ''
        buf = io.StringIO()
        with mock.patch.object(G, 'gh', fake), contextlib.redirect_stdout(buf):
            self.assertEqual(W.main(['--today', '2026-11-25', '--issue']), 0)
        self.assertIn('setup-labels-milestones.py --apply', buf.getvalue())
        self.assertNotIn('--label', calls[-1])

    def test_no_permission_degrades(self):
        buf = io.StringIO()
        with mock.patch.object(G, 'gh', lambda *a, **k: (1, '', 'HTTP 403')), contextlib.redirect_stdout(buf):
            self.assertEqual(W.main(['--today', '2026-11-25', '--issue']), 0)
        self.assertIn('::warning::', buf.getvalue())


class NudgeTests(unittest.TestCase):
    ISSUE = {'number': 4, 'created_at': '2026-11-01T10:00:00Z', 'assignees': [{'login': 'ana'}]}

    def test_old_block_is_nudged_with_assignee(self):
        ev = [{'event': 'labeled', 'label': {'name': 'bloqueado'}, 'created_at': '2026-11-10T10:00:00Z'}]
        msg = N.due(self.ISSUE, ev, [], TODAY)
        self.assertIn('@ana', msg)
        self.assertIn('desde 2026-11-10', msg)

    def test_recent_block_is_not_nudged(self):
        ev = [{'event': 'labeled', 'label': {'name': 'bloqueado'}, 'created_at': '2026-11-22T10:00:00Z'}]
        self.assertIsNone(N.due(self.ISSUE, ev, [], TODAY))

    def test_no_double_nudge_within_7_days(self):
        prev = [{'body': f'{N.MARKER} 2026-11-20 -->\ntexto'}]
        self.assertIsNone(N.due(self.ISSUE, [], prev, TODAY))
        old = [{'body': f'{N.MARKER} 2026-11-10 -->\ntexto'}]
        self.assertIsNotNone(N.due(self.ISSUE, [], old, TODAY))

    def test_no_assignee_message(self):
        issue = dict(self.ISSUE, assignees=[])
        self.assertIn('sem responsável', N.due(issue, [], [], TODAY))

    def test_listing_failure_degrades(self):
        buf = io.StringIO()
        with mock.patch.object(G, 'gh', lambda *a, **k: (1, '', 'HTTP 403')), contextlib.redirect_stdout(buf):
            self.assertEqual(N.main([]), 0)
        self.assertIn('::warning::', buf.getvalue())


if __name__ == '__main__':
    unittest.main()
