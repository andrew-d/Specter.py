.PHONY: test doc clean

test:
	@nosetests specter

doc:
	@cd docs; make html

clean:
	@cd docs; make clean
