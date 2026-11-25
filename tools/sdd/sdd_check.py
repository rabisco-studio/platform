#!/usr/bin/env python3
"""sdd-check: verificações de consistência do repositório de especificações.

Uso:
    python3 tools/sdd/sdd_check.py            # erros falham (exit 1); avisos não
    python3 tools/sdd/sdd_check.py --strict   # avisos também falham (linha de base de release)
    python3 tools/sdd/sdd_check.py --summary  # apenas totais

Somente biblioteca padrão. Veja docs/governance/team-workflow.md para as regras.
"""
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sddlib as L  # noqa: E402

ERR, WARN = [], []


def err(where, msg):
    ERR.append(f'{where}: {msg}')


def warn(where, msg):
    WARN.append(f'{where}: {msg}')


def rel(p):
    return str(pathlib.Path(p).relative_to(L.ROOT))


# --------------------------------------------------------------------- catálogos
def load_catalogs():
    reqs = {r['id']: r for r in L.csv_rows('docs/requirements/requirements-catalog.csv')}
    specs = {r['spec_id']: r for r in L.csv_rows('docs/requirements/spec-catalog.csv')}
    return reqs, specs


def check_catalogs(reqs, specs):
    where = 'docs/requirements'
    for rid, r in reqs.items():
        if r['prioridade'] not in ('Must', 'Should', 'Could'):
            err(where, f'{rid}: prioridade inválida {r["prioridade"]!r}')
        if r['release'] not in L.RELEASES:
            err(where, f'{rid}: release inválida {r["release"]!r}')
        sp = r['spec_planejada']
        if sp == 'GOV':
            continue
        m = re.fullmatch(r'SPEC-(\d{3})', sp)
        if not m or m.group(1) not in specs:
            err(where, f'{rid}: spec_planejada {sp!r} não existe em spec-catalog.csv')
            continue
        srel = specs[m.group(1)]['release']
        if L.RELEASES.index(srel) > L.RELEASES.index(r['release']):
            err(where, f'{rid} (release {r["release"]}) aponta para {sp} de release posterior ({srel})')
    for sid, s in specs.items():
        if s['rigor'] not in L.RIGOR:
            err('spec-catalog.csv', f'SPEC-{sid}: rigor inválido')
        if s['release'] not in L.RELEASES:
            err('spec-catalog.csv', f'SPEC-{sid}: release inválida')
        if s['area'] not in L.AREAS:
            err('spec-catalog.csv', f'SPEC-{sid}: área inválida')
        if s['estado'] not in ('escrita', 'planejada'):
            err('spec-catalog.csv', f'SPEC-{sid}: estado inválido')


