import subprocess
import sys
import unittest

import support
import new_spec as N


class SanitizeTests(unittest.TestCase):
    def test_examples_removed_everywhere(self):
        for doc, rel in N.TEMPLATES.items():
            text = N.sanitize((support.ROOT / rel).read_text(encoding='utf-8'), doc)
            for bad in (r'^### (?:US|N?FR|D|Q|TD|T)-\d{3}', r'^\|\s*(?:N?FR|TD|T)-\d{3}\s*\|'):
                self.assertNotRegex(text, __import__('re').compile(bad, __import__('re').M), f'{doc}: {bad}')

    def test_tasks_heading_matches_checker(self):
        text = N.sanitize((support.ROOT / N.TEMPLATES['tasks.md']).read_text(encoding='utf-8'), 'tasks.md')
        self.assertIn('## Cobertura FR/NFR → Tarefas', text)


class NormalizeTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(N.normalize('18'), '018')
        self.assertEqual(N.normalize('SPEC-018'), '018')
        for bad in ('', 'abc', '0', '1000'):
            with self.assertRaises(N.NewSpecError):
                N.normalize(bad)


class CreateTests(unittest.TestCase):
    def setUp(self):
        self.tmp, self.root = support.copy_repo()
        self.addCleanup(self.tmp.cleanup)

    def run_tool(self, script, *args):
        return subprocess.run([sys.executable, str(self.root / 'tools/sdd' / script), *args], cwd=str(self.root),
                              capture_output=True, text=True, encoding='utf-8')

    def test_creates_spec_that_passes_verify(self):
        r = self.run_tool('new_spec.py', '018')
        self.assertEqual(r.returncode, 0, r.stderr)
        folder = self.root / '.ai/sdd/specs/018-identity'
        self.assertEqual((folder / '.status').read_text(encoding='utf-8'), 'requirements:draft\n')
        req = (folder / 'requirements.md').read_text(encoding='utf-8')
        for field in ('**Área:** backend', '**Release:** R2', '**Rigor:** anchored', '**ADRs:** nenhuma', '**Depende de:**'):
            self.assertIn(field, req)
        self.assertIn('RF-01.1', req)
        for doc in ('design.md', 'tasks.md'):
            self.assertIn('rascunho antecipado; não vinculante', (folder / doc).read_text(encoding='utf-8'))
        self.assertIn('018,identity,Identidade e autenticação,backend,5,R2,anchored,escrita',
                      (self.root / 'docs/requirements/spec-catalog.csv').read_text(encoding='utf-8'))
        # equivalente ao `make verify`: gerador + sdd-check (também --strict)
        self.assertEqual(self.run_tool('generate.py').returncode, 0)
        chk = self.run_tool('sdd_check.py', '--strict')
        self.assertEqual(chk.returncode, 0, chk.stdout)
        self.assertIn('0 erro(s), 0 aviso(s)', chk.stdout)
        self.assertIn('SPEC-018', (self.root / '.ai/sdd/INDEX.md').read_text(encoding='utf-8'))

    def test_adrs_come_from_catalog_title(self):
        self.assertEqual(self.run_tool('new_spec.py', '021').returncode, 0)
        req = (self.root / '.ai/sdd/specs/021-sync-protocol/requirements.md').read_text(encoding='utf-8')
        self.assertIn('**ADRs:** ADR-008, ADR-009', req)
        self.assertIn('**Tags:** contract', req)

    def test_refuses_existing_folder_without_changes(self):
        (self.root / '.ai/sdd/specs/018-identity').mkdir()
        before = (self.root / 'docs/requirements/spec-catalog.csv').read_text(encoding='utf-8')
        r = self.run_tool('new_spec.py', '018')
        self.assertEqual(r.returncode, 1)
        self.assertIn('já existe', r.stderr)
        self.assertEqual(before, (self.root / 'docs/requirements/spec-catalog.csv').read_text(encoding='utf-8'))

    def test_refuses_written_and_unknown_specs(self):
        self.assertIn('já está "escrita"', self.run_tool('new_spec.py', '001').stderr)
        self.assertIn('não existe', self.run_tool('new_spec.py', '999').stderr)
        self.assertEqual(self.run_tool('new_spec.py').returncode, 2)

    def test_second_run_is_refused(self):
        self.assertEqual(self.run_tool('new_spec.py', '018').returncode, 0)
        self.assertEqual(self.run_tool('new_spec.py', '018').returncode, 1)


if __name__ == '__main__':
    unittest.main()
