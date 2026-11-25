import subprocess
import sys
import unittest
from unittest import mock

import support
import new_entry as E


class NewEntryTests(unittest.TestCase):
    def setUp(self):
        self.tmp, self.root = support.copy_repo()
        self.addCleanup(self.tmp.cleanup)

    def check(self):
        r = subprocess.run([sys.executable, str(self.root / 'tools/sdd/sdd_check.py'), '--strict'], cwd=str(self.root),
                           capture_output=True, text=True, encoding='utf-8')
        return r.returncode, r.stdout

    def test_creates_entry_that_passes_sdd_check(self):
        target = E.create(self.root, '2026-12-01', 'ana-souza')
        self.assertEqual(target.relative_to(self.root).as_posix(), 'journal/ana-souza/2026-12-01/entry.md')
        text = target.read_text(encoding='utf-8')
        self.assertIn('# Diário — 2026-12-01', text)
        self.assertIn('**Autor:** ana-souza', text)
        self.assertNotIn('AAAA-MM-DD', text)
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_refuses_to_overwrite(self):
        E.create(self.root, '2026-12-01', 'ana-souza')
        with self.assertRaises(E.NewEntryError):
            E.create(self.root, '2026-12-01', 'ana-souza')

    def test_invalid_date_and_user(self):
        for date, user in (('2026-13-45', 'ana'), ('01/12/2026', 'ana'), ('2026-12-01', '../x'), ('2026-12-01', 'a b')):
            with self.assertRaises(E.NewEntryError, msg=(date, user)):
                E.create(self.root, date, user)

    def test_defaults_to_today_and_github_login(self):
        with mock.patch.object(E, 'github_login', return_value='bia-lima'):
            target = E.create(self.root)
        self.assertEqual(target.parent.parent.name, 'bia-lima')
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_without_login_asks_for_user(self):
        with mock.patch.object(E, 'github_login', return_value=''):
            with self.assertRaises(E.NewEntryError):
                E.create(self.root, '2026-12-01')

    def test_cli_exit_codes(self):
        run = lambda *a: subprocess.run([sys.executable, str(self.root / 'tools/sdd/new_entry.py'), '--root', str(self.root), *a],  # noqa: E731
                                        capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(run('--date', '2026-12-02', '--user', 'ana-souza').returncode, 0)
        self.assertEqual(run('--date', '2026-12-02', '--user', 'ana-souza').returncode, 1)
        self.assertEqual(run('--bogus').returncode, 1)


if __name__ == '__main__':
    unittest.main()
