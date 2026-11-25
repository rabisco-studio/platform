#!/usr/bin/env python3
"""Cobra, por comentário, as issues com label `bloqueado` há mais de 7 dias.

Marca o responsável (assignee) e comenta no máximo uma vez a cada 7 dias por issue
(marcador oculto no comentário). Sem permissão para comentar: avisa e sai com 0.

Uso: python3 tools/github/nudge_blocked.py [--today AAAA-MM-DD] [--dry-run]
Entrada (ambiente): GITHUB_REPOSITORY, GH_TOKEN.
"""
import datetime
import json
import os
import sys

import ghlib as G

LABEL = 'bloqueado'
DAYS = 7
MARKER = '<!-- rabisco-blocked-nudge:'


def _dt(s):
    return datetime.datetime.fromisoformat(s.replace('Z', '+00:00')).date()


def blocked_since(events, created_at):
    """Data do último evento `labeled` com o label bloqueado (ou da criação da issue)."""
    dates = [_dt(e['created_at']) for e in events
             if e.get('event') == 'labeled' and (e.get('label') or {}).get('name') == LABEL]
    return max(dates) if dates else _dt(created_at)


def last_nudge(comments):
    dates = []
    for c in comments:
        body = c.get('body') or ''
        if MARKER in body:
            raw = body.split(MARKER, 1)[1].split('-->', 1)[0].strip()
            try:
                dates.append(datetime.date.fromisoformat(raw))
            except ValueError:
                pass
    return max(dates) if dates else None


def message(issue, today, since):
    who = ' '.join(f'@{a["login"]}' for a in issue.get('assignees', [])) or '_sem responsável definido_'
    return (f'{MARKER} {today.isoformat()} -->\n'
            f'{who}: esta issue está `{LABEL}` desde {since.isoformat()} ({(today - since).days} dias). '
            'Atualize: cite o que bloqueia (issue, Q- ou DEC-) e quem destrava, ou remova o label se já foi resolvido.')


def due(issue, events, comments, today):
    since = blocked_since(events, issue['created_at'])
    if (today - since).days <= DAYS:
        return None
    ln = last_nudge(comments)
    if ln and (today - ln).days < DAYS:
        return None
    return message(issue, today, since)


def main(argv):
    today = datetime.date.today()
    if '--today' in argv:
        today = datetime.date.fromisoformat(argv[argv.index('--today') + 1])
    repo = os.environ.get('GITHUB_REPOSITORY', G.REPO_DEFAULT)
    code, out, err = G.gh(['api', f'repos/{repo}/issues?labels={LABEL}&state=open&per_page=100'])
    if code != 0:
        G.warn(f'não consegui listar issues `{LABEL}`: {(err or out).strip()[:200]}')
        return 0
    issues = [i for i in json.loads(out or '[]') if 'pull_request' not in i]
    print(f'{len(issues)} issue(s) com `{LABEL}`.')
    for i in issues:
        n = i['number']
        c1, ev, _ = G.gh(['api', f'repos/{repo}/issues/{n}/events?per_page=100'])
        c2, cm, _ = G.gh(['api', f'repos/{repo}/issues/{n}/comments?per_page=100'])
        msg = due(i, json.loads(ev or '[]') if c1 == 0 else [], json.loads(cm or '[]') if c2 == 0 else [], today)
        if not msg:
            print(f'#{n}: sem cobrança necessária')
            continue
        if '--dry-run' in argv:
            print(f'[dry-run] #{n}:\n{msg}')
            continue
        code, out, err = G.gh(['api', '-X', 'POST', f'repos/{repo}/issues/{n}/comments'], payload={'body': msg})
        if code != 0:
            G.warn(f'#{n}: não consegui comentar: {(err or out).strip()[:200]}')
        else:
            print(f'#{n}: cobrança publicada')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
