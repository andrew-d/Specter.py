.PHONY: test watch_test check doc clean

# Can specify parallelism on command line.
PARALLELISM ?= 0
ifneq (0,${PARALLELISM})
	PARALLEL_ARGS := -n ${PARALLELISM}
else
	PARALLEL_ARGS :=
endif

# Arguments for py.test
PYTEST_ARGS := --cov specter --cov-report term-missing --timeout=90 ${PARALLEL_ARGS}

# ----------------------------------------------------------------------
# ------------------------------ Commands ------------------------------
# ----------------------------------------------------------------------

test:
	@py.test ${PYTEST_ARGS} specter

watch_test:
	@py.test -f ${PYTEST_ARGS} specter

check:
	@flake8 specter

doc:
	@cd docs; make html

clean:
	@cd docs; make clean
	@rm .coverage
