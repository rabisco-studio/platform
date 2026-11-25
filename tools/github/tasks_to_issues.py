#!/usr/bin/env python3
"""Gera as issues de tarefa de uma spec a partir do tasks.md.

Só funciona depois do gate G3: o `.status` da spec precisa ser `tasks:approved` ou posterior.
Uma issue por tarefa ativa, no formato do formulário .github/ISSUE_TEMPLATE/task.yml:
  título  [SPEC-NNN T-NNN] <título>
  labels  task + area:* + rigor:* (da spec) ; milestone do release
  corpo   Spec, ID, Requisitos, Estimativa, Dependências, Checklist, Verificação
          + marcador oculto <!-- task:SPEC-NNN:T-NNN --> (idempotência: nunca duplica)

ENSAIO por padrão (só imprime). Só cria issues com --apply.

Uso: python3 tools/github/tasks_to_issues.py 001 [--apply] [--repo ORG/REPO] [--root DIR]
Saída: 0 ok; 1 recusa ou erro; 3 sem permissão/milestone ausente (com --apply).
"""
import csv
import io
import math
import pathlib
import re
import sys
import time

import ghlib as G
import sddlib as L

CATALOG = 'docs/requirements/spec-catalog.csv'
MILESTONES = {'R1': 'R1 Local Studio', 'R2': 'R2 Cloud', 'R3': 'R3 Collab', 'R4': 'R4 Everywhere', 'R5': 'R5 Pro'}
AREA_LABEL = {'core': 'area:core', 'backend': 'area:backend', 'clients': 'area:clients',
              'platform': 'area:platform', 'contracts': 'area:platform'}
# A listagem de issues do GitHub é eventualmente consistente: logo após criar, as issues novas podem
# demorar alguns segundos para aparecer. Sem esperar, um segundo --apply seguido duplicaria as últimas.
WAIT_TRIES = 12
WAIT_SECONDS = 5
MARKER = '<!-- task:{spec}:{task} -->'
MARKER_RE = re.compile(r'<!-- task:(SPEC-\d{3}):(T-\d{3}) -->')
TASK_RE = re.compile(r'^### (T-\d{3})\s*[—–-]?\s*(.*)$\n((?:.*\n)*?)(?=^### |^## |\Z)', flags=re.M)


class Refusal(Exception):
    pass


def parse(text):
    """Tarefas do tasks.md: [{id, title, removed, req, est, deps, checklist, verify}]."""
    out = []
    for m in TASK_RE.finditer(text):
        tid, title, body = m.group(1), m.group(2).strip(), m.group(3)
        removed = 'Removid' in title
        f = lambda name: (re.search(r'^\*\*%s:\*\*[ \t]*(.*)$' % name, body, flags=re.M) or [None, None])[1]  # noqa: E731
        est = re.search(r'\*\*Estimativa:\*\*\s*([\d.]+)\s*h', body)
        check = re.search(r'^\*\*Checklist:\*\*[ \t]*\n((?:- \[.\].*\n?)+)', body, flags=re.M)
        out.append({'id': tid, 'title': re.sub(r'\s+', ' ', title), 'removed': removed,
                    'req': (f('Requisito') or '').strip(), 'est': float(est.group(1)) if est else None,
                    'deps': (f('Dependências') or 'Nenhuma').strip(),
                    'checklist': check.group(1).rstrip('\n') if check else '- [ ] (copiar do tasks.md)',
                    'verify': (f('Verificação') or '').strip()})
    return out


def check_ready(status):
    if status not in L.STAGES:
        raise Refusal(f'.status inválido: {status!r}')
    if L.STAGES.index(status) < L.STAGES.index('tasks:approved'):
        raise Refusal(f'a spec está em {status}: issues de tarefa só existem depois do gate G3 '
                      f'(tasks:approved). Antes disso as tarefas podem mudar.')


def estimate_label(est):
    if est is None:
        raise Refusal('tarefa sem estimativa')
    if not 1 <= est <= 4:
        raise Refusal(f'estimativa {est} h fora de 1 a 4 h (quebre a tarefa na spec, via CR C2)')
    return f'{math.ceil(est)} h'


def build(spec_id, row, task):
    """(título, corpo, labels, milestone) da issue de uma tarefa."""
    body = '\n\n'.join([
        '### Spec\n\n' + spec_id,
        '### ID da tarefa (igual ao tasks.md)\n\n' + task['id'],
        '### Requisitos (FR/NFR)\n\n' + (task['req'] or '—'),
        '### Estimativa\n\n' + estimate_label(task['est']),
        '### Dependências\n\n' + task['deps'],
        '### Checklist\n\n' + task['checklist'],
        '### Verificação\n\n' + (task['verify'] or '—'),
        MARKER.format(spec=spec_id, task=task['id']),
    ]) + '\n'
    labels = ['task', AREA_LABEL[row['area']], f'rigor:{row["rigor"]}']
    return f'[{spec_id} {task["id"]}] {task["title"]}', body, labels, MILESTONES[row['release']]


