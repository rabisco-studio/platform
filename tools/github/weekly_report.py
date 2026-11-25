#!/usr/bin/env python3
"""Rascunho do relatório semanal (template status-report) e abertura da issue da semana.

Uso: python3 tools/github/weekly_report.py [--today AAAA-MM-DD] [--issue]
  sem --issue: só imprime o rascunho.
  --issue:     abre UMA issue com label `status-report` por semana (não duplica).
Entrada (ambiente): GITHUB_REPOSITORY, GH_TOKEN. Sem permissão: avisa e sai com 0.
"""
import datetime
import os
import re
import sys

import ghlib as G
import overdue as O
import sddlib as L

LABEL = 'status-report'
TEMPLATE = 'docs/templates/status-report-template.md'


def week_start(today):
    return today - datetime.timedelta(days=today.weekday())


def title_for(today):
    return f'Relatório de status — semana de {week_start(today).isoformat()}'


def index_rows(root=None):
    text = ((root or L.ROOT) / '.ai/sdd/INDEX.md').read_text(encoding='utf-8')
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) == 7 and re.search(r'SPEC-\d{3}', cells[0]) and cells[5] == 'escrita':
            rows.append((re.search(r'SPEC-\d{3}', cells[0]).group(0), cells[6]))
    return rows


def recent_changes(today, root=None):
    since = (today - datetime.timedelta(days=7)).isoformat()
    out = G.git(['log', f'--since={since}', '--no-merges', '--format=%h %s'], cwd=root, check=False)
    return [l for l in out.splitlines() if l.strip()]


def changed_specs(today, root=None):
    since = (today - datetime.timedelta(days=7)).isoformat()
    files = G.git(['log', f'--since={since}', '--name-only', '--format=', '--', '.ai/sdd/specs/*/.status'], cwd=root, check=False)
    return {'SPEC-' + m.group(1) for m in re.finditer(r'\.ai/sdd/specs/(\d{3})-', files)}


def render(today, root=None):
    tpl = ((root or L.ROOT) / TEMPLATE).read_text(encoding='utf-8')
    start = week_start(today)
    end = start + datetime.timedelta(days=6)
    tpl = tpl.replace('# Relatório de status — semana de AAAA-MM-DD', f'# {title_for(today)}')
    tpl = tpl.replace('**Autor:** <PMO>', '**Autor:** PMO (rascunho automático; revise antes de publicar)')
    tpl = tpl.replace('**Período:** <de> a <até>', f'**Período:** {start.isoformat()} a {end.isoformat()}')
    changed = changed_specs(today, root)
    table = ['| Spec | Gate atual | Mudou nesta semana? | Dono | Bloqueio |', '|---|---|---|---|---|']
    table += [f'| {s} | {g} | {"sim" if s in changed else "não"} | — | — |' for s, g in index_rows(root)]
    tpl = re.sub(r'\| Spec \| Gate atual \|.*?\n\|---\|---\|---\|---\|---\|\n\| \| \| \| \| \|\n', '\n'.join(table) + '\n', tpl, flags=re.S)
    changes = recent_changes(today, root)
    done = '\n'.join(f'- {c}' for c in changes[:30]) or '- Nenhuma mudança nos últimos 7 dias.'
    tpl = tpl.replace('- <item com link>', done)
    overdue, undated = O.collect(today)
    risks = ['- Vencidos:'] + [f'  - {r["id"]} (prazo {r["data"]})' for r in overdue]
    if not overdue:
        risks.append('  - nenhum')
    risks += [f'- Abertos sem data: {len(undated)} (veja `overdue.py`)']
    tpl = tpl.replace('- Vencendo nos próximos 7 dias: <itens com prazo>', '\n'.join(risks))
    return tpl


def existing_issue(repo, title):
    code, out, err = G.gh(['issue', 'list', '--repo', repo, '--label', LABEL, '--state', 'all', '--search',
                           f'"{title}" in:title', '--json', 'number,title', '--limit', '20'])
    if code != 0:
        # label ausente: procurar só pelo título
        code, out, err = G.gh(['issue', 'list', '--repo', repo, '--state', 'all', '--search',
                               f'"{title}" in:title', '--json', 'number,title', '--limit', '20'])
        if code != 0:
            raise RuntimeError((err or out).strip())
    import json
    return next((i for i in json.loads(out or '[]') if i['title'] == title), None)


def main(argv):
    today = datetime.date.today()
    if '--today' in argv:
        today = datetime.date.fromisoformat(argv[argv.index('--today') + 1])
    body = render(today)
    print(body)
    if '--issue' not in argv:
        return 0
    repo, title = os.environ.get('GITHUB_REPOSITORY', G.REPO_DEFAULT), title_for(today)
    try:
        found = existing_issue(repo, title)
    except RuntimeError as e:
        G.warn(f'não consegui consultar issues (sem permissão?): {str(e)[:200]}')
        return 0
    if found:
        print(f'Já existe a issue da semana: #{found["number"]}; nada a criar.')
        return 0
    code, out, err = G.gh(['issue', 'create', '--repo', repo, '--title', title, '--body', body, '--label', LABEL])
    if code != 0 and 'label' in (err + out).lower():
        G.warn(f'label `{LABEL}` não existe: rode tools/github/setup-labels-milestones.py --apply. Criando a issue sem label.')
        code, out, err = G.gh(['issue', 'create', '--repo', repo, '--title', title, '--body', body])
    if code != 0:
        G.warn(f'não consegui criar a issue da semana: {(err or out).strip()[:200]}')
        return 0
    print(f'Issue criada: {out.strip()}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
