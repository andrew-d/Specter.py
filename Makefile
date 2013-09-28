.PHONY: test doc clean

test:
	@nosetests specter --with-coverage --cover-package=specter

check:
	@flake8 specter

doc:
	@cd docs; make html

clean:
	@cd docs; make clean
