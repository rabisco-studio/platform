#!/usr/bin/env python3
"""Gera o site estático de pré-visualização (uma página HTML) a partir dos documentos do repositório.

Conteúdo: índice de specs (INDEX.md), cobertura por release (coverage.md), decisões abertas
(decision-log.md), riscos registrados (risk-register.md) e links para os documentos no GitHub.
Somente biblioteca padrão do Python 3. Não usa JavaScript nem recursos externos.

Uso: python3 tools/sdd/build_site.py [--out DIR] [--root DIR] [--repo ORG/REPO] [--branch main]
"""
import datetime
import html
import pathlib
import re
import sys

DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]
LINKS = [
    ('README (guia de entrada)', 'README.md'), ('Charter do projeto', 'docs/governance/project-charter.md'),
    ('Fluxo da equipe', 'docs/governance/team-workflow.md'), ('Constituição', 'docs/constitution.md'),
    ('Roadmap (PLAN)', '.ai/sdd/PLAN.md'), ('Índice de specs', '.ai/sdd/INDEX.md'),
    ('Cobertura', 'docs/requirements/coverage.md'), ('ADRs', 'docs/adr/README.md'),
    ('Registro de decisões', 'docs/governance/decision-log.md'), ('Registro de riscos', 'docs/governance/risk-register.md'),
    ('Cronograma', 'docs/governance/schedule-wbs.md'), ('Contratos', 'contracts/README.md'),
]
CSS = """
:root{--bg:#fff;--fg:#1f2328;--mut:#59636e;--line:#d1d9e0;--head:#f6f8fa;--link:#0969da}
@media (prefers-color-scheme:dark){:root{--bg:#0d1117;--fg:#e6edf3;--mut:#9198a1;--line:#30363d;--head:#161b22;--link:#4493f8}}
body{background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif;margin:0 auto;max-width:72rem;padding:1rem}
h1{margin-bottom:.2rem}h2{margin-top:2rem;border-bottom:1px solid var(--line);padding-bottom:.3rem}
a{color:var(--link)}p.mut{color:var(--mut)}
.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:.9rem}
th,td{border:1px solid var(--line);padding:.35rem .6rem;text-align:left;vertical-align:top}th{background:var(--head)}
ul.links{columns:2;padding-left:1.2rem}@media(max-width:40rem){ul.links{columns:1}}
"""


def cells(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def table_after(text, heading_regex):
    """Linhas (listas de células) da primeira tabela depois do cabeçalho que casa heading_regex."""
    m = re.search(heading_regex, text, flags=re.M)
    if not m:
        return None, []
    rows, started = [], False
    for line in text[m.end():].split('\n'):
        if line.startswith('|'):
            started = True
            rows.append(cells(line))
        elif started:
            break
    rows = [r for r in rows if not all(re.fullmatch(r':?-{3,}:?', c) for c in r)]
    return (rows[0], rows[1:]) if rows else (None, [])


def render_cell(value, base):
    """Escapa o HTML; links Markdown [t](u) viram <a>, com caminhos relativos apontando para o GitHub."""
    out, last = [], 0
    for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', value):
        out.append(html.escape(value[last:m.start()]))
        url = m.group(2)
        if not re.match(r'[a-z]+://', url):
            url = base + url.lstrip('./')
        out.append(f'<a href="{html.escape(url, quote=True)}">{html.escape(m.group(1))}</a>')
        last = m.end()
    out.append(html.escape(value[last:]))
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', ''.join(out))


def html_table(head, rows, base):
    if not head:
        return '<p class="mut">Sem dados.</p>'
    th = ''.join(f'<th>{html.escape(h)}</th>' for h in head)
    body = ''.join('<tr>' + ''.join(f'<td>{render_cell(c, base)}</td>' for c in r) + '</tr>' for r in rows)
    return f'<div class="wrap"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def read(root, rel):
    p = root / rel
    return p.read_text(encoding='utf-8') if p.exists() else ''


def build(root, repo='rabisco-studio/platform', branch='main', now=None):
    root = pathlib.Path(root)
    blob = f'https://github.com/{repo}/blob/{branch}/'
    now = now or datetime.datetime.now(datetime.timezone.utc)
    sdd_base = blob + '.ai/sdd/'

    idx_head, idx_rows = table_after(read(root, '.ai/sdd/INDEX.md'), r'^# Índice de especificações.*$')
    cov_text = read(root, 'docs/requirements/coverage.md')
    cov_head, cov_rows = table_after(cov_text, r'^## Por release\s*$')
    summary = [l[2:] for l in cov_text.split('\n') if l.startswith('- ') and 'Requisitos' in l or l.startswith('- Specs')]
    dec_text = read(root, 'docs/governance/decision-log.md')
    # a tabela de decisões é lida linha a linha (DEC-nnn)
    dec_head = ['ID', 'Decisão', 'Opções', 'Padrão recomendado', 'Dono', 'Prazo', 'Status']
    dec_rows = [cells(l) for l in dec_text.split('\n') if re.match(r'\|\s*DEC-\d+', l)]
    dec_open = [r for r in dec_rows if len(r) >= 7 and 'aberta' in r[6].lower()]
    rsk_text = read(root, 'docs/governance/risk-register.md')
    rsk_head = ['ID', 'Risco', 'P', 'I', 'Exp.', 'Mitigação', 'Dono', 'Gatilho']
    rsk_rows = [cells(l) for l in rsk_text.split('\n') if re.match(r'\|\s*RSK-\d+', l)]
    rsk_rows.sort(key=lambda r: -int(r[4]) if len(r) > 4 and r[4].isdigit() else 0)

    links = ''.join(f'<li><a href="{html.escape(blob + p, quote=True)}">{html.escape(t)}</a></li>' for t, p in LINKS)
    sums = ''.join(f'<li>{render_cell(s, blob)}</li>' for s in summary)
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rabisco — pré-visualização das especificações</title><style>{CSS}</style></head>
<body>
<h1>Rabisco — especificações e governança</h1>
<p class="mut">Pré-visualização gerada automaticamente a partir da branch <code>{html.escape(branch)}</code> de
<a href="https://github.com/{html.escape(repo)}">{html.escape(repo)}</a> em {now.strftime('%Y-%m-%d %H:%M')} UTC.
Os documentos no GitHub são a fonte da verdade; esta página é só uma vista. Todos os direitos reservados (veja o
arquivo <a href="{html.escape(blob + 'LICENSE', quote=True)}">LICENSE</a>).</p>
<h2>Índice de specs</h2>
{html_table(idx_head, idx_rows, sdd_base)}
<h2>Cobertura por release</h2>
<ul>{sums}</ul>
{html_table(cov_head, cov_rows, blob)}
<h2>Decisões abertas</h2>
{html_table(dec_head, dec_open, blob)}
<h2>Riscos registrados (maior exposição primeiro)</h2>
{html_table(rsk_head, rsk_rows, blob)}
<h2>Documentos</h2>
<ul class="links">{links}</ul>
</body></html>
"""


def main(argv):
    def opt(name, default):
        return argv[argv.index(name) + 1] if name in argv else default
    out = pathlib.Path(opt('--out', '_site'))
    page = build(opt('--root', DEFAULT_ROOT), opt('--repo', 'rabisco-studio/platform'), opt('--branch', 'main'))
    out.mkdir(parents=True, exist_ok=True)
    (out / 'index.html').write_text(page, encoding='utf-8', newline='\n')
    (out / '.nojekyll').write_text('', encoding='utf-8')
    print(f'Site gerado em {out / "index.html"} ({len(page)} bytes)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
