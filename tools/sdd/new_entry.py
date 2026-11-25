#!/usr/bin/env python3
"""Cria a entrada do diário do dia a partir do template (`make new-entry`).

Cria journal/<usuario-github>/<AAAA-MM-DD>/entry.md com data e autor preenchidos
(docs/templates/journal-entry-template.md). A data padrão é hoje (hora local); o usuário
padrão é o login do GitHub (`gh api user`). Recusa sobrescrever uma entrada existente.
O campo "Escrita com IA" fica como no template: o autor escolhe "sim" ou "não".

Uso: python3 tools/sdd/new_entry.py [--date AAAA-MM-DD] [--user USUARIO] [--root DIR]
Somente biblioteca padrão do Python 3. Saída: 0 criada; 1 recusa ou erro.
"""
import datetime
import pathlib
import re
import subprocess
import sys

DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]
TEMPLATE = 'docs/templates/journal-entry-template.md'
USER_RE = re.compile(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?')


class NewEntryError(Exception):
    pass


def github_login():
    try:
        r = subprocess.run(['gh', 'api', 'user', '--jq', '.login'], capture_output=True, text=True, encoding='utf-8')
    except OSError:
        return ''
    return r.stdout.strip() if r.returncode == 0 else ''


def create(root, date=None, user=None):
    date = date or datetime.date.today().isoformat()
    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        raise NewEntryError(f'data inválida: {date!r} (use AAAA-MM-DD)')
    user = user or github_login()
    if not user:
        raise NewEntryError('não consegui descobrir o usuário do GitHub; informe --user (make new-entry U=login)')
    if not USER_RE.fullmatch(user):
        raise NewEntryError(f'usuário do GitHub inválido: {user!r}')
    template = root / TEMPLATE
    if not template.exists():
        raise NewEntryError(f'template ausente: {TEMPLATE}')
    target = root / 'journal' / user / date / 'entry.md'
    if target.exists():
        raise NewEntryError(f'já existe: {target.relative_to(root).as_posix()} (edite a entrada do dia)')
    text = template.read_bytes().decode('utf-8').replace('\r\n', '\n')
    text = text.replace('AAAA-MM-DD', date).replace('usuario-github', user)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(text.encode('utf-8'))
    return target


def main(argv):
    opts = {}
    it = iter(argv)
    for a in it:
        if a in ('--date', '--user', '--root'):
            opts[a] = next(it, '')
        else:
            print(f'argumento desconhecido: {a}\nuso: python3 tools/sdd/new_entry.py [--date AAAA-MM-DD] [--user USUARIO] [--root DIR]',
                  file=sys.stderr)
            return 1
    root = pathlib.Path(opts['--root']) if opts.get('--root') else DEFAULT_ROOT
    try:
        target = create(root, opts.get('--date') or None, opts.get('--user') or None)
    except NewEntryError as e:
        print(f'ERRO: {e}', file=sys.stderr)
        return 1
    print(f'criada: {target.relative_to(root).as_posix()}')
    print('Preencha o texto e escolha "sim" ou "não" em **Escrita com IA:**; depois rode make verify.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
