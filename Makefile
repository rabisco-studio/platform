# Alvos de documentação/especificação. Requer apenas Python 3.
.PHONY: verify docs check strict test-tools

verify: docs check test-tools   ## regenera derivados, valida e testa os scripts (usar antes de pedir revisão)

docs:                       ## regenera arquivos gerados
	python3 tools/sdd/generate.py

check:                      ## valida; erros falham, avisos não
	python3 tools/sdd/sdd_check.py

strict:                     ## linha de base de release: avisos também falham
	python3 tools/sdd/sdd_check.py --strict

test-tools:                 ## testes dos scripts de automação (tools/github/tests)
	python3 -m unittest discover -s tools/github/tests -v
