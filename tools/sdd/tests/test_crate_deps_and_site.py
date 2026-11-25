import contextlib
import io
import pathlib
import tempfile
import unittest

import support
import build_site as B
import check_crate_deps as C

CRATES = '''[core-domain]
deps = []

[scene-engine]
deps = ["core-domain"]

[raster-engine]
deps = ["core-domain", "scene-engine"]
'''


def make_root(manifests):
    tmp = tempfile.TemporaryDirectory()
    root = pathlib.Path(tmp.name)
    support.write(root, 'docs/architecture/crates.toml', CRATES)
    support.write(root, 'core/Cargo.toml', '[workspace]\nmembers = ["*"]\n')
    for name, text in manifests.items():
        support.write(root, f'core/{name}/Cargo.toml', text)
    return tmp, root


def manifest(name, deps='', table='dependencies'):
    return f'[package]\nname = "{name}"\nversion = "0.1.0"\n\n[{table}]\n{deps}'


class CrateDepsTests(unittest.TestCase):
    def check(self, manifests):
        tmp, root = make_root(manifests)
        self.addCleanup(tmp.cleanup)
        return C.check(root)[1]

    def test_allowed_edges_pass(self):
        errs = self.check({'core-domain': manifest('core-domain', 'serde = "1"\n'),
                           'scene-engine': manifest('scene-engine', 'core-domain = { path = "../core-domain" }\n'),
                           'raster-engine': manifest('raster-engine', 'scene-engine = { path = "../scene-engine" }\ncore-domain.workspace = true\n')})
        self.assertEqual(errs, [])

    def test_forbidden_edge(self):
        errs = self.check({'core-domain': manifest('core-domain', 'scene-engine = { path = "../scene-engine" }\n'),
                           'scene-engine': manifest('scene-engine')})
        self.assertEqual(len(errs), 1)
        self.assertIn('aresta não permitida core-domain -> scene-engine', errs[0])

    def test_dev_dependency_and_target_tables_count(self):
        errs = self.check({'core-domain': manifest('core-domain', 'raster-engine = { path = "../raster-engine" }\n', 'dev-dependencies'),
                           'scene-engine': manifest('scene-engine') + '\n[target.\'cfg(unix)\'.dependencies]\nraster-engine = { path = "../raster-engine" }\n',
                           'raster-engine': manifest('raster-engine')})
        self.assertEqual(len(errs), 2, errs)

    def test_renamed_dependency_is_resolved(self):
        errs = self.check({'core-domain': manifest('core-domain', 'x = { package = "raster-engine", path = "../raster-engine" }\n'),
                           'raster-engine': manifest('raster-engine')})
        self.assertTrue(any('core-domain -> raster-engine' in e for e in errs), errs)

    def test_unregistered_crate_and_path_dep(self):
        errs = self.check({'mystery': manifest('mystery'),
                           'core-domain': manifest('core-domain', 'other = { path = "../other" }\n')})
        self.assertTrue(any('"mystery" não está registrado' in e for e in errs), errs)
        self.assertTrue(any('path "other" fora do registro' in e for e in errs), errs)

    def test_p01_forbidden_dependencies(self):
        errs = self.check({'core-domain': manifest('core-domain', 'flutter_rust_bridge = "2"\naws-sdk-s3 = "1"\nserde = "1"\n')})
        self.assertEqual(sum('viola P-01' in e for e in errs), 2, errs)

    def test_no_code_yet_exits_zero(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        support.write(tmp.name, 'docs/architecture/crates.toml', CRATES)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(C.main(['--root', tmp.name]), 0)
        self.assertIn('sem código ainda', buf.getvalue())

    def test_real_registry_is_consistent(self):
        reg = C.load_registry(support.ROOT)
        for crate, deps in reg.items():
            for d in deps:
                self.assertIn(d, reg, f'{crate} -> {d}')

    def test_exit_code_on_violation(self):
        tmp, root = make_root({'core-domain': manifest('core-domain', 'scene-engine = { path = "../s" }\n'),
                               'scene-engine': manifest('scene-engine')})
        self.addCleanup(tmp.cleanup)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(C.main(['--root', str(root)]), 1)


class SiteTests(unittest.TestCase):
    def test_real_repo_site(self):
        page = B.build(support.ROOT)
        for needle in ('Índice de specs', 'Cobertura por release', 'Decisões abertas', 'Riscos registrados', 'SPEC-001', 'DEC-', 'RSK-'):
            self.assertIn(needle, page)
        self.assertNotIn('<script', page)
        self.assertIn('https://github.com/rabisco-studio/platform/blob/main/.ai/sdd/specs/001-scene-graph/requirements.md', page)

    def test_html_is_escaped(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        support.write(tmp.name, '.ai/sdd/INDEX.md', '# Índice de especificações (SDD)\n\n| Spec | Título |\n|---|---|\n| SPEC-001 | <script>alert(1)</script> |\n')
        page = B.build(tmp.name)
        self.assertNotIn('<script>alert', page)
        self.assertIn('&lt;script&gt;', page)

    def test_main_writes_files(self):
        with tempfile.TemporaryDirectory() as out, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(B.main(['--out', out]), 0)
            self.assertTrue((pathlib.Path(out) / 'index.html').exists())
            self.assertTrue((pathlib.Path(out) / '.nojekyll').exists())


if __name__ == '__main__':
    unittest.main()
