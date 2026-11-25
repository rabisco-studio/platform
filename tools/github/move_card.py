#!/usr/bin/env python3
"""Move o card da spec no quadro quando um `.status` muda na main.

Tabela de colunas: README, seção 7. Usa `gh project item-edit` com o segredo PROJECT_TOKEN.
Sem o segredo, só avisa e imprime o que faria (sai com 0). Card inexistente: avisa (sai com 0).

Entrada (ambiente): BASE_SHA e HEAD_SHA (commits antes/depois do merge), PROJECT_TOKEN,
[PROJECT_NUMBER] (padrão: procura o projeto pelo título), [PROJECT_OWNER] (padrão rabisco-studio).
Opções: --dry-run  nunca escreve (mesmo com token).
"""
import os
import re
import sys

import ghlib as G

COLUMN_OF = {  # .status -> coluna (campo Status do quadro)
    'requirements:draft': 'Requisitos',
    'requirements:approved': 'Design',
    'design:draft': 'Design',
    'design:approved': 'Tarefas',
    'tasks:draft': 'Tarefas',
    'tasks:approved': 'Implementação',
    'implementation:in-progress': 'Implementação',
    'implementation:done': 'Revisão',
    'review:done': 'Feito',
}
PROJECT_TITLES = ('Rabisco Platform', 'Rabisco Studio')


def changed_status(base, head, repo=None):
    """[(SPEC-NNN, novo_status)] para cada .status alterado entre base e head."""
    out = []
    for f in G.git(['diff', '--name-only', base, head], cwd=repo).splitlines():
        m = re.fullmatch(r'\.ai/sdd/specs/(\d{3})-[^/]+/\.status', f)
        if m:
            status = G.git(['show', f'{head}:{f}'], cwd=repo, check=False).strip()
            if status:
                out.append((f'SPEC-{m.group(1)}', status))
    return out


def find_card(items, spec):
    for it in items:
        if (it.get('spec') or '').strip() == spec or (it.get('title') or '').startswith(spec):
            return it
    return None


def find_project(projects, number=None):
    for p in projects:
        if number and str(p.get('number')) == str(number):
            return p
        if not number and p.get('title') in PROJECT_TITLES:
            return p
    return None


def plan(moves, items, fields):
    """Devolve (ações, avisos). ação = (spec, card_id, coluna, option_id)."""
    status_field = next((f for f in fields if f.get('name') == 'Status'), None)
    actions, warns = [], []
    if not status_field:
        return [], ['campo Status não encontrado no quadro']
    options = {o['name'].lower(): o['id'] for o in status_field.get('options', [])}
    for spec, status in moves:
        col = COLUMN_OF.get(status)
        if not col:
            warns.append(f'{spec}: .status "{status}" sem coluna correspondente; nada a mover')
            continue
        card = find_card(items, spec)
        if not card:
            warns.append(f'{spec}: card não encontrado no quadro; nada a mover (crie o card da spec)')
            continue
        if col.lower() not in options:
            warns.append(f'{spec}: coluna "{col}" não existe no campo Status')
            continue
        if (card.get('status') or '') == col:
            print(f'{spec}: já está em {col}')
            continue
        actions.append((spec, card['id'], col, options[col.lower()], status_field['id']))
    return actions, warns


def main(argv):
    base, head = os.environ.get('BASE_SHA', ''), os.environ.get('HEAD_SHA', '')
    if not base or not head:
        print('BASE_SHA e HEAD_SHA são obrigatórios', file=sys.stderr)
        return 2
    moves = changed_status(base, head)
    if not moves:
        print('Nenhum .status alterado: nada a mover.')
        return 0
    token = os.environ.get('PROJECT_TOKEN', '')
    dry = '--dry-run' in argv
    if not token:
        G.warn('PROJECT_TOKEN ausente: não movo cards. Faria: ' +
               '; '.join(f'{s} -> {COLUMN_OF.get(st, "?")} ({st})' for s, st in moves))
        return 0
    owner = os.environ.get('PROJECT_OWNER', 'rabisco-studio')
    try:
        projects = (G.gh_json(['project', 'list', '--owner', owner, '--format', 'json'], token=token) or {}).get('projects', [])
        proj = find_project(projects, os.environ.get('PROJECT_NUMBER'))
        if not proj:
            G.warn(f'quadro não encontrado em {owner} (defina a variável PROJECT_NUMBER): nada movido')
            return 0
        num = str(proj['number'])
        items = G.gh_json(['project', 'item-list', num, '--owner', owner, '--format', 'json', '--limit', '200'], token=token)['items']
        fields = G.gh_json(['project', 'field-list', num, '--owner', owner, '--format', 'json'], token=token)['fields']
        actions, warns = plan(moves, items, fields)
        for w in warns:
            G.warn(w)
        for spec, card_id, col, option_id, field_id in actions:
            if dry:
                print(f'[dry-run] {spec}: moveria o card para {col}')
                continue
            code, out, err = G.gh(['project', 'item-edit', '--id', card_id, '--project-id', proj['id'],
                                   '--field-id', field_id, '--single-select-option-id', option_id], token=token)
            if code != 0:
                G.warn(f'{spec}: não consegui mover o card: {(err or out).strip()[:200]}')
            else:
                print(f'{spec}: card movido para {col}')
    except (RuntimeError, KeyError, ValueError) as e:
        G.warn(f'não consegui mover cards (token sem escopo `project`?): {str(e)[:200]}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
