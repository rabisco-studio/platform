#!/usr/bin/env python3
"""Cria ou atualiza os labels e os milestones do repositório no GitHub.

Fonte dos dados: README.md (seções 8 e 9) e docs/governance/issue-conventions.md.
Só usa a biblioteca padrão do Python e a CLI `gh` (autenticada: `gh auth login`).

Por padrão roda em ENSAIO (somente leitura): mostra o que criaria, atualizaria
e ignoraria. Só escreve no GitHub com --apply.

Idempotente: o que já existe e está igual é ignorado; diferença de descrição ou
de cor é atualizada e relatada. NUNCA apaga nada (labels e milestones extras
são apenas contados).

Uso:
    python3 tools/github/setup-labels-milestones.py                # ensaio
    python3 tools/github/setup-labels-milestones.py --apply        # executa
    python3 tools/github/setup-labels-milestones.py --repo ORG/REPO

Códigos de saída:
    0  concluído (no ensaio, mesmo havendo mudanças a aplicar)
    1  erro inesperado (resposta inválida, falha de rede, etc.)
    2  `gh` ausente ou sem autenticação
    3  sem permissão para gerenciar labels e milestones no repositório
"""
import argparse
import json
import subprocess
import sys
from urllib.parse import quote

DEFAULT_REPO = 'rabisco-studio/platform'
MAX_LABEL_DESC = 100  # limite do GitHub

EXIT_ERROR, EXIT_NO_GH, EXIT_NO_PERMISSION = 1, 2, 3

# (nome, cor sem '#', descrição). O README só descreve grupos de labels; as descrições
# individuais seguem as que já estavam no GitHub, para não sobrescrevê-las.
LABELS = [
    ('task', '1d76db', 'Tarefa de implementação (T-xxx), criada após o G3'),
    ('gate', '5319e7', 'Pedido de aprovação de portão G1 a G5'),
    ('spike', 'fbca04', 'Experimento da Fase 0'),
    ('question', 'd876e3', 'Pergunta aberta ou decisão pendente'),
    ('defect', 'd73a4a', 'Erro em documento, contrato ou código'),
    ('change-request', 'e99695', 'Mudança em documento aprovado'),
    ('adr', '0e8a16', 'Decisão de arquitetura'),
    ('area:core', 'c5def5', 'Núcleo em Rust'),
    ('area:backend', 'c5def5', 'Backend Java/Spring Boot'),
    ('area:clients', 'c5def5', 'Clientes Flutter e web'),
    ('area:platform', 'c5def5', 'Plataforma, CI e tooling'),
    ('rigor:anchored', 'b60205', 'Rigor máximo: contratos, formato, sync, segurança'),
    ('rigor:spec-first', 'bfdadc', 'Rigor menor: UI, ferramentas, pincéis, filtros'),
    ('status-report', 'fef2c0', 'Relatório de status semanal (gerado pela rotina semanal)'),
    ('bloqueado', '000000', 'Aguardando outra issue, Q- ou DEC-'),
]

# (título, descrição). Sem data de entrega (README, seção 9).
MILESTONES = [
    ('Fase 0 Spikes', 'Fundações e spikes a–e: decisões e números, sem código de produto'),
    ('R1 Local Studio', 'Fases 1 a 4: editor híbrido desktop e offline'),
    ('R2 Cloud', 'Fase 5: conta, biblioteca, versões e sincronização'),
    ('R3 Collab', 'Fase 6: compartilhamento, colaboração em tempo real, comentários'),
    ('R4 Everywhere', 'Fase 7: mobile, web, acessibilidade e i18n'),
    ('R5 Pro', 'Fase 8: plugins, PSD, CMYK, editor de pincéis e filtros avançados'),
]

WRITE_PERMISSIONS = ('admin', 'maintain', 'push', 'triage')


class GhError(Exception):
    def __init__(self, message, permission=False):
        super().__init__(message)
        self.permission = permission


def gh(args, payload=None):
    """Executa `gh api ...` e devolve o JSON da resposta (ou None se vazia)."""
    cmd = ['gh', 'api', *args]
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    if data is not None:
        cmd += ['--input', '-']
    try:
        r = subprocess.run(cmd, input=data, capture_output=True)
    except FileNotFoundError:
        raise SystemExit(fail('a CLI `gh` não foi encontrada. Instale: https://cli.github.com', EXIT_NO_GH))
    out = r.stdout.decode('utf-8', 'replace')
    err = r.stderr.decode('utf-8', 'replace').strip()
    if r.returncode != 0:
        text = (err + ' ' + out).strip()
        low = text.lower()
        if 'gh auth login' in low or 'not logged in' in low or 'authentication' in low and 'token' in low:
            raise SystemExit(fail('`gh` sem autenticação. Rode `gh auth login`.', EXIT_NO_GH))
        permission = any(s in low for s in ('http 403', 'http 401', 'http 404', 'resource not accessible',
                                            'must have push access', 'must have admin'))
        raise GhError(text or f'gh saiu com código {r.returncode}', permission=permission)
    return json.loads(out) if out.strip() else None


def fail(message, code):
    print(f'ERRO: {message}', file=sys.stderr)
    return code


def get_all(path):
    items, page = [], 1
    while True:
        sep = '&' if '?' in path else '?'
        chunk = gh([f'{path}{sep}per_page=100&page={page}'])
        items += chunk
        if len(chunk) < 100:
            return items
        page += 1


def norm_color(c):
    return (c or '').lstrip('#').lower()


