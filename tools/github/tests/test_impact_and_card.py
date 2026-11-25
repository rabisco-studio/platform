import contextlib
import io
import json
import os
import unittest
from unittest import mock

import support
import ghlib as G
import impact_comment as I
import move_card as M

TASKS_1 = '### T-001 base\n**Requisito:** FR-001\n**Dependências:** nenhuma\n'
TASKS_2 = '### T-001 usa a 001\n**Requisito:** FR-001\n**Dependências:** SPEC-001 T-001\n'
TASKS_3 = '### T-001 usa a 002\n**Requisito:** FR-001\n**Dependências:** SPEC-002 T-001\n'
TRACE = ('requisito,prioridade,release,spec_dona,spec_estado,fr,tarefas,situacao\n'
         'RF-01.1,Must,R1,SPEC-001,escrita,SPEC-001/FR-001,T-001,especificado\n'
         'RF-02.1,Must,R1,SPEC-002,escrita,SPEC-002/FR-001,T-001,especificado\n'
         'RF-09.1,Must,R2,SPEC-018,planejada,,,pendente\n')


def fixture():
    r = support.TmpRepo()
    for d, t in (('001-a', TASKS_1), ('002-b', TASKS_2), ('003-c', TASKS_3)):
        r.write(f'.ai/sdd/specs/{d}/tasks.md', t)
        r.write(f'.ai/sdd/specs/{d}/requirements.md', '# r\n')
        r.write(f'.ai/sdd/specs/{d}/design.md', '# d\n' + ('usa ADR-004 e contracts/document-format/tile.json\n' if d == '001-a' else ''))
    r.write('docs/requirements/traceability.csv', TRACE)
    return r


class ImpactTests(unittest.TestCase):
    def setUp(self):
        self.r = fixture()
        self.addCleanup(self.r.cleanup)

    def test_spec_with_transitive_dependents(self):
        res = I.compute(['.ai/sdd/specs/001-a/requirements.md'], self.r.path)
        self.assertEqual(res['specs'], ['SPEC-001'])
        self.assertEqual(list(res['dependents']), ['SPEC-002', 'SPEC-003'])  # 003 via 002 (transitivo)
        self.assertEqual(res['dependents']['SPEC-003'], ['SPEC-002'])
        self.assertIn('RF-01.1', res['reqs'])
        self.assertNotIn('RF-02.1', res['reqs'])

    def test_leaf_spec_has_no_dependents(self):
        res = I.compute(['.ai/sdd/specs/003-c/design.md'], self.r.path)
        self.assertEqual(res['dependents'], {})

    def test_adr_and_contract_find_citing_specs(self):
        res = I.compute(['docs/adr/ADR-004-x.md', 'contracts/document-format/tile.json'], self.r.path)
        self.assertEqual(res['citing']['SPEC-001'], ['ADR-004', 'contracts/document-format/tile.json'])
        self.assertIn('SPEC-002', res['dependents'])

    def test_catalog_change_lists_changed_requirement(self):
        base = 'id,x\nRF-01.1,a\nRF-09.1,b\n'
        self.r.write(I.REQ_CAT, 'id,x\nRF-01.1,a\nRF-09.1,CHANGED\n')
        res = I.compute([I.REQ_CAT], self.r.path, {I.REQ_CAT: base})
        self.assertEqual(res['cat_reqs'], ['RF-09.1'])
        self.assertIn('RF-09.1', res['reqs'])

    def test_irrelevant_pr_has_no_comment(self):
        self.assertIsNone(I.compute(['README.md', 'tools/x.py'], self.r.path))

    def test_render_has_marker_and_sections(self):
        body = I.render(I.compute(['.ai/sdd/specs/001-a/requirements.md'], self.r.path))
        self.assertTrue(body.startswith(I.MARKER))
        for s in ('RF-01.1', 'SPEC-002', 'SPEC-003', 'Specs dependentes'):
            self.assertIn(s, body)

    def test_upsert_updates_existing_comment(self):
        calls = []

        def fake(args, payload=None, token=None):
            calls.append((args, payload))
            if args[0] == 'api' and 'comments?per_page' in args[1]:
                return 0, json.dumps([{'id': 7, 'body': I.MARKER + ' antigo'}]), ''
            return 0, '{}', ''
        with mock.patch.object(G, 'gh', fake):
            ok, _ = I.upsert_comment('o/r', 5, I.MARKER + ' novo')
        self.assertTrue(ok)
        self.assertEqual(calls[-1][0][:3], ['api', '-X', 'PATCH'])
        self.assertIn('issues/comments/7', calls[-1][0][3])

    def test_upsert_creates_when_absent(self):
        calls = []

        def fake(args, payload=None, token=None):
            calls.append(args)
            return (0, '[]', '') if 'per_page' in args[1] else (0, '{}', '')
        with mock.patch.object(G, 'gh', fake):
            I.upsert_comment('o/r', 5, 'x')
        self.assertEqual(calls[-1][:3], ['api', '-X', 'POST'])

    def test_permission_denied_degrades_with_exit_0(self):
        base = self.r.commit('base')
        self.r.write('.ai/sdd/specs/001-a/requirements.md', '# mudou\n')
        head = self.r.commit('muda')
        env = {'BASE_SHA': base, 'HEAD_SHA': head, 'PR_NUMBER': '3', 'GITHUB_REPOSITORY': 'o/r'}
        buf = io.StringIO()
        with mock.patch.object(L := I.L, 'ROOT', self.r.path), \
                mock.patch.object(G, 'ROOT', self.r.path), \
                mock.patch.object(G, 'gh', lambda *a, **k: (1, '', 'HTTP 403: Resource not accessible by integration')), \
                mock.patch.dict(os.environ, env, clear=False), contextlib.redirect_stdout(buf):
            code = I.main([])
        self.assertEqual(code, 0)
        self.assertIn('::warning::', buf.getvalue())
        self.assertIn('Não consegui comentar', buf.getvalue())


