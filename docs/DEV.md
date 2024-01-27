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
- `sudo apt-get install make git python3`
- `sudo apt-get install emacs tmux ripgrep` (these are my personal editor and env choices...)
- `make -p ~/repos/searchf`
- `cd ~/repos/searchf`
- `git clone git@github.com:human3/searchf.git`

Then, run
- `sudo make sudo_deps`
- `make deps`

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
- all the above steps describe how to run the application while working on it... This is different from how end-user run it as `searchf` is packaged and installed on their system using `pip`.

## How to run test?

- `make tests`
- `python3 -m searchf.test.color` shows current palettes definition, and bridges gaps in colors unit tests which do not evaluate side-effects

All the test commands I use can found in the `Makefile`.

## How to build the package from sources

The following `Makefile` targets can help with this:
- `make build` to build the package
- `make install` to install package on your system

Then, you should be able to use `searchf` on your system as if you had downloaded from `pypi.org` and installed it through regular `pip`.

To uninstall: `pip uninstall -y searchf`

WARNING: the instructions in the Makefile might need to be adapted according to platform.

## What about coverage?

The numbers below are as of version `1.14`.

### Unit tests

```
Name                            Stmts   Miss  Cover
---------------------------------------------------
searchf/__init__.py                 1      0   100%
searchf/colors.py                  30      0   100%
searchf/enums.py                   86      0   100%
searchf/keys.py                    92      2    98%
searchf/models.py                 227      1    99%
searchf/segments.py                57      0   100%
searchf/storage.py                 62      0   100%
searchf/test/__init__.py            0      0   100%
searchf/test/test_colors.py        32      4    88%
searchf/test/test_enums.py         19      0   100%
searchf/test/test_keys.py          44      0   100%
searchf/test/test_models.py       111      0   100%
searchf/test/test_segments.py      51      0   100%
searchf/test/test_storage.py       22      0   100%
searchf/types.py                   17      4    76%
---------------------------------------------------
TOTAL                             851     11    99%
```

Run `make cover_unit` for updated numbers.

### Application tests

```
Name                            Stmts   Miss  Cover
---------------------------------------------------
searchf/__init__.py                 1      0   100%
searchf/app.py                    208      1    99%
searchf/colors.py                  30      0   100%
searchf/debug.py                    5      0   100%
searchf/enums.py                   86      0   100%
searchf/keys.py                    92      0   100%
searchf/main.py                    74      0   100%
searchf/models.py                 227      0   100%
searchf/segments.py                57      0   100%
searchf/storage.py                 62      0   100%
searchf/test/__init__.py            0      0   100%
searchf/test/all.py               194      0   100%
searchf/test/test_enums.py         19      0   100%
searchf/test/test_keys.py          44      0   100%
searchf/test/test_models.py       111      0   100%
searchf/test/test_segments.py      51      0   100%
searchf/test/test_storage.py       22      0   100%
searchf/types.py                   17      0   100%
searchf/utils.py                   21      0   100%
searchf/views.py                  396      0   100%
-------------------------------------------------------------
TOTAL                            1717      1    99%
```

Run `make cover_all` for updated numbers.
