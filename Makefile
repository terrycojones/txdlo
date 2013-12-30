.PHONY: pep8 pyflakes lint test

test:
	trial --rterrors test_txdlo.py

lint: pep8 pyflakes

pep8:
	pep8 *.py

pyflakes:
	pyflakes *.py

clean:
	rm -f *~ *.pyc
	rm -fr _trial_temp
