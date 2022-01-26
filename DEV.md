# Development

![Latest Version](https://img.shields.io/pypi/v/searchf)
![Publish badge](https://github.com/human3/searchf/actions/workflows/python-publish.yml/badge.svg)
![Package badge](https://github.com/human3/searchf/actions/workflows/python-package.yml/badge.svg)
![Pylint badge](https://github.com/human3/searchf/actions/workflows/pylint.yml/badge.svg)

The code in this project tries to abide by the following principles:

- Simplicity comes first
- Don't Repeat Yourself
- no-use-before-define

## How to run the application?

If working from the sources (ie not an installed package), the application can be launched as a module:

`python3 -m searchf.app <FILE>`

## How to run test?

- First install dependencies with `pip install pytest pytest-cov` (once)
- Then just type `pytest` to run the unit tests
- `python3 -m searchf.test.all` runs the application tests
- `python3 -m searchf.test.color` shows current palettes definition, and bridges gaps in colors unit tests which do not evaluate side-effects

## What about coverage?

The numbers below are as of version `1.5`.

Unit tests don't cover much as `pytest --cov=searchf` returns:

```
Name                            Stmts   Miss  Cover
---------------------------------------------------
searchf/__init__.py                 1      0   100%
searchf/app.py                    554    554     0%
searchf/colors.py                  29      0   100%
searchf/models.py                 134      2    99%
searchf/segments.py                48      0   100%
searchf/test/__init__.py            0      0   100%
searchf/test/all.py               144    144     0%
searchf/test/color.py              48     48     0%
searchf/test/test_colors.py        32      4    88%
searchf/test/test_models.py        62      0   100%
searchf/test/test_segments.py      50      0   100%
---------------------------------------------------
TOTAL                            1102    752    32%
```

Application tests coverage is better at 99%. Indeed, running
- `coverage run -m searchf.test.all` then
- `coverage report`

shows:

```
Name                            Stmts   Miss  Cover
---------------------------------------------------
searchf/__init__.py                 1      0   100%
searchf/app.py                    554     10    98%
searchf/colors.py                  29      0   100%
searchf/models.py                 134      0   100%
searchf/segments.py                48      0   100%
searchf/test/__init__.py            0      0   100%
searchf/test/all.py               144      5    97%
searchf/test/test_models.py        62      0   100%
searchf/test/test_segments.py      50      0   100%
---------------------------------------------------
TOTAL                            1022     15    99%
```

## How to build the package from sources

WARNING: instructions below must be adapted according to platform

First install build dependencies (once) with something like

`python -m pip install build`

Then:

- Go to root of project
- `python -m build`
- Then, you can install with `python -m install dist/searchf-1.5-py3-none-any.whl`