def load_spec(root, n):
    sid = f'{int(str(n).upper().removeprefix("SPEC-")):03d}'
    rows = list(csv.DictReader(io.StringIO((root / CATALOG).read_text(encoding='utf-8'))))
    row = next((r for r in rows if r['spec_id'] == sid), None)
    if row is None:
        raise Refusal(f'SPEC-{sid} não existe no catálogo')
    folder = root / '.ai/sdd/specs' / f'{sid}-{row["slug"]}'
    if not (folder / 'tasks.md').exists():
        raise Refusal(f'{folder.name}/tasks.md não existe (a spec ainda não foi escrita)')
    status = (folder / '.status').read_text(encoding='utf-8').strip()
    check_ready(status)
    return f'SPEC-{sid}', row, parse((folder / 'tasks.md').read_text(encoding='utf-8'))


def existing_markers(repo):
    """Conjunto {(SPEC-NNN, T-NNN)} das issues (abertas ou fechadas) que já têm marcador."""
    found, page = set(), 1
    while True:
        code, out, err = G.gh(['api', f'repos/{repo}/issues?state=all&labels=task&per_page=100&page={page}'])
        if code != 0:
            raise RuntimeError((err or out).strip())
        import json
        items = json.loads(out or '[]')
        for it in items:
            found |= set(MARKER_RE.findall(it.get('body') or ''))
        if len(items) < 100:
            return found
        page += 1


def wait_visible(repo, wanted):
    """Espera as issues recém-criadas aparecerem na listagem; devolve as que continuam invisíveis."""
    missing = set(wanted)
    for attempt in range(WAIT_TRIES):
        missing = set(wanted) - existing_markers(repo)
        if not missing:
            break
        if attempt < WAIT_TRIES - 1:
            time.sleep(WAIT_SECONDS)
    return missing


def plan(spec_id, row, tasks, existing):
    """[(ação, tarefa, título, corpo, labels, milestone)]; ação = criar | ignorar."""
    rows = []
    for t in tasks:
        if t['removed']:
            continue
        title, body, labels, ms = build(spec_id, row, t)
        action = 'ignorar' if (spec_id, t['id']) in existing else 'criar'
        rows.append((action, t['id'], title, body, labels, ms))
    return rows


def main(argv):
    args = [a for a in argv if not a.startswith('--')]
    opts = {k: argv[argv.index(k) + 1] for k in ('--repo', '--root') if k in argv}
    args = [a for a in args if a not in opts.values()]
    apply = '--apply' in argv
    if len(args) != 1:
        print('uso: python3 tools/github/tasks_to_issues.py NNN [--apply] [--repo ORG/REPO] [--root DIR]', file=sys.stderr)
        return 1
    repo, root = opts.get('--repo', G.REPO_DEFAULT), pathlib.Path(opts.get('--root', G.ROOT))
    try:
        spec_id, row, tasks = load_spec(root, args[0])
        existing = set()
        if apply or '--check-existing' in argv:
            existing = existing_markers(repo)
        rows = plan(spec_id, row, tasks, existing)
    except Refusal as e:
        print(f'RECUSADO: {e}', file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f'ERRO ao consultar o GitHub: {e}', file=sys.stderr)
        return 3
    print(f'{spec_id} em {repo}: modo {"APLICAR" if apply else "ENSAIO (nada será criado; use --apply)"}')
    for action, tid, title, body, labels, ms in rows:
        print(f'\n[{action}] {title}\n  labels: {", ".join(labels)} | milestone: {ms}')
        if not apply and action == 'criar':
            print('  corpo:\n' + '\n'.join('    ' + l for l in body.splitlines()))
    todo = [r for r in rows if r[0] == 'criar']
    print(f'\nTotal: criar {len(todo)}, ignorar {len(rows) - len(todo)}')
    if not apply:
        if not existing:
            print('Obs.: o ensaio não consulta o GitHub; use --check-existing para ver o que seria ignorado.')
        return 0
    code, out, err = G.gh(['api', f'repos/{repo}/milestones?state=all&per_page=100'])
    have = {m['title'] for m in __import__('json').loads(out or '[]')} if code == 0 else set()
    for ms in sorted({r[5] for r in todo} - have):
        print(f'ERRO: milestone "{ms}" não existe; rode tools/github/setup-labels-milestones.py --apply', file=sys.stderr)
        return 3
    for action, tid, title, body, labels, ms in todo:
        args_ = ['issue', 'create', '--repo', repo, '--title', title, '--body', body, '--milestone', ms]
        for lb in labels:
            args_ += ['--label', lb]
        code, out, err = G.gh(args_)
        if code != 0:
            print(f'ERRO ao criar {tid}: {(err or out).strip()[:300]}', file=sys.stderr)
            return 3
        print(f'criada: {out.strip()}')
    try:
        missing = wait_visible(repo, {(spec_id, r[1]) for r in todo})
    except RuntimeError:
        missing = {(spec_id, r[1]) for r in todo}
    if missing:
        print('AVISO: ainda não aparecem na listagem: ' + ', '.join(sorted(t for _, t in missing)) +
              '. Aguarde alguns minutos antes de rodar --apply de novo, para não duplicar.', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
