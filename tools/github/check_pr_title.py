#!/usr/bin/env python3
"""Valida o título de um PR: só os prefixos do projeto (README, seção 5).

Uso:  PR_TITLE='SPEC-001: algo' python3 tools/github/check_pr_title.py
      python3 tools/github/check_pr_title.py "GOV: algo"
O título vem por variável de ambiente ou argumento, nunca interpolado em shell.
Saída: 0 válido; 1 inválido.
"""
import os
import re
import sys

PATTERNS = [
    re.compile(r'^SPEC-\d{3}: \S'),
    re.compile(r'^ADR-\d{3}: \S'),
    re.compile(r'^GOV: \S'),
    re.compile(r'^contracts: \S'),
    re.compile(r'^feat \d{3} T-\d{3}: \S'),
    re.compile(r'^feat/\d{3}-T-\d{3}: \S'),
]

HELP = '''Título de PR inválido: "{title}"

Use um dos prefixos (README, seção 5), seguido de ": " e do assunto:
  SPEC-001: mapeia FR-012 no design
  ADR-019: cache de tiles
  GOV: atualiza o RACI
  contracts: tile-schema
  feat 001 T-004: DocumentMeta e perfil de cor
  feat/001-T-004: DocumentMeta e perfil de cor
'''


def is_valid(title):
    return bool(title) and any(p.match(title) for p in PATTERNS)


def main(argv):
    title = argv[1] if len(argv) > 1 else os.environ.get('PR_TITLE', '')
    if is_valid(title):
        print(f'Título válido: {title}')
        return 0
    print('::error title=Título de PR inválido::' + HELP.format(title=title).replace('\n', '%0A'))
    print(HELP.format(title=title), file=sys.stderr)
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