# --------------------------------------------------------------------- specs escritas
def check_specs(reqs, specs):
    seen = {}
    task_graph = {}
    all_tasks = {}
    constitution = L.read(L.ROOT / 'docs/constitution.md')
    for d in L.written_specs():
        name = d.name
        m = re.fullmatch(r'(\d{3})-([a-z0-9-]+)', name)
        if not m:
            err(rel(d), 'nome de pasta fora do padrão NNN-slug')
            continue
        sid, slug = m.groups()
        if sid in seen:
            err(rel(d), f'prefixo duplicado com {seen[sid]}')
        seen[sid] = name
        cat = specs.get(sid)
        if not cat:
            err(rel(d), 'spec não existe em docs/requirements/spec-catalog.csv')
            continue
        if cat['slug'] != slug:
            err(rel(d), f'slug difere do catálogo ({cat["slug"]})')
        if cat['estado'] != 'escrita':
            err(rel(d), 'pasta existe mas o catálogo marca a spec como planejada')

        files = {f: d / f for f in ('requirements.md', 'design.md', 'tasks.md', '.status')}
        for f, p in files.items():
            if not p.exists():
                err(rel(d), f'arquivo obrigatório ausente: {f}')
        if not all(p.exists() for p in files.values()):
            continue

        status = L.read(files['.status']).strip()
        if '\n' in status or status not in L.STAGES:
            err(rel(files['.status']), f'.status inválido: {status!r}')
            continue
        sidx = L.STAGES.index(status)

        req_t, des_t, tsk_t = (L.read(files[f]) for f in ('requirements.md', 'design.md', 'tasks.md'))

        # ---- cabeçalho de requirements
        for fld in ('Status', 'Área', 'Release', 'Rigor', 'Tags', 'ADRs', 'Depende de'):
            if L.header_field(req_t, fld) is None:
                err(rel(files['requirements.md']), f'cabeçalho sem campo **{fld}:**')
        if L.header_field(req_t, 'Área') and cat['area'] != L.header_field(req_t, 'Área'):
            err(rel(files['requirements.md']), 'Área difere do catálogo')
        if L.header_field(req_t, 'Release') and cat['release'] != L.header_field(req_t, 'Release'):
            err(rel(files['requirements.md']), 'Release difere do catálogo')
        if L.header_field(req_t, 'Rigor') and cat['rigor'] != L.header_field(req_t, 'Rigor'):
            err(rel(files['requirements.md']), 'Rigor difere do catálogo')
        tags = {t.strip() for t in (L.header_field(req_t, 'Tags') or '').split(',') if t.strip()}
        if not tags <= L.TAGS:
            err(rel(files['requirements.md']), f'tags inválidas: {sorted(tags - L.TAGS)}')
        if 'contract' not in tags and cat['rigor'] != 'anchored' and 'format' in tags:
            warn(rel(d), 'tag format exige rigor anchored')
        if ('format' in tags or 'contract' in tags or 'security' in tags or 'privacy' in tags) and cat['rigor'] != 'anchored':
            err(rel(d), 'tags format/contract/security/privacy exigem rigor anchored (regra de dúvida)')

        # ---- gates x status dos documentos
        tokens = {
            'requirements': L.parse_status_token(L.header_field(req_t, 'Status')),
            'design': L.parse_status_token(L.header_field(des_t, 'Status')),
            'tasks': L.parse_status_token(L.header_field(tsk_t, 'Status')),
        }
        for doc, tok in tokens.items():
            if tok not in L.STAGES:
                err(rel(d), f'{doc}.md com Status inválido: {tok!r}')
                continue
            dr = L.STAGES.index(f'{doc}:draft')
            ap = L.STAGES.index(f'{doc}:approved')
            if sidx < dr and tok != f'{doc}:draft':
                err(rel(d), f'{doc}.md está {tok} mas o .status ({status}) ainda não chegou nesta fase')
            if sidx >= ap and tok != f'{doc}:approved':
                err(rel(d), f'.status={status} exige {doc}.md em {doc}:approved (está {tok})')
            if sidx < ap and tok == f'{doc}:approved':
                err(rel(d), f'{doc}.md marcado approved mas o .status ({status}) não registra a aprovação')
        if sidx < L.STAGES.index('requirements:approved'):
            for doc in ('design', 'tasks'):
                if tokens[doc] == f'{doc}:draft' and 'antecipado' not in L.read(files[f'{doc}.md'])[:400]:
                    warn(rel(d), f'{doc}.md é rascunho antecipado e deve declarar "rascunho antecipado" no cabeçalho')

        # ---- perguntas abertas
        open_q = re.findall(r'^- \*\*(Q-\d{3})[^*]*\*\*[^\n]*(?:aberta|TBD|\?\?)', req_t, flags=re.M)
        open_q += re.findall(r'^- \*\*(Q-\d{3}) \(aberta', req_t, flags=re.M)
        for q in sorted(set(open_q)):
            (err if sidx >= L.STAGES.index('requirements:approved') else warn)(rel(files['requirements.md']),
                                                                              f'{q} está aberta')
        if re.search(r'\bTBD\b', req_t + des_t + tsk_t):
            err(rel(d), 'contém TBD')

        # ---- IDs duplicados
        for f, txt in (('requirements.md', req_t), ('design.md', des_t), ('tasks.md', tsk_t)):
            ids = re.findall(r'^#{2,4} ((?:US|FR|NFR|TD|T)-\d{3})\b', txt, flags=re.M)
            ids += re.findall(r'^- \*\*((?:AC|D|Q)-\d{3})\b', txt, flags=re.M)
            dup = {i for i in ids if ids.count(i) > 1}
            for i in sorted(dup):
                err(rel(files[f]), f'ID duplicado: {i}')

        # ---- requisitos x catálogo
        blocks = L.requirement_blocks(req_t)
        active = {k: v for k, v in blocks.items() if not v['removed']}
        for rid, b in active.items():
            if not b['cobre']:
                err(rel(files['requirements.md']), f'{rid} sem linha **Cobre:**')
            for c in b['cobre']:
                if c not in reqs:
                    err(rel(files['requirements.md']), f'{rid} cobre {c}, que não existe no catálogo')
        # ---- design mapping / cobertura de tarefas
        mapped = L.design_mapped(des_t)
        cov = L.tasks_coverage(tsk_t)
        tasks = L.parse_tasks(tsk_t)
        for rid in active:
            if rid.startswith('FR'):
                if rid not in mapped:
                    err(rel(files['design.md']), f'{rid} sem linha no mapeamento de requisitos')
                if not cov.get(rid):
                    err(rel(files['tasks.md']), f'{rid} sem tarefa na tabela de cobertura')
        for rid in mapped:
            if rid in blocks and blocks[rid]['removed']:
                continue
            if rid not in blocks:
                err(rel(files['design.md']), f'mapeamento cita {rid}, que não existe em requirements.md')
        for rid, ts in cov.items():
            for t in ts:
                if t not in tasks or tasks[t]['removed']:
                    err(rel(files['tasks.md']), f'cobertura cita {t}, que não existe ou foi removida')
            if rid in blocks and blocks[rid]['removed'] and ts and 'removido' not in ' '.join(ts).lower():
                pass
        # NFR deve aparecer em alguma tarefa
        for rid in active:
            if rid.startswith('NFR') and not any(rid in t['req'] for t in tasks.values()):
                warn(rel(files['tasks.md']), f'{rid} não é citado por nenhuma tarefa')

        # ---- tarefas
        total_h = 0.0
        for tid, t in tasks.items():
            if t['removed']:
                continue
            for need, has in (('Requisito', t['has_req']), ('Dependências', t['has_dep']), ('Verificação', t['verif'])):
                if not has:
                    err(rel(files['tasks.md']), f'{tid} sem **{need}:**')
            if t['est'] is None:
                err(rel(files['tasks.md']), f'{tid} sem Prioridade/Estimativa no formato padrão')
            else:
                total_h += t['est']
                if not (1 <= t['est'] <= 4):
                    err(rel(files['tasks.md']), f'{tid} estimativa {t["est"]}h fora de 1 a 4 h')
            for r in t['req']:
                if r not in blocks or blocks[r]['removed']:
                    err(rel(files['tasks.md']), f'{tid} cita {r}, inexistente ou removido')
            for dep in t['dep_local']:
                if dep not in tasks or tasks[dep]['removed']:
                    err(rel(files['tasks.md']), f'{tid} depende de {dep}, inexistente ou removida')
            for sp in t['dep_spec']:
                if sp not in specs:
                    err(rel(files['tasks.md']), f'{tid} depende de SPEC-{sp}, fora do catálogo')
        all_tasks[sid] = tasks
        # grafo de tarefas
        for tid, t in tasks.items():
            if t['removed']:
                continue
            node = (sid, tid)
            task_graph.setdefault(node, set())
            for dep in t['dep_local']:
                task_graph[node].add((sid, dep))
            for (sp, dt) in t['dep_cross']:
                task_graph[node].add((sp, dt))

        # ---- referências dentro do texto
        full = req_t + des_t + tsk_t
        for p in set(re.findall(r'\bP-(\d{2})\b', full)):
            if f'### P-{p}' not in constitution:
                err(rel(d), f'referência a P-{p} inexistente na constituição')
        for a in set(re.findall(r'\bADR-(\d{3})\b', full)):
            if not list((L.ROOT / 'docs/adr').glob(f'ADR-{a}-*.md')):
                err(rel(d), f'referência a ADR-{a} inexistente')
        for s in set(re.findall(r'\bSPEC-(\d{3})\b', full)):
            if s not in specs:
                err(rel(d), f'referência a SPEC-{s} fora do catálogo')
        crates = L.crates()
        for c in set(re.findall(r'-p ([a-z][a-z-]+)', full)):
            if c not in crates:
                err(rel(d), f'cargo -p {c}: crate fora de docs/architecture/crates.toml')
        for c in set(re.findall(r'core/([a-z][a-z-]+)/', full)):
            if c not in crates:
                err(rel(d), f'caminho core/{c}/: crate fora de docs/architecture/crates.toml')
        for c in set(re.findall(r'`([a-z]+(?:-[a-z]+)*-engine)`', full)):
            if c not in crates:
                err(rel(d), f'`{c}` não é um crate registrado')
        for stale in ('27 modos', 'ORA 0.0.6', 'tools::', 'StrokeCommitter', 'HistoryEngine'):
            if stale in full:
                err(rel(d), f'termo obsoleto encontrado: {stale!r}')
        check_paths(d, full)
        cat['_horas'] = total_h
        cat['_tarefas'] = len([t for t in tasks.values() if not t['removed']])

    # ---- ciclos e referências cruzadas
    for (sp, t), deps in task_graph.items():
        for (dsp, dt) in deps:
            if dsp in all_tasks and (dt not in all_tasks[dsp] or all_tasks[dsp][dt]['removed']):
                err(f'SPEC-{sp}', f'{t} depende de SPEC-{dsp} {dt}, inexistente')
    color = {}

    def dfs(n, stack):
        color[n] = 1
        for m in task_graph.get(n, ()):
            if m not in task_graph:
                continue
            if color.get(m) == 1:
                err('dependências', 'ciclo: ' + ' -> '.join(f'SPEC-{a} {b}' for a, b in stack + [n, m]))
            elif color.get(m) is None:
                dfs(m, stack + [n])
        color[n] = 2

    for n in list(task_graph):
        if color.get(n) is None:
            dfs(n, [])
    return seen


