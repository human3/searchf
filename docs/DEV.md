# Development

![Latest Version](https://img.shields.io/pypi/v/searchf)
![Publish badge](https://github.com/human3/searchf/actions/workflows/python-publish.yml/badge.svg)
![Package badge](https://github.com/human3/searchf/actions/workflows/python-package.yml/badge.svg)
![Pylint badge](https://github.com/human3/searchf/actions/workflows/pylint.yml/badge.svg)

The code in this project tries to abide by the following principles:

- Simplicity comes first
- Don't Repeat Yourself
- no-use-before-define

## Dependencies

First, you will need to pick a computer with a keyboard and some OS on it... The next steps will vary depending on that. So, assuming a fresh debian-based machine, here are the steps I usually perform:
- `sudo apt-get install git make`
- `git clone git@github.com:human3/searchf.git`

Then, run
- `cd searchf`
- `sudo make sudo_deps`

## How to run the application?

To launch the application with a default sample file, use:

`make run`

To launch application with another file:

`python3 -m searchf.main <FILE>`

To launch in debug mode:

`make debug`

Debug mode will change UI layout to make room for a few print statements emitted by the application at runtime.

Notes:
- please explore the `Makefile` to discover more ways to run
- all the above steps describe how to run the application while working on it... This is different from how end-user run it as `searchf` is packaged and installed on their system using `pip` or `pipx`.

## How to run test?

- `make tests`
- `python3 -m searchf.test.color` shows current palettes definition, and bridges gaps in colors unit tests which do not evaluate side-effects

All the test commands I use can found in the `Makefile`.

## How to build the package from sources

The following `Makefile` targets can help with this:
- `make build` to build the package
- `make install` to install package on your system

Then, you should be able to use `searchf` on your system as if you had downloaded from `pypi.org` and installed it through regular `pip` or `pipx`.

To uninstall: `pip uninstall -y searchf`

WARNING: the instructions in the Makefile might need to be adapted according to platform.

## Testing with older python version

https://bgasparotto.com/install-pyenv-ubuntu-debian

## What about coverage?

The numbers below are as of version `1.24`.

### Unit tests

```
Name                            Stmts   Miss  Cover
---------------------------------------------------
searchf/__init__.py                 2      0   100%
searchf/colors.py                  54      0   100%
searchf/enums.py                   96      0   100%
searchf/keys.py                   111      8    93%
searchf/models.py                 270      0   100%
searchf/segments.py               113      0   100%
searchf/sgr.py                     69      0   100%
searchf/storage.py                 62      0   100%
searchf/test/__init__.py            0      0   100%
searchf/test/test_colors.py        36      5    86%
searchf/test/test_enums.py         19      0   100%
searchf/test/test_keys.py          46      0   100%
searchf/test/test_models.py       145      0   100%
searchf/test/test_segments.py     112      0   100%
searchf/test/test_sgr.py           43      0   100%
searchf/test/test_storage.py       22      0   100%
searchf/types.py                   20      4    80%
---------------------------------------------------
TOTAL                            1220     17    99%
```

Run `make cover-unit` for updated numbers.

### Application tests

```
Name                            Stmts   Miss  Cover
---------------------------------------------------
searchf/__init__.py                 2      0   100%
searchf/app.py                    221      1    99%
searchf/colors.py                  54      1    98%
searchf/debug.py                    5      0   100%
searchf/enums.py                   96      0   100%
searchf/keys.py                   111      3    97%
searchf/main.py                    81      0   100%
searchf/models.py                 270      0   100%
searchf/segments.py               113      0   100%
searchf/sgr.py                     69      0   100%
searchf/storage.py                 62      0   100%
searchf/test/__init__.py            0      0   100%
searchf/test/all.py               219      0   100%
searchf/test/test_enums.py         19      0   100%
searchf/test/test_keys.py          46      0   100%
searchf/test/test_models.py       145      0   100%
searchf/test/test_segments.py     112      0   100%
searchf/test/test_sgr.py           43      0   100%
searchf/test/test_storage.py       22      0   100%
searchf/types.py                   20      0   100%
searchf/utils.py                   21      0   100%
searchf/views.py                  411      0   100%
---------------------------------------------------
TOTAL                            2142      5    99%
```

Run `make cover-all` for updated numbers.
