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

- First install dependencies with `make deps` (once)
- Then run `make tests`

Provided that your terminal as the appropriate color settings
(eg TERM=screen-256color), you can also use:

- `pytest` to run the unit tests
- `python3 -m searchf.test.all` runs the application tests
- `python3 -m searchf.test.color` shows current palettes definition, and bridges gaps in colors unit tests which do not evaluate side-effects

## What about coverage?

The numbers below are as of version `1.13`.

### Unit tests

```
Name                            Stmts   Miss  Cover
---------------------------------------------------
searchf/__init__.py                 1      0   100%
searchf/colors.py                  30      0   100%
searchf/enums.py                   85      0   100%
searchf/keys.py                    78      3    96%
searchf/models.py                 227      1    99%
searchf/segments.py                57      0   100%
searchf/storage.py                 62      0   100%
searchf/test/__init__.py            0      0   100%
searchf/test/test_colors.py        32      4    88%
searchf/test/test_enums.py         19      0   100%
searchf/test/test_keys.py          31      0   100%
searchf/test/test_models.py       111      0   100%
searchf/test/test_segments.py      51      0   100%
searchf/test/test_storage.py       22      0   100%
searchf/types.py                   17      4    76%
---------------------------------------------------
TOTAL                             823     12    99%
```

Run `make cover_unit` for updated numbers.

### Application tests

```
Name                            Stmts   Miss  Cover
---------------------------------------------------
searchf/__init__.py                 1      0   100%
searchf/app.py                    205      1    99%
searchf/colors.py                  30      0   100%
searchf/debug.py                    5      0   100%
searchf/enums.py                   85      0   100%
searchf/keys.py                    78      0   100%
searchf/main.py                    73      0   100%
searchf/models.py                 227      0   100%
searchf/segments.py                57      0   100%
searchf/storage.py                 62      0   100%
searchf/test/__init__.py            0      0   100%
searchf/test/all.py               194      0   100%
searchf/test/test_enums.py         19      0   100%
searchf/test/test_keys.py          31      0   100%
searchf/test/test_models.py       111      0   100%
searchf/test/test_segments.py      51      0   100%
searchf/test/test_storage.py       22      0   100%
searchf/types.py                   17      0   100%
searchf/utils.py                   21      0   100%
searchf/views.py                  396      0   100%
---------------------------------------------------
TOTAL                            1685      1    99%
```

Run `make cover_all` for updated numbers.

## How to build the package from sources

WARNING: instructions below must be adapted according to platform

First install build dependencies (once) with something like

`python3 -m pip install build`

Then:

- Go to root of project
- `python3 -m build`
- Then, you can install with `python3 -m pip install dist/searchf-*.tar.gz`
