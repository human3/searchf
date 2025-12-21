PIP=$(VENV_DIR)/bin/pip
VENV_DIR=.venv
PY=$(VENV_DIR)/bin/python
RUN_PY_MOD=TERM='screen-256color' $(PY) -m
RUN_SEARCHF=$(RUN_PY_MOD) searchf.main
GENERATE_REPORT=$(PY) -m coverage report -m

FILE=README.md

$(VENV_DIR):
	python3 -m venv $(VENV_DIR)
	# Install python packages in venv
	$(PIP) install build pytest pytest-cov flake8 pyyaml

env: $(VENV_DIR)

run: env
	$(RUN_SEARCHF) $(FILE)

runc: env
	$(RUN_SEARCHF) searchf/test/sample_with_colors.txt

runi: env
	$(RUN_SEARCHF) searchf/test/sample_international.txt

runb: env
	$(RUN_SEARCHF) --debug searchf/test/sample_bug.txt

runr: env
	$(RUN_SEARCHF) searchf/test/rulers.txt

debug: env
	$(RUN_SEARCHF) --debug $(FILE)

debug+: env
	$(RUN_SEARCHF) --debug --show-events $(FILE)

tests: env
	$(RUN_PY_MOD) pytest searchf
	$(RUN_PY_MOD) searchf.test.all

cover-all: env
	$(RUN_PY_MOD) coverage run -m searchf.test.all
	$(GENERATE_REPORT)

cover-unit: env
	$(RUN_PY_MOD) coverage run -m pytest searchf
	$(GENERATE_REPORT)

test-color: env
	$(RUN_PY_MOD) searchf.test.color

profile: env
	$(RUN_PY_MOD) cProfile -s cumtime -m searchf.test.all

type:
	mypy searchf

lint:
	pylint searchf
	$(RUN_PY_MOD) flake8 searchf

checks: type lint

# sudo-xxx targets must be invoked with sudo (eg "sudo make sudo-deps"...)
sudo-deps:
	apt-get -y install python3 python3-venv mypy pylint

sudo-deps-clean:
	apt-get purge python3 python3-venv pip pylint

deps-clean:
	rm -Rf $(VENV_DIR)

# Build package locally
build:
	$(PY) -m build

# Install package in local venv
install: build
	$(PY) -m pip install dist/searchf-*.tar.gz

clean:
	$(PIP) uninstall -y searchf
	find -type f -name "*~" -print -delete
	rm -Rf dist

cover: cover-all

all: type lint cover-all
