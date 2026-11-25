#!/usr/bin/env python3
"""Check do gate: valida PRs que alteram `.ai/sdd/specs/*/.status`.

Regras (team-workflow.md, seção 2; README, seção 4):
  (a) a mudança é uma transição válida de STAGES: avança no máximo 1 etapa ou volta (reabertura);
  (b) o autor do PR não escreveu requirements.md, design.md nem tasks.md da spec (git log),
      e o PR só toca esses documentos no cabeçalho `**Status:**`;
  (c) cabeçalhos Status coerentes com o novo .status (chama o sdd_check);
  (d) o corpo do PR usa o template gate ("## Gate" e "## Registro da revisão").
Opcional: com ORG_READ_TOKEN, confirma que o autor pertence à equipe aprovadora do gate;
sem o segredo, só avisa.

Entrada por variáveis de ambiente (nunca interpoladas em shell):
  BASE_SHA, HEAD_SHA, PR_AUTHOR, PR_BODY, [GATE_AUTHOR_ALIASES], [ORG_READ_TOKEN]
Saída: 0 sem erros (avisos não falham); 1 com erros.
"""
import os
import re
import subprocess
import sys

import ghlib as G
import sddlib as L

DOCS = ('requirements.md', 'design.md', 'tasks.md')
GATE_OF = {  # novo .status -> gate
    'requirements:approved': 'G1', 'design:approved': 'G2', 'tasks:approved': 'G3',
    'implementation:done': 'G4', 'review:done': 'G5',
}
TEAMS = {'G1': ['product', 'tech-leads'], 'G2': ['architects'], 'G3': ['tech-leads'],
         'G4': ['tech-leads', 'qa'], 'G5': ['product']}
ORG = 'rabisco-studio'


def check_transition(old, new):
    """Devolve mensagem de erro ou None."""
    if new not in L.STAGES:
        return f'estado desconhecido "{new}" (válidos: {", ".join(L.STAGES)})'
    if old is None:  # spec nova
        return None if new == L.STAGES[0] else f'spec nova deve começar em {L.STAGES[0]}, não em {new}'
    if old not in L.STAGES:
        return f'estado anterior desconhecido "{old}"'
    delta = L.STAGES.index(new) - L.STAGES.index(old)
    if delta > 1:
        return f'{old} -> {new} pula {delta - 1} etapa(s); um gate avança no máximo uma etapa'
    return None  # 0, +1 ou recuo (reabertura por CR)


def author_matches(login, aliases, name, email):
    cands = {login.lower(), *[a.lower() for a in aliases]}
    e = (email or '').lower()
    local = e.split('@')[0]
    if e.endswith('@users.noreply.github.com'):
        local = local.split('+')[-1]
    return (name or '').lower() in cands or e in cands or local in cands


def doc_authors(spec_dir, base_sha, repo=None):
    """[(nome, email, ref)] de quem alterou os três documentos até a base do PR."""
    out = []
    for d in DOCS:
        path = f'.ai/sdd/specs/{spec_dir}/{d}'
        txt = G.git(['log', base_sha, '--format=%an%x09%ae%x09%h', '--', path], cwd=repo, check=False)
        for line in txt.splitlines():
            parts = line.split('\t')
            if len(parts) == 3:
                out.append((parts[0], parts[1], f'{parts[2]} ({d})'))
    return out


def only_header_changed(spec_dir, base_sha, head_sha, repo=None):
    """Erros se o PR mexer em requirements/design/tasks fora da linha `**Status:**`."""
    errs = []
    for d in DOCS:
        path = f'.ai/sdd/specs/{spec_dir}/{d}'
        diff = G.git(['diff', '-U0', base_sha, head_sha, '--', path], cwd=repo, check=False)
        for line in diff.splitlines():
            if line[:1] in '+-' and not line.startswith(('+++', '---')):
                if not re.match(r'^[+-]\*\*Status:\*\*', line):
                    errs.append(f'{d}: o PR altera mais que o cabeçalho Status ("{line[:60]}")')
                    break
    return errs


