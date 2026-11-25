#!/usr/bin/env python3
"""Gera arquivos derivados (nunca editar à mão):
  docs/requirements/traceability.csv, docs/requirements/coverage.md,
  .ai/sdd/INDEX.md, docs/adr/README.md
Uso: generate.py [--check]   (--check falha se algum arquivo estiver desatualizado)
"""
import csv, io, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sddlib as L

CHECK = '--check' in sys.argv
STALE = []
BANNER = '<!-- GERADO por tools/sdd/generate.py. NÃO EDITAR. Rode `make docs`. -->\n'


def emit(rel, content):
    p = L.ROOT / rel
    old = p.read_text(encoding='utf-8') if p.exists() else None
    if old != content:
        if CHECK:
            STALE.append(rel)
        else:
            p.write_text(content, encoding='utf-8', newline='')


reqs = L.csv_rows('docs/requirements/requirements-catalog.csv')
specs = L.csv_rows('docs/requirements/spec-catalog.csv')
spec_by = {s['spec_id']: s for s in specs}
written = {d.name[:3]: d for d in L.written_specs()}

# requisito -> FRs que o cobrem (specs escritas)
covered = {}
spec_info = {}
for sid, d in written.items():
    req_t = L.read(d / 'requirements.md')
    tsk_t = L.read(d / 'tasks.md')
    blocks = L.requirement_blocks(req_t)
    cov = L.tasks_coverage(tsk_t)
    tasks = L.parse_tasks(tsk_t)
    status = L.read(d / '.status').strip()
    hours = sum(t['est'] or 0 for t in tasks.values() if not t['removed'])
    spec_info[sid] = {'status': status, 'tasks': len([t for t in tasks.values() if not t['removed']]), 'hours': hours,
                      'frs': len([b for k, b in blocks.items() if k.startswith('FR') and not b['removed']])}
    for fr, b in blocks.items():
        if b['removed']:
            continue
        for rid in b['cobre']:
            covered.setdefault(rid, []).append((sid, fr, cov.get(fr, [])))

# ---- traceability.csv
buf = io.StringIO(newline='')
w = csv.writer(buf, lineterminator='\n')
w.writerow(['requisito', 'prioridade', 'release', 'spec_dona', 'spec_estado', 'fr', 'tarefas', 'situacao'])
for r in reqs:
    sp = r['spec_planejada']
    sid = sp[5:] if sp.startswith('SPEC-') else ''
    est = spec_by[sid]['estado'] if sid else 'governança'
    items = covered.get(r['id'], [])
    if items:
        for (s, fr, ts) in items:
            w.writerow([r['id'], r['prioridade'], r['release'], sp, est, f'SPEC-{s}/{fr}', ' '.join(ts), 'especificado'])
    else:
        w.writerow([r['id'], r['prioridade'], r['release'], sp, est, '', '', 'governança' if sp == 'GOV' else
                    ('lacuna: spec escrita sem cobertura' if est == 'escrita' else 'pendente: spec ainda não escrita')])
emit('docs/requirements/traceability.csv', buf.getvalue())

# ---- coverage.md
def cnt(f):
    return sum(1 for r in reqs if f(r))
def has(r):
    return r['id'] in covered
lines = [BANNER, '# Cobertura de especificação\n',
         'Gerado a partir de `requirements-catalog.csv`, `spec-catalog.csv` e das specs escritas. '
         'Mostra **quanto do produto está de fato especificado**.\n',
         '## Resumo\n',
         f'- Requisitos catalogados: **{len(reqs)}** ({cnt(lambda r: r["tipo"]=="RF")} RF + {cnt(lambda r: r["tipo"]=="RNF")} RNF)',
         f'- Specs no plano: **{len(specs)}**; escritas: **{len(written)}**; planejadas: **{len(specs)-len(written)}**',
         f'- Requisitos com cobertura em spec escrita: **{cnt(has)}** de {len(reqs)}',
         '']
lines += ['## Por release\n', '| Release | Requisitos | Cobertos por spec escrita | Specs no plano | Specs escritas |', '|---|---|---|---|---|']
for rel_ in L.RELEASES:
    rr = [r for r in reqs if r['release'] == rel_]
    ss = [s for s in specs if s['release'] == rel_]
    lines.append(f'| {rel_} | {len(rr)} | {sum(1 for r in rr if has(r))} | {len(ss)} | {sum(1 for s in ss if s["spec_id"] in written)} |')
lines += ['', '## Por spec\n', '| Spec | Título | Fase | Release | Rigor | Estado | `.status` | FRs | Tarefas | Horas |', '|---|---|---|---|---|---|---|---|---|---|']
for s in specs:
    i = spec_info.get(s['spec_id'])
    lines.append('| SPEC-{id} | {t} | {f} | {r} | {g} | {e} | {st} | {fr} | {tk} | {h} |'.format(
        id=s['spec_id'], t=s['titulo'].split(' (')[0], f=s['fase'], r=s['release'], g=s['rigor'], e=s['estado'],
        st=i['status'] if i else '-', fr=i['frs'] if i else '-', tk=i['tasks'] if i else '-', h=f"{i['hours']:g}" if i else '-'))
lines += ['', '## Requisitos Must do R1 ainda sem spec escrita\n', '| Requisito | Spec dona | Descrição |', '|---|---|---|']
for r in reqs:
    if r['release'] == 'R1' and r['prioridade'] == 'Must' and not has(r) and r['spec_planejada'] != 'GOV':
        lines.append(f"| {r['id']} | {r['spec_planejada']} | {r['descricao'][:80]} |")
emit('docs/requirements/coverage.md', '\n'.join(lines) + '\n')

# ---- INDEX.md
idx = [BANNER, '# Índice de especificações (SDD)\n',
       'Fonte: `docs/requirements/spec-catalog.csv` e arquivos `.status`. Este índice é gerado.\n',
       '| Spec | Título | Release | Fase | Rigor | Estado | Gate atual |', '|---|---|---|---|---|---|---|']
for s in specs:
    sid = s['spec_id']
    if sid in written:
        d = written[sid].name
        link = f'[SPEC-{sid}](specs/{d}/requirements.md)'
        gate = spec_info[sid]['status']
    else:
        link, gate = f'SPEC-{sid}', 'não iniciada'
    idx.append(f"| {link} | {s['titulo'].split(' (')[0]} | {s['release']} | {s['fase']} | {s['rigor']} | {s['estado']} | {gate} |")
emit('.ai/sdd/INDEX.md', '\n'.join(idx) + '\n')

# ---- ADR README
adrs = []
for f in sorted((L.ROOT / 'docs/adr').glob('ADR-*.md')):
    t = L.read(f)
    title = re.search(r'^# (.*)$', t, flags=re.M).group(1)
    adrs.append((f.name, title, L.header_field(t, 'Status') or '?', L.header_field(t, 'Resolvida por') or '-'))
a = [BANNER, '# Registro de decisões de arquitetura (ADR)\n',
     'Todas as ADRs estão **Proposta** até aprovação formal (ver `docs/governance/change-control.md`).\n',
     '| ADR | Título | Status | Resolvida por |', '|---|---|---|---|']
for n, t, s, r in adrs:
    a.append(f'| [{n[:7]}]({n}) | {re.sub(r"^ADR-\d+:?\s*", "", t)} | {s} | {r} |')
emit('docs/adr/README.md', '\n'.join(a) + '\n')

if CHECK:
    if STALE:
        print('desatualizados: ' + ', '.join(STALE))
        sys.exit(1)
else:
    print('gerados: traceability.csv, coverage.md, INDEX.md, adr/README.md')
