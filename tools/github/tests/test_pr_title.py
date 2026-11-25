import unittest

import support  # noqa: F401
import check_pr_title as T

VALID = [
    'SPEC-001: mapeia FR-012 no design',
    'ADR-019: cache de tiles',
    'GOV: atualiza o RACI',
    'contracts: tile-schema',
    'feat 001 T-004: DocumentMeta e perfil de cor',
    'feat/001-T-004: DocumentMeta e perfil de cor',
]
INVALID = [
    '',
    'atualiza readme',
    'SPEC-1: curto demais',
    'SPEC-001 sem dois pontos',
    'SPEC-001:',
    'gov: minúsculo',
    'feat(core): estilo conventional',
    'feat 001 T-4: id curto',
    'fix: algo',
]


class TitleTests(unittest.TestCase):
    def test_valid(self):
        for t in VALID:
            self.assertTrue(T.is_valid(t), t)

    def test_invalid(self):
        for t in INVALID:
            self.assertFalse(T.is_valid(t), t)

    def test_exit_codes(self):
        self.assertEqual(T.main(['x', 'GOV: ok']), 0)
        self.assertEqual(T.main(['x', 'qualquer coisa']), 1)

    def test_help_has_examples(self):
        self.assertIn('SPEC-001:', T.HELP)
        self.assertIn('feat/001-T-004:', T.HELP)


if __name__ == '__main__':
    unittest.main()