def plan_labels(existing):
    by_name = {l['name'].lower(): l for l in existing}
    rows = []
    for name, color, desc in LABELS:
        cur = by_name.get(name.lower())
        if cur is None:
            rows.append(('criar', name, [f'cor #{color}', f'descrição "{desc}"'], None))
            continue
        diffs = []
        if cur['name'] != name:
            diffs.append(f'nome "{cur["name"]}" -> "{name}"')
        if norm_color(cur.get('color')) != color:
            diffs.append(f'cor #{norm_color(cur.get("color"))} -> #{color}')
        if (cur.get('description') or '') != desc:
            diffs.append(f'descrição "{cur.get("description") or ""}" -> "{desc}"')
        rows.append(('atualizar' if diffs else 'ignorar', name, diffs, cur))
    return rows


def plan_milestones(existing):
    by_title = {m['title']: m for m in existing}
    rows = []
    for title, desc in MILESTONES:
        cur = by_title.get(title)
        if cur is None:
            rows.append(('criar', title, [f'descrição "{desc}"', 'sem data de entrega'], None))
            continue
        diffs = []
        if (cur.get('description') or '') != desc:
            diffs.append(f'descrição "{cur.get("description") or ""}" -> "{desc}"')
        rows.append(('atualizar' if diffs else 'ignorar', title, diffs, cur))
    return rows


def show(title, rows, extras):
    print(f'\n== {title} ==')
    for action, name, diffs, _ in rows:
        mark = {'criar': '+', 'atualizar': '~', 'ignorar': '='}[action]
        print(f'  {mark} {action:<9} {name}')
        for d in diffs:
            print(f'      {d}')
    counts = {a: sum(1 for r in rows if r[0] == a) for a in ('criar', 'atualizar', 'ignorar')}
    print(f'  -> criar {counts["criar"]}, atualizar {counts["atualizar"]}, ignorar {counts["ignorar"]}'
          f' (existentes fora da lista, intocados: {extras})')
    return counts


def apply_labels(repo, rows):
    for action, name, _, cur in rows:
        wanted = next(l for l in LABELS if l[0] == name)
        _, color, desc = wanted
        if action == 'criar':
            gh([f'repos/{repo}/labels', '-X', 'POST'], {'name': name, 'color': color, 'description': desc})
        elif action == 'atualizar':
            gh([f'repos/{repo}/labels/{quote(cur["name"], safe="")}', '-X', 'PATCH'],
               {'new_name': name, 'color': color, 'description': desc})
        else:
            continue
        print(f'  aplicado: {action} label {name}')


def apply_milestones(repo, rows):
    for action, title, _, cur in rows:
        desc = next(m[1] for m in MILESTONES if m[0] == title)
        if action == 'criar':
            gh([f'repos/{repo}/milestones', '-X', 'POST'], {'title': title, 'description': desc})
        elif action == 'atualizar':
            gh([f'repos/{repo}/milestones/{cur["number"]}', '-X', 'PATCH'], {'description': desc})
        else:
            continue
        print(f'  aplicado: {action} milestone {title}')


def check_permission(repo):
    info = gh([f'repos/{repo}'])
    perms = info.get('permissions') or {}
    if not any(perms.get(p) for p in WRITE_PERMISSIONS):
        raise GhError(f'sem permissão de escrita/triagem em {repo} (permissões: {perms or "nenhuma informada"})',
                      permission=True)


def run(repo, apply):
    for name, _, desc in LABELS:
        if len(desc) > MAX_LABEL_DESC:
            raise SystemExit(fail(f'descrição do label {name} passa de {MAX_LABEL_DESC} caracteres', EXIT_ERROR))
    print(f'Repositório: {repo}')
    print(f'Modo: {"APLICAR" if apply else "ENSAIO (somente leitura; use --apply para executar)"}')
    check_permission(repo)
    labels = get_all(f'repos/{repo}/labels')
    milestones = get_all(f'repos/{repo}/milestones?state=all')
    lrows, mrows = plan_labels(labels), plan_milestones(milestones)
    lc = show('Labels', lrows, len(labels) - sum(1 for r in lrows if r[3] is not None))
    mc = show('Milestones', mrows, len(milestones) - sum(1 for r in mrows if r[3] is not None))
    changes = lc['criar'] + lc['atualizar'] + mc['criar'] + mc['atualizar']
    print(f'\nTotal de mudanças: {changes}')
    if not apply:
        print('Ensaio: nada foi alterado.')
        return
    if changes == 0:
        print('Nada a aplicar.')
        return
    print('\n== Aplicando ==')
    apply_labels(repo, lrows)
    apply_milestones(repo, mrows)
    print('Concluído. Rode o ensaio de novo: deve mostrar 0 mudanças.')


def main():
    for s in (sys.stdout, sys.stderr):
        s.reconfigure(encoding='utf-8')
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--repo', default=DEFAULT_REPO, help=f'ORG/REPO (padrão: {DEFAULT_REPO})')
    ap.add_argument('--apply', action='store_true', help='executa as mudanças (padrão: ensaio)')
    args = ap.parse_args()
    try:
        run(args.repo, args.apply)
    except GhError as e:
        if e.permission:
            return fail(f'permissão negada ou repositório inacessível: {e}', EXIT_NO_PERMISSION)
        return fail(str(e), EXIT_ERROR)
    except json.JSONDecodeError as e:
        return fail(f'resposta inválida da API: {e}', EXIT_ERROR)
    return 0


if __name__ == '__main__':
    sys.exit(main())
