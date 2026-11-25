# Alvos de documentação/especificação. Requer apenas Python 3.
.PHONY: verify docs check strict test-tools new-spec

verify: docs check test-tools   ## regenera derivados, valida e testa os scripts (usar antes de pedir revisão)

docs:                       ## regenera arquivos gerados
	python3 tools/sdd/generate.py

check:                      ## valida; erros falham, avisos não
	python3 tools/sdd/sdd_check.py

strict:                     ## linha de base de release: avisos também falham
	python3 tools/sdd/sdd_check.py --strict

test-tools:                 ## testes dos scripts de automação (tools/github/tests e tools/sdd/tests)
	python3 -m unittest discover -s tools/github/tests -v
	python3 -m unittest discover -s tools/sdd/tests -v

new-spec:                   ## cria a pasta de uma spec planejada: make new-spec N=018
	python3 tools/sdd/new_spec.py $(N)
