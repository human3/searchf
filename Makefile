run:
	python3 -m searchf.app README.md

tests:
	TERM='screen-256color' pytest
	TERM='screen-256color' python3 -m searchf.test.all

cover:
	TERM='screen-256color' coverage run -m searchf.test.all
	coverage report -m

lint:
	pylint searchf

all: lint tests cover
