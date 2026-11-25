#!/usr/bin/env python3
"""Verifica as dependências internas dos crates do core contra docs/architecture/crates.toml (P-01).

Para cada Cargo.toml de crate em core/:
  - o crate precisa estar registrado em crates.toml;
  - toda dependência interna (nome registrado, ou dependência por `path`) precisa ser uma aresta
    permitida (`deps` do crate); vale para [dependencies], [dev-dependencies], [build-dependencies]
    e para as tabelas por alvo ([target.*.dependencies]);
  - nenhuma dependência pode ser de UI, backend ou nuvem (lista abaixo; P-01).
Sem core/Cargo.toml, imprime "sem código ainda" e sai com 0.

Uso: python3 tools/sdd/check_crate_deps.py [--root DIR]
Requer Python 3.11+ (tomllib). Saída: 0 ok; 1 violações.
"""
import pathlib
import sys
import tomllib

DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]
DEP_TABLES = ('dependencies', 'dev-dependencies', 'build-dependencies')
# P-01: o core nunca importa UI, backend nem provedor de nuvem.
FORBIDDEN_PREFIXES = ('flutter', 'react', 'spring', 'postgres', 'tokio-postgres', 'aws-', 'aws_', 'rusoto',
                      'google-cloud', 'gcloud', 'azure-', 'azure_')


def load_registry(root):
    data = tomllib.loads((root / 'docs/architecture/crates.toml').read_text(encoding='utf-8'))
    return {name: list(v.get('deps', [])) for name, v in data.items() if isinstance(v, dict)}


def manifests(core):
    return sorted(p for p in core.rglob('Cargo.toml') if 'target' not in p.relative_to(core).parts)


def dep_entries(doc):
    """[(chave, especificação)] de todas as tabelas de dependência, inclusive por alvo."""
    out = []
    for t in DEP_TABLES:
        out += list((doc.get(t) or {}).items())
    for tgt in (doc.get('target') or {}).values():
        for t in DEP_TABLES:
            out += list((tgt.get(t) or {}).items())
    return out


def check(root):
    root = pathlib.Path(root)
    core = root / 'core'
    if not (core / 'Cargo.toml').exists():
        return None, []
    reg = load_registry(root)
    errors = []
    for crate, deps in reg.items():
        for d in deps:
            if d not in reg:
                errors.append(f'crates.toml: {crate} permite {d}, que não está registrado')
    for mf in manifests(core):
        rel = mf.relative_to(root).as_posix()
        try:
            doc = tomllib.loads(mf.read_text(encoding='utf-8'))
        except tomllib.TOMLDecodeError as e:
            errors.append(f'{rel}: TOML inválido ({e})')
            continue
        pkg = (doc.get('package') or {}).get('name')
        if not pkg:  # manifesto de workspace
            continue
        if pkg not in reg:
            errors.append(f'{rel}: crate "{pkg}" não está registrado em docs/architecture/crates.toml')
            continue
        for key, spec in dep_entries(doc):
            real = spec.get('package', key) if isinstance(spec, dict) else key
            has_path = isinstance(spec, dict) and 'path' in spec
            if any(real.lower().startswith(p) for p in FORBIDDEN_PREFIXES):
                errors.append(f'{rel}: dependência "{real}" viola P-01 (o core não depende de UI, backend nem nuvem)')
            if real in reg or has_path:
                if real not in reg:
                    errors.append(f'{rel}: dependência por path "{real}" fora do registro de crates')
                elif real != pkg and real not in reg[pkg]:
                    errors.append(f'{rel}: aresta não permitida {pkg} -> {real} (permitidas: {", ".join(reg[pkg]) or "nenhuma"})')
    return reg, errors


def main(argv):
    root = pathlib.Path(argv[argv.index('--root') + 1]) if '--root' in argv else DEFAULT_ROOT
    reg, errors = check(root)
    if reg is None:
        print('sem código ainda: core/Cargo.toml não existe; nada a verificar.')
        return 0
    for e in errors:
        print('ERRO   ', e)
    print(f'check-crate-deps: {len(errors)} violação(ões) em {len(manifests(root / "core"))} manifesto(s)')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