ITEMS = [{'id': 'PVTI_1', 'spec': 'SPEC-001', 'title': 'SPEC-001 · Scene Graph', 'status': 'Requisitos'},
         {'id': 'PVTI_2', 'spec': 'SPEC-002', 'title': 'SPEC-002 · Formato', 'status': 'Design'}]
FIELDS = [{'id': 'F_status', 'name': 'Status', 'options': [
    {'id': 'o1', 'name': 'Ideia'}, {'id': 'o2', 'name': 'Requisitos'}, {'id': 'o3', 'name': 'Design'},
    {'id': 'o4', 'name': 'Tarefas'}, {'id': 'o5', 'name': 'Implementação'}, {'id': 'o6', 'name': 'Revisão'},
    {'id': 'o7', 'name': 'Feito'}]}]


class MoveCardTests(unittest.TestCase):
    def test_column_table_covers_all_stages(self):
        import sddlib as L
        self.assertEqual(set(M.COLUMN_OF), set(L.STAGES))

    def test_plan_moves_card(self):
        actions, warns = M.plan([('SPEC-001', 'requirements:approved')], ITEMS, FIELDS)
        self.assertEqual(actions, [('SPEC-001', 'PVTI_1', 'Design', 'o3', 'F_status')])
        self.assertEqual(warns, [])

    def test_plan_missing_card_warns(self):
        actions, warns = M.plan([('SPEC-099', 'design:draft')], ITEMS, FIELDS)
        self.assertEqual(actions, [])
        self.assertIn('card não encontrado', warns[0])

    def test_plan_already_in_column(self):
        actions, _ = M.plan([('SPEC-002', 'design:draft')], ITEMS, FIELDS)
        self.assertEqual(actions, [])

    def test_find_project_by_title_or_number(self):
        ps = [{'number': 4, 'title': 'Outro'}, {'number': 1, 'title': 'Rabisco Studio'}]
        self.assertEqual(M.find_project(ps)['number'], 1)
        self.assertEqual(M.find_project(ps, 4)['number'], 4)
        self.assertIsNone(M.find_project(ps, 9))

    def test_changed_status_from_git(self):
        r = support.TmpRepo()
        self.addCleanup(r.cleanup)
        r.write('.ai/sdd/specs/001-a/.status', 'requirements:draft\n')
        base = r.commit('a')
        r.write('.ai/sdd/specs/001-a/.status', 'requirements:approved\n')
        r.write('README.md', 'x')
        head = r.commit('b')
        self.assertEqual(M.changed_status(base, head, r.path), [('SPEC-001', 'requirements:approved')])

    def test_without_token_only_warns(self):
        r = support.TmpRepo()
        self.addCleanup(r.cleanup)
        r.write('.ai/sdd/specs/001-a/.status', 'requirements:draft\n')
        base = r.commit('a')
        r.write('.ai/sdd/specs/001-a/.status', 'design:approved\n')
        head = r.commit('b')
        env = {'BASE_SHA': base, 'HEAD_SHA': head, 'PROJECT_TOKEN': ''}
        buf = io.StringIO()
        with mock.patch.object(G, 'ROOT', r.path), mock.patch.dict(os.environ, env), \
                mock.patch.object(G, 'gh', side_effect=AssertionError('não deve chamar o gh')), \
                contextlib.redirect_stdout(buf):
            code = M.main([])
        self.assertEqual(code, 0)
        self.assertIn('PROJECT_TOKEN ausente', buf.getvalue())
        self.assertIn('SPEC-001 -> Tarefas', buf.getvalue())

    def test_with_token_edits_card(self):
        r = support.TmpRepo()
        self.addCleanup(r.cleanup)
        r.write('.ai/sdd/specs/001-a/.status', 'requirements:draft\n')
        base = r.commit('a')
        r.write('.ai/sdd/specs/001-a/.status', 'requirements:approved\n')
        head = r.commit('b')
        edits = []

        def fake_json(args, token=None):
            if args[:2] == ['project', 'list']:
                return {'projects': [{'number': 1, 'id': 'PVT_1', 'title': 'Rabisco Studio'}]}
            if args[:2] == ['project', 'item-list']:
                return {'items': ITEMS}
            return {'fields': FIELDS}

        def fake_gh(args, payload=None, token=None):
            edits.append(args)
            return 0, '', ''
        env = {'BASE_SHA': base, 'HEAD_SHA': head, 'PROJECT_TOKEN': 'tok'}
        with mock.patch.object(G, 'ROOT', r.path), mock.patch.dict(os.environ, env), \
                mock.patch.object(G, 'gh_json', fake_json), mock.patch.object(G, 'gh', fake_gh), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(M.main([]), 0)
        self.assertEqual(len(edits), 1)
        self.assertIn('o3', edits[0])  # opção Design
        self.assertIn('PVTI_1', edits[0])


if __name__ == '__main__':
    unittest.main()
