# Alvos de documentação/especificação. Requer apenas Python 3.
.PHONY: verify docs check strict test-tools new-spec new-entry lint-workflows

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

new-entry:                  ## cria a entrada do diário de hoje: make new-entry (opcional: D=AAAA-MM-DD U=usuario-github)
	python3 tools/sdd/new_entry.py $(if $(D),--date $(D)) $(if $(U),--user $(U))

lint-workflows:             ## valida os workflows com o actionlint (instale: winget install rhysd.actionlint | brew install actionlint)
	actionlint
