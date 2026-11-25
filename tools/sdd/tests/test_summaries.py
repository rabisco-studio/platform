import re
import subprocess
import sys
import unittest

import support

SPEC_SUMMARY = '.ai/sdd/specs/spec-summary.md'


class SummaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp, self.root = support.copy_repo()
        self.addCleanup(self.tmp.cleanup)

    def check(self):
        r = subprocess.run([sys.executable, str(self.root / 'tools/sdd/sdd_check.py'), '--strict'], cwd=str(self.root),
                           capture_output=True, text=True, encoding='utf-8')
        return r.returncode, r.stdout

    def test_real_repo_summaries_pass(self):
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_new_adr_must_be_cited(self):
        support.write(self.root, 'docs/adr/ADR-019-nova.md', '# ADR-019 — Nova\n\n**Status:** Proposta\n')
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn('adr-summary.md: não cita docs/adr/ADR-019-nova.md', out)

    def test_new_governance_doc_must_be_cited(self):
        support.write(self.root, 'docs/governance/novo.md', '# Novo\n')
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn('governance-summary.md: não cita docs/governance/novo.md', out)

    def test_new_workflow_script_and_spike_must_be_cited(self):
        support.write(self.root, '.github/workflows/novo.yml', 'name: novo\non: push\njobs: {}\n')
        support.write(self.root, 'tools/github/novo_script.py', '# x\n')
        support.write(self.root, 'spikes/spike-f-novo/README.md', '# Spike (f)\n')
        code, out = self.check()
        self.assertEqual(code, 1)
        for needle in ('.github/workflows/README.md: não cita .github/workflows/novo.yml',
                       'tools-summary.md: não cita tools/github/novo_script.py',
                       'spike-summary.md: não cita spikes/spike-f-novo'):
            self.assertIn(needle, out)

    def test_missing_spec_row_fails(self):
        p = self.root / SPEC_SUMMARY
        text = p.read_text(encoding='utf-8')
        p.write_text(re.sub(r'^\| SPEC-037 \|.*\n', '', text, flags=re.M), encoding='utf-8', newline='\n')
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn('sem linha para SPEC-037', out)

    def test_unknown_spec_row_fails(self):
        p = self.root / SPEC_SUMMARY
        p.write_text(p.read_text(encoding='utf-8') + '| SPEC-099 | inventada | — |\n', encoding='utf-8', newline='\n')
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn('linha de SPEC-099, que não existe no catálogo', out)

    def test_written_spec_must_be_linked(self):
        p = self.root / SPEC_SUMMARY
        text = p.read_text(encoding='utf-8').replace('001-scene-graph/requirements.md', 'x/requirements.md')
        p.write_text(text, encoding='utf-8', newline='\n')
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn('SPEC-001 está escrita', out)

    def test_every_summary_is_in_the_documentation_map(self):
        p = self.root / 'docs/README.md'
        p.write_text(p.read_text(encoding='utf-8').replace('adr-summary.md', 'x.md'), encoding='utf-8', newline='\n')
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn('docs/README.md: não cita docs/adr/adr-summary.md', out)

    def test_new_spec_fills_the_summary_row(self):
        r = subprocess.run([sys.executable, str(self.root / 'tools/sdd/new_spec.py'), '018'], cwd=str(self.root),
                           capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn('AVISO', r.stderr)
        row = re.search(r'^\| SPEC-018 \|.*$', (self.root / SPEC_SUMMARY).read_text(encoding='utf-8'), flags=re.M).group(0)
        self.assertIn('[requirements](018-identity/requirements.md)', row)
        self.assertIn('[tasks](018-identity/tasks.md)', row)
        code, out = self.check()
        self.assertEqual(code, 0, out)


if __name__ == '__main__':
    unittest.main()
