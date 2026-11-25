#!/usr/bin/env python3
"""Comentário de impacto em PRs que mexem em specs, ADRs, contratos ou catálogos.

Lista os requisitos (RF/RNF), as specs e as specs dependentes afetados, usando
docs/requirements/traceability.csv e as dependências dos tasks.md. O comentário é
único por PR: execuções seguintes atualizam o mesmo (marcador oculto).

Entrada (ambiente): BASE_SHA, HEAD_SHA, PR_NUMBER, GITHUB_REPOSITORY, GH_TOKEN.
Sem permissão para comentar (PR de fork), avisa, grava no resumo do job e sai com 0.
Opções: --dry-run  imprime o comentário e não publica.
"""
import csv
import io
import os
import re
import sys

import ghlib as G
import sddlib as L

MARKER = '<!-- rabisco-impact-comment -->'
SPEC_RE = re.compile(r'^\.ai/sdd/specs/(\d{3})-[^/]+/')
ADR_RE = re.compile(r'^docs/adr/(ADR-\d{3})-')
REQ_CAT = 'docs/requirements/requirements-catalog.csv'
SPEC_CAT = 'docs/requirements/spec-catalog.csv'
TRACE = 'docs/requirements/traceability.csv'


def _read(root, rel):
    p = root / rel
    return p.read_text(encoding='utf-8') if p.exists() else ''


def _rows(text):
    return list(csv.DictReader(io.StringIO(text)))


def written_specs(root):
    base = root / '.ai/sdd/specs'
    return sorted(p for p in base.iterdir() if p.is_dir()) if base.exists() else []


def dependency_graph(root):
    """{'SPEC-002': {'SPEC-001', 'SPEC-003'}}: de quem cada spec depende (via tasks.md)."""
    graph = {}
    for d in written_specs(root):
        sid = G.spec_id_from_dir(d.name)
        deps = set()
        tp = d / 'tasks.md'
        if tp.exists():
            for t in L.parse_tasks(tp.read_text(encoding='utf-8')).values():
                deps |= {f'SPEC-{s}' for s in t['dep_spec']}
                deps |= {f'SPEC-{s}' for s, _ in t['dep_cross']}
        deps.discard(sid)
        graph[sid] = deps
    return graph


def dependents(graph, targets):
    """Fecho transitivo das specs que dependem de algum alvo. Devolve {spec: [via]} ordenado."""
    found, frontier = {}, set(targets)
    while frontier:
        nxt = set()
        for s, deps in graph.items():
            hit = deps & frontier
            if hit and s not in found and s not in targets:
                found[s] = sorted(hit)
                nxt.add(s)
        frontier = nxt
    return dict(sorted(found.items()))


def changed_ids(old_text, new_text, key):
    old = {r[key]: r for r in _rows(old_text)}
    new = {r[key]: r for r in _rows(new_text)}
    return sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))


def compute(files, root, base_texts=None):
    """files: caminhos alterados no PR. base_texts: {caminho: texto na base} para os catálogos."""
    base_texts = base_texts or {}
    specs = sorted({'SPEC-' + m.group(1) for f in files if (m := SPEC_RE.match(f))})
    adrs = sorted({m.group(1) for f in files if (m := ADR_RE.match(f))})
    contracts = sorted(f for f in files if f.startswith('contracts/'))
    cat_reqs = changed_ids(base_texts.get(REQ_CAT, ''), _read(root, REQ_CAT), 'id') if REQ_CAT in files else []
    cat_specs = []
    if SPEC_CAT in files:
        cat_specs = ['SPEC-' + s for s in changed_ids(base_texts.get(SPEC_CAT, ''), _read(root, SPEC_CAT), 'spec_id')]
    if not (specs or adrs or contracts or cat_reqs or cat_specs):
        return None
    graph = dependency_graph(root)
    spec_docs = {G.spec_id_from_dir(d.name): ''.join(_read(d, n) for n in ('requirements.md', 'design.md'))
                 for d in written_specs(root)}
    citing = {}
    for a in adrs:
        for s, txt in spec_docs.items():
            if a in txt:
                citing.setdefault(s, []).append(a)
    for c in contracts:
        for s, txt in spec_docs.items():
            if c in txt or c.rsplit('/', 1)[-1] in txt:
                citing.setdefault(s, []).append(c)
    direct = sorted(set(specs) | set(cat_specs) | set(citing))
    reqs = {}
    for r in _rows(_read(root, TRACE)):
        owner = r['spec_dona']
        fr_spec = r['fr'].split('/')[0] if r['fr'] else ''
        if owner in direct or fr_spec in direct or r['requisito'] in cat_reqs:
            reqs.setdefault(r['requisito'], set()).add(owner if owner.startswith('SPEC') else fr_spec)
    for rid in cat_reqs:
        reqs.setdefault(rid, set())
    return {'specs': specs, 'adrs': adrs, 'contracts': contracts, 'cat_reqs': cat_reqs, 'cat_specs': cat_specs,
            'citing': citing, 'direct': direct, 'reqs': reqs, 'dependents': dependents(graph, set(direct))}


