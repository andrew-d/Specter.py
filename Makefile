.PHONY: test doc clean

test:
	@nosetests specter --with-coverage --cover-package=specter

doc:
	@cd docs; make html

clean:
	@cd docs; make clean