PLANNED = None


def planned_paths():
    global PLANNED
    if PLANNED is None:
        p = L.ROOT / 'tools/sdd/planned-paths.txt'
        PLANNED = {x.strip() for x in L.read(p).splitlines() if x.strip() and not x.startswith('#')} if p.exists() else set()
    return PLANNED


def check_paths(d, text):
    """Caminhos citados entre crases em contracts/docs/spikes/.ai devem existir ou estar em planned-paths.txt."""
    for pth in set(re.findall(r'`((?:contracts|docs|spikes|\.ai)/[A-Za-z0-9_./*<>-]+\.[a-z]{2,4})`', text)):
        if '*' in pth or '<' in pth:
            continue
        if (L.ROOT / pth).exists() or pth in planned_paths():
            continue
        err(rel(d), f'caminho citado não existe e não está em planned-paths.txt: {pth}')


# --------------------------------------------------------------------- ADRs
def check_adrs():
    consts = L.read(L.ROOT / 'docs/constitution.md')
    for f in sorted((L.ROOT / 'docs/adr').glob('ADR-*.md')):
        t = L.read(f)
        if not re.fullmatch(r'ADR-\d{3}-[a-z0-9-]+\.md', f.name):
            err(rel(f), 'nome fora do padrão')
        st = L.header_field(t, 'Status')
        if st not in L.ADR_STATUS and not (st or '').startswith('Substituída'):
            err(rel(f), f'Status inválido: {st!r}')
        for fld in ('Origem', 'Data', 'Resolvida por', 'Requisitos relacionados'):
            if L.header_field(t, fld) is None:
                err(rel(f), f'sem campo **{fld}:**')
        for p in set(re.findall(r'\bP-(\d{2})\b', t)):
            if f'### P-{p}' not in consts:
                err(rel(f), f'referência a P-{p} inexistente')
        for s in set(re.findall(r'SPEC-(\d{3})', t)):
            if s not in {r['spec_id'] for r in L.csv_rows('docs/requirements/spec-catalog.csv')}:
                err(rel(f), f'referência a SPEC-{s} fora do catálogo')
        check_paths(f, t)
        for stale in ('27 modos', 'ORA 0.0.6'):
            if stale in t:
                err(rel(f), f'termo obsoleto: {stale!r}')