def team_member(login, team, token):
    """True/False, ou None se não deu para consultar."""
    code, out, err = G.gh(['api', f'orgs/{ORG}/teams/{team}/memberships/{login}', '--jq', '.state'], token=token)
    if code == 0:
        return out.strip() == 'active'
    return False if 'Not Found' in err or '404' in err else None


def run_sdd_check(repo=None):
    r = subprocess.run([sys.executable, str(L.ROOT / 'tools/sdd/sdd_check.py')], capture_output=True, text=True,
                       encoding='utf-8', cwd=str(repo or L.ROOT))
    return r.returncode, (r.stdout + r.stderr).strip()


def evaluate(env, repo=None, sdd_check=run_sdd_check, member=team_member):
    """Devolve (erros, avisos)."""
    errors, warns = [], []
    base, head = env['BASE_SHA'], env['HEAD_SHA']
    author, body = env.get('PR_AUTHOR', ''), env.get('PR_BODY', '')
    aliases = [a.strip() for a in env.get('GATE_AUTHOR_ALIASES', '').split(',') if a.strip()]
    changed = G.git(['diff', '--name-only', base, head], cwd=repo).splitlines()
    status_files = [f for f in changed if re.fullmatch(r'\.ai/sdd/specs/[^/]+/\.status', f)]
    if not status_files:
        return [], ['nenhum .status alterado: não é um PR de gate']
    if '## Gate' not in body or '## Registro da revisão' not in body:
        errors.append('(d) o corpo do PR deve usar o template gate (seções "## Gate" e "## Registro da revisão"): '
                      'abra o PR com ?template=gate.md')
    for f in status_files:
        spec_dir = f.split('/')[3]
        new = G.git(['show', f'{head}:{f}'], cwd=repo).strip()
        old = G.git(['show', f'{base}:{f}'], cwd=repo, check=False).strip() or None
        e = check_transition(old, new)
        if e:
            errors.append(f'(a) {spec_dir}: {e}')
        if old == new:
            continue
        for name, email, ref in doc_authors(spec_dir, base, repo):
            if author_matches(author, aliases, name, email):
                errors.append(f'(b) {spec_dir}: o autor do PR ({author}) escreveu {ref}; autor não aprova o próprio trabalho')
                break
        errors += [f'(b) {spec_dir}: {m}' for m in only_header_changed(spec_dir, base, head, repo)]
        advancing = old is not None and new in L.STAGES and old in L.STAGES and L.STAGES.index(new) > L.STAGES.index(old)
        gate = GATE_OF.get(new) if advancing else None
        if gate:
            token = env.get('ORG_READ_TOKEN')
            if not token:
                warns.append(f'{spec_dir}: sem ORG_READ_TOKEN, não confirmei que {author} pertence a '
                             f'{" ou ".join(TEAMS[gate])} ({gate}); confirme manualmente')
            else:
                res = [member(author, t, token) for t in TEAMS[gate]]
                if any(r is True for r in res):
                    pass
                elif all(r is None for r in res):
                    warns.append(f'{spec_dir}: não consegui consultar a equipe aprovadora do {gate} (token sem permissão?)')
                else:
                    errors.append(f'(equipe) {spec_dir}: {author} não pertence à equipe aprovadora do {gate} '
                                  f'({" ou ".join(TEAMS[gate])})')
    code, out = sdd_check(repo)
    if code != 0:
        errors.append('(c) sdd_check falhou (cabeçalhos Status incoerentes com o .status?):\n' + out)
    return errors, warns


def main():
    env = {k: os.environ.get(k, '') for k in ('BASE_SHA', 'HEAD_SHA', 'PR_AUTHOR', 'PR_BODY',
                                              'GATE_AUTHOR_ALIASES', 'ORG_READ_TOKEN')}
    if not env['BASE_SHA'] or not env['HEAD_SHA']:
        print('BASE_SHA e HEAD_SHA são obrigatórios', file=sys.stderr)
        return 2
    errors, warns = evaluate(env)
    for w in warns:
        G.warn(w)
    for e in errors:
        G.say('error', e.replace('\n', '%0A'))
        print('ERRO   ', e)
    print(f'check-gate: {len(errors)} erro(s), {len(warns)} aviso(s)')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
