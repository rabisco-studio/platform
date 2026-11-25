import subprocess
import sys
import unittest

import support


class NamingGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp, self.root = support.copy_repo()
        self.addCleanup(self.tmp.cleanup)

    def check(self):
        r = subprocess.run([sys.executable, str(self.root / 'tools/sdd/sdd_check.py'), '--strict'], cwd=str(self.root),
                           capture_output=True, text=True, encoding='utf-8')
        return r.returncode, r.stdout

    def test_real_repo_passes(self):
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_forbidden_name_fails(self):
        support.write(self.root, 'docs/notas.md', 'O arquivo termina em .hybrid e o crate é hybrid-schema.\n')
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn('nomenclatura proibida', out)
        self.assertEqual(out.count('docs/notas.md:1'), 2, out)

    def test_hlc_and_conceptual_hybrid_are_allowed(self):
        support.write(self.root, 'docs/notas.md', 'Usa HybridLogicalClock e o motor híbrido (raster + vetor).\n')
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_allow_list_exempts_a_file(self):
        support.write(self.root, 'docs/notas.md', 'Antes era .hybrid.\n')
        allow = self.root / 'tools/sdd/naming-allow.txt'
        text = allow.read_text(encoding='utf-8')
        allow.write_text(text + '\ndocs/notas.md: ' + r'\.hybrid\b' + ': histórico\n', encoding='utf-8')
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_malformed_allow_line_fails(self):
        allow = self.root / 'tools/sdd/naming-allow.txt'
        text = allow.read_text(encoding='utf-8')
        allow.write_text(text + '\nsó-um-campo\n', encoding='utf-8')
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn('formato esperado', out)


if __name__ == '__main__':
    unittest.main()
