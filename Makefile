RUN_PY_MOD=TERM='screen-256color' python3 -m
GENERATE_REPORT=python3 -m coverage report -m

run:
	$(RUN_PY_MOD) searchf.main README.md

tests:
	$(RUN_PY_MOD) pytest
	$(RUN_PY_MOD) searchf.test.all

cover_all:
	$(RUN_PY_MOD) coverage run -m searchf.test.all
	$(GENERATE_REPORT)

cover_unit:
	$(RUN_PY_MOD) coverage run -m pytest
	$(GENERATE_REPORT)

test_color:
	$(RUN_PY_MOD) searchf.test.color

type:
	mypy searchf

lint:
	pylint searchf
	flake8

# deps target requires sudo
deps:
	apt install mypy pylint python3-venv
	python3 -m pip install build pytest pytest-cov flake8

# Build package locally
build:
	python3 -m build

install: build
	python3 -m pip install dist/searchf-*.tar.gz

clean:
	pip uninstall -y searchf
	find -type f -name "*~" -print -delete

cover: cover_all

all: type lint cover_all
