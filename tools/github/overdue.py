#!/usr/bin/env python3
"""Lista itens abertos com prazo vencido ou sem data.

Fontes: docs/governance/decision-log.md (decisões com Status "Aberta") e as perguntas
Q- abertas dos requirements.md das specs. "Vencido" = prazo em data ISO (AAAA-MM-DD)
anterior a hoje. "Sem data" = item aberto sem data ISO no prazo (ex.: "Início da Fase 0").

Uso: python3 tools/github/overdue.py [--today AAAA-MM-DD] [--json]
Saída: sempre 0 (é informativo).
"""
import datetime
import json
import re
import sys

import ghlib as G
import sddlib as L

ISO = re.compile(r'\b(\d{4}-\d{2}-\d{2})\b')
OPEN_Q = re.compile(r'^- \*\*(Q-\d{3})[^\n]*$', flags=re.M)


def _date(text):
    m = ISO.search(text or '')
    if not m:
        return None
    try:
        return datetime.date.fromisoformat(m.group(1))
    except ValueError:
        return None


def decisions(text):
    """[(id, titulo, prazo_texto)] das decisões com Status Aberta."""
    out = []
    for line in text.splitlines():
        if not re.match(r'\|\s*DEC-\d{3}', line):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) >= 7 and 'aberta' in cells[6].lower():
            out.append((cells[0], cells[1], cells[5]))
    return out


def open_questions(root=None):
    """[(spec, id, texto)] das perguntas Q- abertas."""
    out = []
    for d in (L.written_specs() if root is None else sorted((root / '.ai/sdd/specs').iterdir())):
        rq = d / 'requirements.md'
        if not rq.exists():
            continue
        for m in OPEN_Q.finditer(rq.read_text(encoding='utf-8')):
            line = m.group(0)
            head = line.split('**R:**')[0]
            if re.search(r'\(aberta|aberta\b|TBD|\?\?', head, flags=re.I) and '**R:**' not in line:
                out.append((G.spec_id_from_dir(d.name), m.group(1), line[2:].strip()))
    return out


def classify(items, today):
    """items: [(origem, id, titulo, prazo_texto)] -> (vencidos, sem_data)."""
    overdue, undated = [], []
    for origin, ident, title, prazo in items:
        d = _date(prazo)
        row = {'origem': origin, 'id': ident, 'titulo': title, 'prazo': prazo, 'data': d.isoformat() if d else None}
        if d is None:
            undated.append(row)
        elif d < today:
            overdue.append(row)
    return overdue, undated


def collect(today, root=None):
    base = root or L.ROOT
    log = (base / 'docs/governance/decision-log.md')
    items = [('decision-log', i, t, p) for i, t, p in decisions(log.read_text(encoding='utf-8') if log.exists() else '')]
    items += [(spec, qid, text, text) for spec, qid, text in open_questions(root)]
    return classify(items, today)


def to_markdown(overdue, undated):
    out = ['### Vencidos (prazo em data ISO anterior a hoje)']
    out += [f'- **{r["id"]}** ({r["origem"]}): prazo {r["data"]} — {r["titulo"][:90]}' for r in overdue] or ['- Nenhum.']
    out += ['', '### Sem data (aberto sem prazo em AAAA-MM-DD)']
    out += [f'- **{r["id"]}** ({r["origem"]}): {r["prazo"][:70]}' for r in undated] or ['- Nenhum.']
    return '\n'.join(out) + '\n'


def main(argv):
    today = datetime.date.today()
    if '--today' in argv:
        today = datetime.date.fromisoformat(argv[argv.index('--today') + 1])
    overdue, undated = collect(today)
    if '--json' in argv:
        print(json.dumps({'vencidos': overdue, 'sem_data': undated}, ensure_ascii=False, indent=2))
    else:
        print(to_markdown(overdue, undated))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
