VENV_DIR=.venv
PY=$(VENV_DIR)/bin/python
PIP=$(VENV_DIR)/bin/pip
RUN_PY_MOD=TERM='screen-256color' $(PY) -m
GENERATE_REPORT=$(PY) -m coverage report -m

FILE=README.md
#FILE=searchf/test/rulers.txt

run:
	$(RUN_PY_MOD) searchf.main $(FILE)

runc:
	$(RUN_PY_MOD) searchf.main searchf/test/sample_with_colors.txt

debug:
	$(RUN_PY_MOD) searchf.main --debug $(FILE)

debug+:
	$(RUN_PY_MOD) searchf.main --debug --show-events $(FILE)

tests:
	$(RUN_PY_MOD) pytest searchf
	$(RUN_PY_MOD) searchf.test.all

cover_all:
	$(RUN_PY_MOD) coverage run -m searchf.test.all
	$(GENERATE_REPORT)

cover_unit:
	$(RUN_PY_MOD) coverage run -m pytest searchf
	$(GENERATE_REPORT)

test_color:
	$(RUN_PY_MOD) searchf.test.color

profile:
	$(RUN_PY_MOD) cProfile -s cumtime -m searchf.test.all

type:
	mypy searchf

lint:
	pylint searchf
	$(RUN_PY_MOD) flake8 searchf

checks: type lint

# sudo_deps target must be invoked with "sudo make sudo_deps"...
sudo-deps:
	apt-get -y install python3 python3-venv mypy pip pylint

sudo-deps-clean:
	apt-get purge python3 python3-venv pip pylint

$(VENV_DIR):
	python3 -m venv $(VENV_DIR)

deps: $(VENV_DIR)
	# Install python packages in venv
	$(PIP) install build pytest pytest-cov flake8

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

cover: cover_all

all: type lint cover_all
