"""Caminhos e utilitários comuns dos testes de tools/sdd (só biblioteca padrão)."""
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if str(ROOT / 'tools' / 'sdd') not in sys.path:
    sys.path.insert(0, str(ROOT / 'tools' / 'sdd'))


def copy_repo():
    """Cópia do repositório (sem .git) em diretório temporário. Devolve (TemporaryDirectory, Path)."""
    tmp = tempfile.TemporaryDirectory()
    dst = pathlib.Path(tmp.name) / 'repo'
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns('.git', '__pycache__', '_site'))
    return tmp, dst


def write(root, rel, text):
    p = pathlib.Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8', newline='\n')
