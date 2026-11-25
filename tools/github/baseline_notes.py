#!/usr/bin/env python3
"""Notas de uma baseline (template docs/templates/release-baseline-template.md).

Usado pelo workflow `baseline-release` (push de tag `baseline-R<n>-v<n>`), que publica o
resultado como GitHub Release marcado como pre-release, para o PMO revisar.

  --validate TAG        só valida o formato `baseline-R<n>-v<n>` (R1 a R5)
  --notes TAG           imprime as notas em Markdown
    --strict-ok         marca "make strict passa" (o workflow só chega aqui se passou)
    --today AAAA-MM-DD  data (padrão: hoje)
    --root DIR          raiz do repositório (padrão: o repositório do script)

Escopo congelado: INDEX.md; cobertura: coverage.md; decisões abertas: decision-log.md;
riscos com exposição >= 12: risk-register.md; mudanças: commits desde a baseline anterior.
Não cria tag nem release.
"""
import datetime
import pathlib
import re
import sys

import ghlib as G
import overdue as O

TAG_RE = re.compile(r'^baseline-(R[1-5])-v([1-9]\d*)$')
RELEASE_NAME = {'R1': 'R1 Local Studio (Fases 1 a 4)', 'R2': 'R2 Cloud (Fase 5)', 'R3': 'R3 Collab (Fase 6)',
                'R4': 'R4 Everywhere (Fase 7)', 'R5': 'R5 Pro (Fase 8)'}


def parse_tag(tag):
    m = TAG_RE.match(tag or '')
    if not m:
        raise ValueError(f'tag inválida: {tag!r}. Use baseline-R<n>-v<n>, por exemplo baseline-R1-v1 (n de R: 1 a 5).')
    return m.group(1), int(m.group(2))


def _cells(line):
    return [c.strip() for c in line.strip().strip('|').split('|')]


def scope_rows(root, release):
    rows = []
    for line in (root / '.ai/sdd/INDEX.md').read_text(encoding='utf-8').splitlines():
        c = _cells(line)
        if len(c) == 7 and re.search(r'SPEC-\d{3}', c[0]) and c[2] == release:
            sid = re.search(r'SPEC-\d{3}', c[0]).group(0)
            obs = 'spec escrita' if c[5] == 'escrita' else 'planejada: ainda sem spec'
            rows.append((sid, c[1], c[6], obs))
    return rows


def coverage_row(root, release):
    for line in (root / 'docs/requirements/coverage.md').read_text(encoding='utf-8').splitlines():
        c = _cells(line)
        if len(c) == 5 and c[0] == release:
            return {'reqs': c[1], 'cobertos': c[2], 'specs': c[3], 'escritas': c[4]}
    return None


def risks(root, min_exp=12):
    out = []
    for line in (root / 'docs/governance/risk-register.md').read_text(encoding='utf-8').splitlines():
        c = _cells(line)
        if len(c) >= 5 and re.fullmatch(r'RSK-\d+', c[0]) and c[4].isdigit() and int(c[4]) >= min_exp:
            out.append((c[0], c[1], int(c[4])))
    return out


def open_decisions(root):
    p = root / 'docs/governance/decision-log.md'
    return O.decisions(p.read_text(encoding='utf-8')) if p.exists() else []


def previous_tag(root, tag):
    tags = G.git(['tag', '--list', 'baseline-*', '--sort=-creatordate'], cwd=root, check=False).split()
    others = [t for t in tags if t != tag]
    return others[0] if others else None


def changes(root, tag):
    prev = previous_tag(root, tag)
    head = tag if G.git(['rev-parse', '-q', '--verify', f'refs/tags/{tag}'], cwd=root, check=False).strip() else 'HEAD'
    rng = f'{prev}..{head}' if prev else head
    out = G.git(['log', rng, '--no-merges', '--format=%h %s', '-n', '40'], cwd=root, check=False)
    return prev, [l for l in out.splitlines() if l.strip()]


def render(tag, today, root=None, strict_ok=False):
    root = pathlib.Path(root or G.ROOT)
    release, n = parse_tag(tag)
    prev, log = changes(root, tag)
    cov = coverage_row(root, release)
    L_ = [f'# Baseline {release} v{n} — notas', '',
          '> **Pre-release gerado automaticamente.** O PMO revisa, preenche as assinaturas e só então '
          'desmarca "pre-release". Nada aqui substitui a aprovação humana.', '',
          f'**Tag:** {tag}', f'**Data:** {today.isoformat()}',
          '**Aprovado por:** pendente (PO e Arquiteto-chefe)', f'**Fase / Release:** {RELEASE_NAME[release]}', '',
          '## Escopo congelado', '| Spec | Título | Gate final | Observação |', '|---|---|---|---|']
    L_ += [f'| {s} | {t} | {g} | {o} |' for s, t, g, o in scope_rows(root, release)] or ['| — | — | — | — |']
    L_ += ['', '## Cobertura na data']
    if cov:
        L_.append(f'- Requisitos do release com spec escrita: **{cov["cobertos"]} de {cov["reqs"]}** '
                  f'(specs escritas: {cov["escritas"]} de {cov["specs"]})')
    else:
        L_.append('- Cobertura do release não encontrada em coverage.md.')
    L_ += ['- Pendências aceitas (com justificativa): a preencher pelo PMO', '',
           '## Mudanças desde a baseline anterior',
           f'Baseline anterior: {prev or "nenhuma (primeira baseline)"}. Commits no intervalo (CRs: ver `change-control.md`):', '']
    L_ += [f'- {c}' for c in log] or ['- Nenhum commit no intervalo.']
    L_ += ['', '## Decisões e riscos relevantes', '**Decisões abertas:**']
    L_ += [f'- {i}: {t[:100]} (prazo: {p})' for i, t, p in open_decisions(root)] or ['- Nenhuma.']
    L_ += ['', '**Riscos com exposição 12 ou mais:**']
    L_ += [f'- {i} (exposição {e}): {t[:100]}' for i, t, e in risks(root)] or ['- Nenhum.']
    L_ += ['', '## Verificações',
           f'- [{"x" if strict_ok else " "}] make strict passa (avisos também falham)',
           '- [ ] Todas as ADRs do escopo estão Aprovadas',
           '- [ ] Nenhuma pergunta Q- aberta nas specs do escopo',
           '- [ ] Catálogos, rastreabilidade e cobertura regenerados', '',
           '## Assinaturas', '| Papel | Nome | Data |', '|---|---|---|', '| PO | | |', '| Arquiteto-chefe | | |']
    return '\n'.join(L_) + '\n'


def main(argv):
    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv else default
    try:
        if '--validate' in argv:
            release, n = parse_tag(opt('--validate'))
            print(f'Tag válida: {release}, versão {n}')
            return 0
        if '--notes' in argv:
            today = datetime.date.fromisoformat(opt('--today')) if opt('--today') else datetime.date.today()
            print(render(opt('--notes'), today, opt('--root'), strict_ok='--strict-ok' in argv))
            return 0
    except ValueError as e:
        print(f'ERRO: {e}', file=sys.stderr)
        return 1
    print(__doc__)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
