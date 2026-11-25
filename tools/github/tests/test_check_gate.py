import unittest

import support
import check_gate as C

ALICE = ('Alice Autora', 'alice@example.com')
BOB = ('Bob Aprovador', 'bob@example.com')
BODY_OK = '## Gate\nSPEC-001 · G1\n\n## Registro da revisão\nok\n'
SPEC = '001-scene-graph'
OK = lambda repo=None: (0, '')  # noqa: E731


def make_repo(status='requirements:draft'):
    r = support.TmpRepo()
    for d in C.DOCS:
        r.write(f'.ai/sdd/specs/{SPEC}/{d}', f'# {d}\n\n**Status:** {status}\n\ncorpo original\n')
    r.write(f'.ai/sdd/specs/{SPEC}/.status', status + '\n')
    base = r.commit('SPEC-001: escreve', author=ALICE)
    return r, base


def env(base, head, author='bob', body=BODY_OK, **kw):
    return dict(BASE_SHA=base, HEAD_SHA=head, PR_AUTHOR=author, PR_BODY=body, **kw)


def set_status(r, new, headers=True):
    r.write(f'.ai/sdd/specs/{SPEC}/.status', new + '\n')
    if headers:
        for d in C.DOCS:
            p = r.path / f'.ai/sdd/specs/{SPEC}/{d}'
            lines = p.read_text(encoding='utf-8').splitlines()
            lines = [f'**Status:** {new}' if l.startswith('**Status:**') else l for l in lines]
            p.write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')


class TransitionTests(unittest.TestCase):
    def test_transitions(self):
        self.assertIsNone(C.check_transition('requirements:draft', 'requirements:approved'))
        self.assertIsNone(C.check_transition('design:approved', 'requirements:draft'))  # reabertura
        self.assertIsNone(C.check_transition(None, 'requirements:draft'))
        self.assertIn('pula', C.check_transition('requirements:draft', 'design:approved'))
        self.assertIn('desconhecido', C.check_transition('requirements:draft', 'foo:bar'))
        self.assertIn('começar', C.check_transition(None, 'design:draft'))

    def test_author_matching(self):
        self.assertTrue(C.author_matches('alice', [], 'alice', 'x@y.z'))
        self.assertTrue(C.author_matches('alice', [], 'Fulana', '123+alice@users.noreply.github.com'))
        self.assertTrue(C.author_matches('alice', ['fulana@corp.com'], 'F', 'fulana@corp.com'))
        self.assertFalse(C.author_matches('bob', [], 'Alice', 'alice@example.com'))


class GateTests(unittest.TestCase):
    def setUp(self):
        self.r, self.base = make_repo()
        self.addCleanup(self.r.cleanup)

    def head(self, new, headers=True, author=BOB):
        set_status(self.r, new, headers)
        return self.r.commit('GOV: gate', author=author)

    def run_eval(self, head, **kw):
        e = env(self.base, head, **{k: v for k, v in kw.items() if k in ('author', 'body')})
        e.update({k: v for k, v in kw.items() if k not in ('author', 'body', 'sdd', 'member')})
        return C.evaluate(e, repo=self.r.path, sdd_check=kw.get('sdd', OK), member=kw.get('member', lambda *a: True))

    def test_valid_gate_other_author_warns_without_token(self):
        errors, warns = self.run_eval(self.head('requirements:approved'))
        self.assertEqual(errors, [])
        self.assertTrue(any('ORG_READ_TOKEN' in w for w in warns))

    def test_not_a_gate_pr(self):
        self.r.write('docs/x.md', 'x')
        head = self.r.commit('doc', author=BOB)
        errors, warns = self.run_eval(head)
        self.assertEqual(errors, [])
        self.assertIn('não é um PR de gate', warns[0])

    def test_author_wrote_the_spec(self):
        errors, _ = self.run_eval(self.head('requirements:approved'), author='alice')
        self.assertTrue(any(e.startswith('(b)') and 'autor não aprova' in e for e in errors), errors)

    def test_alias_catches_other_email(self):
        errors, _ = self.run_eval(self.head('requirements:approved'), author='maria', GATE_AUTHOR_ALIASES='alice@example.com')
        self.assertTrue(any(e.startswith('(b)') for e in errors), errors)

    def test_skipped_stage(self):
        errors, _ = self.run_eval(self.head('design:approved'))
        self.assertTrue(any(e.startswith('(a)') and 'pula' in e for e in errors), errors)

    def test_unknown_stage(self):
        errors, _ = self.run_eval(self.head('foo:bar'))
        self.assertTrue(any(e.startswith('(a)') for e in errors), errors)

    def test_body_without_template(self):
        errors, _ = self.run_eval(self.head('requirements:approved'), body='só texto')
        self.assertTrue(any(e.startswith('(d)') for e in errors), errors)

    def test_sdd_check_failure_is_reported(self):
        errors, _ = self.run_eval(self.head('requirements:approved'), sdd=lambda repo=None: (1, 'ERRO cabeçalho'))
        self.assertTrue(any(e.startswith('(c)') and 'cabeçalho' in e for e in errors), errors)

    def test_pr_changes_more_than_header(self):
        p = self.r.path / f'.ai/sdd/specs/{SPEC}/requirements.md'
        p.write_text(p.read_text(encoding='utf-8') + '\nnovo requisito escondido\n', encoding='utf-8', newline='\n')
        errors, _ = self.run_eval(self.head('requirements:approved'))
        self.assertTrue(any('mais que o cabeçalho' in e for e in errors), errors)

    def test_reopen_is_allowed(self):
        self.r.write(f'.ai/sdd/specs/{SPEC}/.status', 'design:approved\n')
        base = self.r.commit('estado', author=ALICE)
        set_status(self.r, 'requirements:draft')
        head = self.r.commit('GOV: reabre', author=BOB)
        errors, _ = C.evaluate(env(base, head), repo=self.r.path, sdd_check=OK)
        self.assertEqual(errors, [])

    def test_team_membership(self):
        head = self.head('requirements:approved')
        errors, _ = self.run_eval(head, ORG_READ_TOKEN='x', member=lambda login, team, tok: team == 'product')
        self.assertEqual(errors, [])
        errors, _ = self.run_eval(head, ORG_READ_TOKEN='x', member=lambda *a: False)
        self.assertTrue(any('equipe aprovadora' in e for e in errors), errors)
        _, warns = self.run_eval(head, ORG_READ_TOKEN='x', member=lambda *a: None)
        self.assertTrue(any('não consegui consultar' in w for w in warns), warns)

    def test_new_spec_must_start_at_draft(self):
        self.r.write('.ai/sdd/specs/009-nova/.status', 'design:approved\n')
        head = self.r.commit('nova', author=BOB)
        errors, _ = self.run_eval(head)
        self.assertTrue(any('009-nova' in e and 'começar' in e for e in errors), errors)


if __name__ == '__main__':
    unittest.main()
