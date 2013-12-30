.PHONY: pep8 pyflakes lint test

test:
	trial --rterrors test_*.py

lint: pep8 pyflakes

pep8:
	pep8 *.py

pyflakes:
	pyflakes *.py
