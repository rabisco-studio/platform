#!/usr/bin/env python3
"""Cria a pasta de uma spec nova a partir dos templates (`make new-spec N=018`).

O que faz:
  1. valida que a spec existe em docs/requirements/spec-catalog.csv e ainda é "planejada";
  2. cria .ai/sdd/specs/NNN-slug/ com requirements.md, design.md e tasks.md (cabeçalhos
     preenchidos com área, release, rigor, ADRs e requisitos globais do catálogo) e o
     `.status` com `requirements:draft`; design e tasks levam "rascunho antecipado; não vinculante";
  3. marca a spec como "escrita" no catálogo;
  4. roda o gerador (tools/sdd/generate.py).
Recusa se a pasta já existir. Os blocos de exemplo dos templates (FR-001, T-001...) são
removidos para o esqueleto passar no sdd-check; o autor acrescenta os reais.

Uso: python3 tools/sdd/new_spec.py 018 [--root DIR] [--no-generate]
Somente biblioteca padrão do Python 3.
"""
import csv
import io
import pathlib
import re
import subprocess
import sys

DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]
CATALOG = 'docs/requirements/spec-catalog.csv'
REQ_CATALOG = 'docs/requirements/requirements-catalog.csv'
TEMPLATES = {
    'requirements.md': 'docs/templates/spec-requirements-template.md',
    'design.md': 'docs/templates/spec-design-template.md',
    'tasks.md': 'docs/templates/spec-tasks-template.md',
}
EXAMPLE_HEADING = re.compile(r'^### (?:US|N?FR|D|Q|TD|T)-\d{3}\b')
EXAMPLE_ROW = re.compile(r'^\|\s*(?:N?FR|US|TD|T)-\d{3}\s*\|')
TASK_FORMAT = ('<!-- Formato aceito pelo sdd-check: "### T-001 — Título", "**Requisito:** FR-001", '
               '"**Prioridade:** Must | **Estimativa:** 2h" (1 a 4 h), "**Dependências:** nenhuma", '
               '"**Checklist:**", "**Verificação:** `comando`". Cobertura: tabela "| FR-001 | T-001 |". -->')


class NewSpecError(Exception):
    pass


def read_csv(root, rel):
    text = (root / rel).read_bytes().decode('utf-8')
    return list(csv.DictReader(io.StringIO(text)))


def normalize(n):
    n = str(n).strip().upper().removeprefix('SPEC-')
    if not n.isdigit() or not 1 <= int(n) <= 999:
        raise NewSpecError(f'número de spec inválido: {n!r} (use, por exemplo, 018)')
    return f'{int(n):03d}'


def header_block(title, fields):
    return f'# {title}\n\n' + '\n'.join(f'**{k}:** {v}' for k, v in fields) + '\n\n---\n'


def sanitize(template_text, doc):
    """Corpo do template (a partir de '## 1.') sem os blocos de exemplo, com uma dica no lugar."""
    start = re.search(r'^## ', template_text, flags=re.M)
    body = template_text[start.start():] if start else template_text
    out, skipping, hinted = [], False, False
    for line in body.split('\n'):
        if EXAMPLE_HEADING.match(line):
            skipping = True
            if not hinted:
                shape = line.lstrip('# ').replace('`', '')
                out += [f'_Acrescente aqui os blocos no formato do template (por exemplo, "### {shape}")._', '']
                hinted = True
            continue
        if skipping:
            if line.startswith('## ') or (line.startswith('### ') and not EXAMPLE_HEADING.match(line)):
                skipping = False
                hinted = False
            else:
                continue
        if EXAMPLE_ROW.match(line) or line.strip() == '...':
            continue
        out.append(line)
    text = '\n'.join(out)
    if doc == 'tasks.md':
        text = text.replace('## 2. Cobertura', '## Cobertura FR/NFR → Tarefas')
        text = text.replace('## 3. Tarefas', '## 3. Tarefas\n\n' + TASK_FORMAT, 1)
    return re.sub(r'\n{3,}', '\n\n', text).rstrip('\n') + '\n'


