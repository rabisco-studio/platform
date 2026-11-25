"""Biblioteca comum do sdd-check e do gerador. Somente biblioteca padrão do Python 3."""
import csv, re, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
STAGES = ['requirements:draft', 'requirements:approved', 'design:draft', 'design:approved',
          'tasks:draft', 'tasks:approved', 'implementation:in-progress', 'implementation:done', 'review:done']
RIGOR = {'anchored', 'spec-first'}
TAGS = {'security', 'privacy', 'contract', 'format', 'perf'}
AREAS = {'core', 'backend', 'clients', 'platform', 'contracts'}
RELEASES = ['R1', 'R2', 'R3', 'R4', 'R5']
ADR_STATUS = {'Proposta', 'Aprovada', 'Rejeitada', 'Substituída'}


def read(p):
    return pathlib.Path(p).read_text(encoding='utf-8')


def csv_rows(rel):
    with open(ROOT / rel, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def header_field(text, name):
    m = re.search(r'^\*\*%s:\*\*\s*(.*)$' % re.escape(name), text, flags=re.M)
    return m.group(1).strip() if m else None


def parse_status_token(value):
    if not value:
        return None
    m = re.match(r'([a-z]+:[a-z-]+)', value)
    return m.group(1) if m else None


def expand_task_range(a, b):
    return ['T-%03d' % i for i in range(int(a), int(b) + 1)]


def requirement_blocks(text):
    """Devolve {id: {'removed': bool, 'cobre': [..], 'prio': str}} para FR-/NFR- (headings ###)."""
    out = {}
    for m in re.finditer(r'^### ((?:N?FR)-\d{3})(.*)$\n((?:.*\n)*?)(?=^### |^## |\Z)', text, flags=re.M):
        rid, rest, body = m.group(1), m.group(2), m.group(3)
        removed = 'Removido' in rest
        cm = re.search(r'^\*\*Cobre:\*\*\s*(.*)$', body, flags=re.M)
        cobre = [x.strip() for x in cm.group(1).split(',')] if cm else []
        pm = re.search(r'\((Must|Should|Could)\)', rest)
        out[rid] = {'removed': removed, 'cobre': cobre, 'prio': pm.group(1) if pm else ''}
    return out


def design_mapped(text):
    return set(re.findall(r'^\|\s*(FR-\d{3})\s*\|', text, flags=re.M))


def tasks_coverage(text):
    cov = {}
    m = re.search(r'^## Cobertura FR.*?\n(.*?)(?=^## )', text, flags=re.M | re.S)
    if m:
        for row in re.finditer(r'^\|\s*((?:N?FR)-\d{3})\s*\|\s*(.*?)\s*\|\s*$', m.group(1), flags=re.M):
            cov[row.group(1)] = re.findall(r'T-\d{3}', row.group(2))
    return cov


def parse_tasks(text):
    """{'T-001': {'removed':bool,'req':[..],'deps':[(spec|None,'T-xxx')...],'depspecs':[..],'verif':str,'has':{...}}}"""
    tasks = {}
    for m in re.finditer(r'^### (T-\d{3})\b(.*)$\n((?:.*\n)*?)(?=^### |^## |\Z)', text, flags=re.M):
        tid, title, body = m.group(1), m.group(2), m.group(3)
        removed = 'Removida' in title or 'Removido' in title
        req = re.search(r'^\*\*Requisito:\*\*\s*(.*)$', body, flags=re.M)
        dep = re.search(r'^\*\*Dependências:\*\*\s*(.*)$', body, flags=re.M)
        ver = re.search(r'^\*\*Verificação:\*\*\s*(.*)$', body, flags=re.M)
        est = re.search(r'^\*\*Prioridade:\*\*\s*(\w+)\s*\|\s*\*\*Estimativa:\*\*\s*([\d.]+)h', body, flags=re.M)
        deps_local, deps_cross, deps_spec = [], [], []
        if dep:
            d = dep.group(1)
            # intervalos "T-001 a T-007"
            for a, b in re.findall(r'T-(\d{3}) a T-(\d{3})', d):
                deps_local += expand_task_range(a, b)
            d2 = re.sub(r'T-\d{3} a T-\d{3}', '', d)
            for sp, ts in re.findall(r'SPEC-(\d{3})((?:\s*T-\d{3}[,\s]*(?:e\s*)?)+)', d2):
                for t in re.findall(r'T-\d{3}', ts):
                    deps_cross.append((sp, t))
            d3 = re.sub(r'SPEC-\d{3}((?:\s*T-\d{3}[,\s]*(?:e\s*)?)+)', '', d2)
            deps_local += re.findall(r'T-\d{3}', d3)
            deps_spec += re.findall(r'SPEC-(\d{3})', d3)
        tasks[tid] = {'removed': removed,
                      'req': re.findall(r'(?:N?FR)-\d{3}', req.group(1)) if req else [],
                      'dep_local': sorted(set(deps_local)), 'dep_cross': deps_cross, 'dep_spec': deps_spec,
                      'verif': ver.group(1) if ver else None, 'has_req': bool(req), 'has_dep': bool(dep),
                      'est': float(est.group(2)) if est else None, 'prio': est.group(1) if est else None}
    return tasks


def written_specs():
    base = ROOT / '.ai/sdd/specs'
    return sorted(p for p in base.iterdir() if p.is_dir()) if base.exists() else []


def crates():
    """Lê docs/architecture/crates.toml (formato simples: [crate] / deps = [...])."""
    reg = {}
    cur = None
    for line in read(ROOT / 'docs/architecture/crates.toml').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        m = re.match(r'\[([a-z-]+)\]$', line)
        if m:
            cur = m.group(1); reg[cur] = {'deps': [], 'fase': '1'}; continue
        m = re.match(r'deps\s*=\s*\[(.*)\]', line)
        if m and cur:
            reg[cur]['deps'] = [x.strip().strip('"') for x in m.group(1).split(',') if x.strip()]
        m = re.match(r'fase\s*=\s*"?(\w+)"?', line)
        if m and cur:
            reg[cur]['fase'] = m.group(1)
    return reg
