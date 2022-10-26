run:
	python3 -m searchf.app README.md

tests:
	TERM='screen-256color' python3 -m pytest
	TERM='screen-256color' python3 -m searchf.test.all

cover:
	TERM='screen-256color' python3 -m coverage run -m searchf.test.all
	python3 -m coverage report -m

type:
	mypy searchf

lint:
	pylint searchf

# deps target requires sudo
deps:
	apt install mypy pylint python3-venv
	python3 -m pip install build

# Build package locally
build:
	python3 -m build

install: build
	python3 -m pip install dist/searchf-*.tar.gz

clean:
	pip uninstall -y searchf

all: type lint tests cover
