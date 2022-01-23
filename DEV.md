# Development

## How to run the application?

If working from the sources (ie not an installed package), the application can be launched as a module:

`python3 -m searchf.app <FILE>`

## How to run test?

- `pytest` runs unit test
- `python3 -m searchf.test.all` runs the application tests

## What about coverage?

Note: numbers below are as of version `1.4.2`.

Unit tests don't cover much as `pytest --cov=searchf` returns:

```
Name                            Stmts   Miss  Cover
---------------------------------------------------
searchf/__init__.py                 1      0   100%
searchf/app.py                    586    586     0%
searchf/models.py                 131      5    96%
searchf/segments.py                46      0   100%
searchf/test/__init__.py            0      0   100%
searchf/test/all.py               136    136     0%
searchf/test/color.py              48     48     0%
searchf/test/test_models.py        56      0   100%
searchf/test/test_segments.py      47      0   100%
---------------------------------------------------
TOTAL                            1051    775    26%
```

Application tests coverage is better at 99%. Indeed, running
- `coverage run -m searchf.test.all` then
- `coverage report`

shows:

```
Name                            Stmts   Miss  Cover
---------------------------------------------------
searchf/__init__.py                 1      0   100%
searchf/app.py                    586     10    98%
searchf/models.py                 131      0   100%
searchf/segments.py                46      0   100%
searchf/test/__init__.py            0      0   100%
searchf/test/all.py               136      5    96%
searchf/test/test_models.py        56      0   100%
searchf/test/test_segments.py      47      0   100%
---------------------------------------------------
TOTAL                            1003     15    99%
```

## How to build and test searchf package from sources

WARNING: instructions below must be adapted according to platform

First install build dependencies (once) with something like

`python -m pip install build`

Then:

- Go to root of project
- `python -m build`
- `python -m install dist/searchf-1.4.2-py3-none-any.whl`