def render(res):
    L_ = [MARKER, '## Análise de impacto', '',
          'Gerada automaticamente a partir de `traceability.csv` e das dependências dos `tasks.md`. '
          'Atualizada a cada push; não edite.', '']
    if res['specs']:
        L_.append('**Specs alteradas:** ' + ', '.join(res['specs']))
    if res['adrs']:
        L_.append('**ADRs alteradas:** ' + ', '.join(res['adrs']))
    if res['contracts']:
        L_.append('**Contratos alterados:** ' + ', '.join(f'`{c}`' for c in res['contracts']))
    if res['cat_reqs']:
        L_.append('**Requisitos alterados no catálogo:** ' + ', '.join(res['cat_reqs']))
    if res['cat_specs']:
        L_.append('**Specs alteradas no catálogo:** ' + ', '.join(res['cat_specs']))
    L_ += ['']
    if res['citing']:
        L_ += ['### Specs que citam ADRs ou contratos alterados', '| Spec | Cita |', '|---|---|']
        L_ += [f'| {s} | {", ".join(sorted(set(v)))} |' for s, v in sorted(res['citing'].items())]
        L_.append('')
    L_ += ['### Requisitos afetados']
    if res['reqs']:
        L_ += ['| Requisito | Spec |', '|---|---|']
        L_ += [f'| {r} | {", ".join(sorted(x for x in s if x)) or "—"} |' for r, s in sorted(res['reqs'].items())]
    else:
        L_.append('Nenhum requisito do catálogo aponta para estas specs.')
    L_ += ['', '### Specs dependentes (reavaliar)']
    if res['dependents']:
        L_ += ['| Spec | Depende de |', '|---|---|']
        L_ += [f'| {s} | {", ".join(v)} |' for s, v in res['dependents'].items()]
        L_.append('')
        L_.append('Se a mudança for em documento aprovado, ela reabre o gate (ver [change-control](docs/governance/change-control.md)).')
    else:
        L_.append('Nenhuma spec escrita depende das specs afetadas.')
    return '\n'.join(L_) + '\n'


def upsert_comment(repo, number, body):
    """Cria ou atualiza o comentário com o marcador. Devolve (ok, mensagem)."""
    code, out, err = G.gh(['api', f'repos/{repo}/issues/{number}/comments?per_page=100'])
    if code != 0:
        return False, (err or out).strip()
    import json
    existing = next((c for c in json.loads(out or '[]') if MARKER in (c.get('body') or '')), None)
    if existing:
        code, out, err = G.gh(['api', '-X', 'PATCH', f'repos/{repo}/issues/comments/{existing["id"]}'], payload={'body': body})
    else:
        code, out, err = G.gh(['api', '-X', 'POST', f'repos/{repo}/issues/{number}/comments'], payload={'body': body})
    return (code == 0), (err or out).strip()


def main(argv):
    base, head = os.environ.get('BASE_SHA', ''), os.environ.get('HEAD_SHA', '')
    if not base or not head:
        print('BASE_SHA e HEAD_SHA são obrigatórios', file=sys.stderr)
        return 2
    files = G.git(['diff', '--name-only', base, head]).splitlines()
    base_texts = {p: G.git(['show', f'{base}:{p}'], check=False) for p in (REQ_CAT, SPEC_CAT) if p in files}
    res = compute(files, L.ROOT, base_texts)
    if res is None:
        print('Nenhuma spec, ADR, contrato ou catálogo alterado: sem comentário de impacto.')
        return 0
    body = render(res)
    print(body)
    G.step_summary(body)
    if '--dry-run' in argv:
        return 0
    repo, number = os.environ.get('GITHUB_REPOSITORY', G.REPO_DEFAULT), os.environ.get('PR_NUMBER', '')
    if not number:
        G.warn('PR_NUMBER ausente: comentário não publicado (relatório no log e no resumo do job).')
        return 0
    ok, msg = upsert_comment(repo, number, body)
    if not ok:
        G.warn(f'Não consegui comentar no PR (token somente leitura, comum em PRs de fork?): {msg[:200]}. '
               'O relatório está no log e no resumo do job.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
