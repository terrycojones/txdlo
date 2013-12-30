.PHONY: pep8 pyflakes lint test
XARGS := xargs $(shell test $$(uname) = Linux && echo -r)

test:
	trial --rterrors txdlo

lint: pep8 pyflakes

pep8:
	find . -name '*.py' -print0 | $(XARGS) -0 pep8 --repeat

pyflakes:
	find . -name '*.py' -print0 | $(XARGS) -0 pyflakes

clean:
	find . -name '*.pyc' -o -name '*~' -print0 | $(XARGS) -0 rm
	rm -fr _trial_temp
