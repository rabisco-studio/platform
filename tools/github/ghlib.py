"""Funções comuns dos scripts de automação. Somente biblioteca padrão do Python 3."""
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools' / 'sdd'))

REPO_DEFAULT = 'rabisco-studio/platform'


def say(level, msg):
    """Imprime no formato de anotação do GitHub Actions (aparece como aviso/erro no PR)."""
    print(f'::{level}::{msg}')
    sys.stdout.flush()


def warn(msg):
    say('warning', msg)


def git(args, cwd=None, check=True):
    r = subprocess.run(['git', *args], cwd=str(cwd or ROOT), capture_output=True, text=True, encoding='utf-8')
    if check and r.returncode != 0:
        raise RuntimeError(f'git {" ".join(args)} falhou: {r.stderr.strip()}')
    return r.stdout


def gh(args, payload=None, token=None):
    """Executa `gh ...`. Devolve (código, stdout, stderr). Nunca lança por falha do gh."""
    env = dict(os.environ)
    if token:
        env['GH_TOKEN'] = token
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    cmd = ['gh', *args] + (['--input', '-'] if data is not None else [])
    try:
        r = subprocess.run(cmd, input=data, capture_output=True, env=env)
    except FileNotFoundError:
        return 127, '', 'gh não encontrado'
    return r.returncode, r.stdout.decode('utf-8', 'replace'), r.stderr.decode('utf-8', 'replace')


def gh_json(args, token=None):
    code, out, err = gh(args, token=token)
    if code != 0:
        raise RuntimeError((err or out).strip() or f'gh saiu com código {code}')
    return json.loads(out) if out.strip() else None


def spec_id_from_dir(name):
    """'001-scene-graph' -> 'SPEC-001'."""
    return 'SPEC-' + name.split('-', 1)[0]


def step_summary(text):
    path = os.environ.get('GITHUB_STEP_SUMMARY')
    if path:
        with open(path, 'a', encoding='utf-8') as f:
            f.write(text + '\n')