def build_files(root, row):
    sid = row['spec_id']
    title = f'SPEC-{sid}: {row["titulo"]}'
    adrs = sorted(set(re.findall(r'ADR-\d{3}', row['titulo'])))
    reqs = [r['id'] for r in read_csv(root, REQ_CATALOG) if r['spec_planejada'] == f'SPEC-{sid}']
    tags = 'contract' if row['area'] == 'contracts' else ''
    req_head = header_block(title, [
        ('Status', 'requirements:draft'), ('Área', row['area']), ('Release', row['release']),
        ('Rigor', row['rigor']), ('Tags', tags), ('ADRs', ', '.join(adrs) or 'nenhuma'),
        ('Depende de', 'a preencher pelo autor (ver .ai/sdd/PLAN.md)'),
        ('Requisitos globais', ', '.join(reqs) or 'nenhum no catálogo')])
    des_head = header_block(f'SPEC-{sid}: {row["titulo"]} — Design', [
        ('Status', 'design:draft (rascunho antecipado; não vinculante até requirements:approved)'),
        ('Requisitos', '`requirements.md`')])
    tsk_head = header_block(f'SPEC-{sid}: {row["titulo"]} — Tasks', [
        ('Status', 'tasks:draft (rascunho antecipado; não vinculante até design:approved)'),
        ('Requisitos', '`requirements.md`'), ('Design', '`design.md`')])
    heads = {'requirements.md': req_head, 'design.md': des_head, 'tasks.md': tsk_head}
    files = {}
    for doc, rel in TEMPLATES.items():
        tpl = (root / rel).read_text(encoding='utf-8')
        files[doc] = heads[doc] + '\n' + sanitize(tpl, doc)
    files['.status'] = 'requirements:draft\n'
    return files


def mark_written(root, sid):
    path = root / CATALOG
    raw = path.read_bytes().decode('utf-8')
    lines = raw.split('\n')
    for i, line in enumerate(lines):
        if line.startswith(f'{sid},'):
            stripped = line.rstrip('\r')
            if not stripped.endswith(',planejada'):
                raise NewSpecError(f'linha da SPEC-{sid} do catálogo em formato inesperado')
            lines[i] = stripped[:-len('planejada')] + 'escrita' + line[len(stripped):]
            path.write_bytes('\n'.join(lines).encode('utf-8'))
            return
    raise NewSpecError(f'SPEC-{sid} não encontrada no catálogo')


def create(root, n, generate=True):
    """Cria a spec. Devolve a pasta criada. Levanta NewSpecError em qualquer recusa."""
    root = pathlib.Path(root)
    sid = normalize(n)
    row = next((r for r in read_csv(root, CATALOG) if r['spec_id'] == sid), None)
    if row is None:
        raise NewSpecError(f'SPEC-{sid} não existe em {CATALOG}')
    if row['estado'] != 'planejada':
        raise NewSpecError(f'SPEC-{sid} já está "{row["estado"]}" no catálogo; só specs "planejada" podem ser criadas')
    folder = root / '.ai/sdd/specs' / f'{sid}-{row["slug"]}'
    if folder.exists():
        raise NewSpecError(f'a pasta {folder.relative_to(root)} já existe; nada foi alterado')
    files = build_files(root, row)
    folder.mkdir(parents=True)
    try:
        for name, text in files.items():
            (folder / name).write_text(text, encoding='utf-8', newline='\n')
        mark_written(root, sid)
    except Exception:
        for p in folder.glob('*'):
            p.unlink()
        folder.rmdir()
        raise
    if generate:
        r = subprocess.run([sys.executable, str(root / 'tools/sdd/generate.py')], cwd=str(root),
                           capture_output=True, text=True, encoding='utf-8')
        if r.returncode != 0:
            raise NewSpecError('a spec foi criada, mas o gerador falhou: ' + (r.stderr or r.stdout).strip())
    return folder


def main(argv):
    args = [a for a in argv if not a.startswith('--')]
    root = DEFAULT_ROOT
    if '--root' in argv:
        root = pathlib.Path(argv[argv.index('--root') + 1])
        args = [a for a in args if a != str(root)]
    if len(args) != 1:
        print('uso: python3 tools/sdd/new_spec.py NNN [--root DIR] [--no-generate]   (ou: make new-spec N=018)',
              file=sys.stderr)
        return 2
    try:
        folder = create(root, args[0], generate='--no-generate' not in argv)
    except NewSpecError as e:
        print(f'ERRO: {e}', file=sys.stderr)
        return 1
    print(f'Spec criada em {folder.relative_to(root)}')
    print('Próximos passos: preencher requirements.md (Depende de, Tags, FRs), rodar `make verify` e abrir PR (?template=spec.md).')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
