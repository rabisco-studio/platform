import subprocess
import sys
import unittest

import support

ENTRY = '# Diário — {d}\n\n**Data:** {d}\n**Autor:** {u}\n**Escrita com IA:** não\n\n## Resumo do dia\nfeito.\n'


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp, self.root = support.copy_repo()
        self.addCleanup(self.tmp.cleanup)

    def check(self):
        r = subprocess.run([sys.executable, str(self.root / 'tools/sdd/sdd_check.py'), '--strict'], cwd=str(self.root),
                           capture_output=True, text=True, encoding='utf-8')
        return r.returncode, r.stdout

    def add(self, rel, text):
        support.write(self.root, rel, text)

    def test_real_repo_journal_passes(self):
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_valid_entry_passes(self):
        self.add('journal/ana-souza/2026-12-01/entry.md', ENTRY.format(d='2026-12-01', u='ana-souza'))
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_wrong_file_name_or_depth_fails(self):
        self.add('journal/ana-souza/2026-12-01/notas.md', 'x')
        self.add('journal/ana-souza/entry.md', 'x')
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(out.count('fora do padrão journal/'), 2, out)

    def test_invalid_date_fails(self):
        self.add('journal/ana-souza/2026-13-45/entry.md', ENTRY.format(d='2026-13-45', u='ana-souza'))
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn('data inválida', out)

    def test_header_must_match_folder(self):
        self.add('journal/ana-souza/2026-12-01/entry.md', ENTRY.format(d='2026-12-02', u='outra-pessoa'))
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn('**Data:** deve ser 2026-12-01', out)
        self.assertIn('**Autor:** deve ser ana-souza', out)

    def test_template_itself_is_not_an_entry(self):
        # o template mora em docs/templates e usa placeholders; não pode ser tratado como entrada
        self.assertTrue((self.root / 'docs/templates/journal-entry-template.md').exists())
        code, out = self.check()
        self.assertEqual(code, 0, out)


if __name__ == '__main__':
    unittest.main()
