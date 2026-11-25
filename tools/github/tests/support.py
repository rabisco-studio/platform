"""Caminhos e utilitários comuns dos testes (só biblioteca padrão)."""
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for p in (ROOT / 'tools' / 'github', ROOT / 'tools' / 'sdd'):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


class TmpRepo:
    """Repositório git temporário com autores controlados."""

    def __init__(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self._tmp.name)
        self.git('init', '-q', '-b', 'main')

    def git(self, *args, author=None):
        env = dict(os.environ)
        if author:
            name, email = author
            env.update(GIT_AUTHOR_NAME=name, GIT_AUTHOR_EMAIL=email, GIT_COMMITTER_NAME=name, GIT_COMMITTER_EMAIL=email)
        else:
            env.update(GIT_AUTHOR_NAME='T', GIT_AUTHOR_EMAIL='t@example.com', GIT_COMMITTER_NAME='T',
                       GIT_COMMITTER_EMAIL='t@example.com')
        r = subprocess.run(['git', *args], cwd=str(self.path), capture_output=True, text=True, env=env, encoding='utf-8')
        assert r.returncode == 0, r.stderr
        return r.stdout.strip()

    def write(self, rel, text):
        p = self.path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8', newline='\n')

    def commit(self, msg, author=None):
        self.git('add', '-A')
        self.git('commit', '-q', '-m', msg, author=author)
        return self.git('rev-parse', 'HEAD')

    def cleanup(self):
        self._tmp.cleanup()
