# Alvos de documentação/especificação. Requer apenas Python 3.
.PHONY: verify docs check strict

verify: docs check          ## regenera derivados e valida (usar antes de pedir revisão)

docs:                       ## regenera arquivos gerados
	python3 tools/sdd/generate.py

check:                      ## valida; erros falham, avisos não
	python3 tools/sdd/sdd_check.py

strict:                     ## linha de base de release: avisos também falham
	python3 tools/sdd/sdd_check.py --strict