# --------------------------------------------------------------------- links, governança
def check_links():
    for f in L.ROOT.rglob('*.md'):
        if any(part in ('.git', 'node_modules') for part in f.parts):
            continue
        t = L.read(f)
        for m in re.finditer(r'\[[^\]]+\]\(([^)#\s]+)(?:#[^)]*)?\)', t):
            tgt = m.group(1)
            if re.match(r'[a-z]+:', tgt):
                continue
            if not (f.parent / tgt).resolve().exists():
                err(rel(f), f'link quebrado: {tgt}')


def check_governance():
    for need in ('.github/CODEOWNERS', '.github/workflows/sdd-check.yml', '.github/rulesets/main-protection.json', '.github/ISSUE_TEMPLATE/config.yml', '.github/ISSUE_TEMPLATE/change-request.yml', '.github/ISSUE_TEMPLATE/gate-approval.yml', '.github/ISSUE_TEMPLATE/task.yml', '.github/ISSUE_TEMPLATE/spike.yml', '.github/ISSUE_TEMPLATE/open-question.yml', '.github/ISSUE_TEMPLATE/defect.yml', 'docs/governance/issue-conventions.md', 'docs/templates/README.md', 'docs/templates/spec-requirements-template.md', 'docs/templates/spec-design-template.md', 'docs/templates/spec-tasks-template.md', 'docs/templates/adr-template.md', 'docs/templates/spike-plan-template.md', 'docs/templates/spike-report-template.md', 'docs/templates/gate-review-template.md', 'docs/templates/test-plan-template.md', 'docs/templates/privacy-impact-template.md', 'docs/templates/decision-entry-template.md', 'docs/templates/risk-entry-template.md', 'docs/templates/release-baseline-template.md', 'docs/templates/status-report-template.md', 'docs/templates/meeting-minutes-template.md', 'docs/templates/onboarding-checklist-template.md', 'docs/templates/handover-template.md', '.github/PULL_REQUEST_TEMPLATE/spec.md', '.github/PULL_REQUEST_TEMPLATE/gate.md', '.github/PULL_REQUEST_TEMPLATE/adr.md', '.github/PULL_REQUEST_TEMPLATE/contract.md', '.github/PULL_REQUEST_TEMPLATE/governance.md', '.github/PULL_REQUEST_TEMPLATE/code.md', '.github/pull_request_template.md', 'tools/github/setup-labels-milestones.py', 'tools/github/README.md', 'tools/github/ghlib.py', 'tools/github/check_pr_title.py', 'tools/github/check_gate.py', 'tools/github/impact_comment.py', 'tools/github/move_card.py', 'tools/github/overdue.py', 'tools/github/weekly_report.py', 'tools/github/nudge_blocked.py', 'tools/github/tests/support.py', '.github/labeler.yml', '.github/workflows/labeler.yml', '.github/workflows/pr-title.yml', '.github/workflows/gate-check.yml', '.github/workflows/impact-comment.yml', '.github/workflows/move-card.yml', '.github/workflows/weekly.yml',
                 'Makefile', 'README.md', 'docs/governance/team-workflow.md', 'docs/governance/raci.md',
                 'docs/governance/change-control.md', 'docs/governance/risk-register.md',
                 'docs/governance/decision-log.md', 'docs/governance/project-charter.md',
                 'docs/governance/document-control.md', 'docs/governance/schedule-wbs.md',
                 'docs/architecture/ownership-matrix.md', 'docs/architecture/crates.toml'):
        if not (L.ROOT / need).exists():
            err(need, 'arquivo obrigatório ausente')
    rs = L.ROOT / '.github/rulesets/main-protection.json'
    if rs.exists():
        import json
        try:
            names = [r['type'] for r in json.loads(L.read(rs))['rules']]
        except Exception as e:  # noqa: BLE001
            err(rel(rs), f'JSON inválido: {e}')
        else:
            for need in ('pull_request', 'required_status_checks', 'non_fast_forward', 'deletion'):
                if need not in names:
                    err(rel(rs), f'regra obrigatória ausente: {need}')
    co = L.ROOT / '.github/CODEOWNERS'
    if co.exists():
        txt = L.read(co)
        for path in ('/contracts/', '/docs/adr/', '/.ai/sdd/specs/', '/docs/governance/', '/.github/', '/core/'):
            if path not in txt:
                err('.github/CODEOWNERS', f'sem regra para {path}')
    for f in sorted((L.ROOT / 'docs/governance').glob('*.md')):
        t = L.read(f)
        if f.name == 'review-report-2026-11-25.md':
            continue
        for fld in ('Versão', 'Data', 'Status', 'Dono'):
            if L.header_field(t, fld) is None:
                err(rel(f), f'cabeçalho de controle sem **{fld}:**')
    # decisões abertas devem ter padrão recomendado
    dl = L.ROOT / 'docs/governance/decision-log.md'
    if dl.exists():
        for line in L.read(dl).splitlines():
            if re.match(r'\|\s*DEC-\d{3}', line):
                cells = [c.strip() for c in line.strip('|').split('|')]
                if len(cells) < 6 or not cells[3]:
                    err('decision-log.md', f'linha sem padrão recomendado: {cells[0]}')


def check_generated_fresh():
    import subprocess
    r = subprocess.run([sys.executable, str(L.ROOT / 'tools/sdd/generate.py'), '--check'], capture_output=True, text=True)
    if r.returncode != 0:
        err('arquivos gerados', (r.stdout + r.stderr).strip() or 'arquivos gerados desatualizados: rode `make docs` e faça commit')


def main():
    summary = '--summary' in sys.argv
    strict = '--strict' in sys.argv
    reqs, specs = load_catalogs()
    check_catalogs(reqs, specs)
    check_specs(reqs, specs)
    check_adrs()
    check_links()
    check_governance()
    check_generated_fresh()
    if not summary:
        for e in ERR:
            print('ERRO   ', e)
        for w in WARN:
            print('AVISO  ', w)
    print(f'sdd-check: {len(ERR)} erro(s), {len(WARN)} aviso(s)')
    if ERR or (strict and WARN):
        sys.exit(1)


if __name__ == '__main__':
    main()
