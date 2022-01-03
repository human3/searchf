# [searchf](https://github.com/human3/searchf)

Utility program to interactively search and colorize keywords in text files, select relevant lines, remove noise and help you discover the things you should care about. Works in terminals and uses stack-based interactions to minimize the number of key presses (think HP calculators).

![Peek 2021-12-31 21-05](https://user-images.githubusercontent.com/15265841/147842653-46e2fc0f-fdac-424e-9e5a-2e806d86440e.gif)

The above screenshot shows how the content of a text file can be filtered. In this example, 3 filters have been defined and are displayed in the filter stack, at the bottom and right below the blue bar:
- `def AND init` reveals 6 lines in red
- `def AND push` reveals 3 lines in orange
- `keyword` reveals 40 lines in yellow

New filters can be pushed to the stack by pressing `ENTER` or `f`, and poped by pressing `backspace` or `delete`. Keywords can be added to the most recent filter (the one at the bottom and associated to yellow in the above screenshot) by pressing `+` or `=`, and removed from the filter by pressing `-`.

A filter is a list of keywords that a line must contain to match and get highlighted in a specific color. All keywords in the same filter are ANDed together. By defining multiple filters, you can reveal more content of the file (filters are ORed...). By default, lines not matching any filter are hidden, but their visibility can be toggled by pressing `m`. Filters are evaluated in the order that they are defined, meaning lines are shown in the color of the first filter they match.

## Features

- Supports multiple views (try pressing `1`, `2`, `3`)
- Supports multiple palettes (try pressing `c` for color)
- Various display modes (`l` toggles line numbers, `m` toggles visibility of non-matching line, `k` toggles line wrapping, ...)
- Common search key bindings (`/`, then `n` for next, `p` for previous)

## Installation

`pip install searchf`

then run

`searchf-test`

to run builtin application tests and verify your installation. Please note that your terminal must supports color (`TERM=screen-256color` or `TERM=xterm-256color`) and must be UTF-8 enabled (eg. start tmux with "tmux -u").

## Usage

`searchf <FILE>`

- Press `f` to enter keyword in a new filter
- Press `?` for help
 
 ![Screenshot searchf help](https://user-images.githubusercontent.com/15265841/147901733-f2714f76-22d1-4dc9-8ef0-133f5157f2d8.png)

When all lines are shown, including the ones not matching any filter, it can be usefull to scroll to next match with `n` or previous one with `p`. When all lines are displayed, it can be hard to identify which ones that are matching which filter, so you can either show the line numbers by pressing `l`, which will show the matching lines with colorized output, or change the highlight mode by pressing `h`, to colorize lines as a whole (and not just keywords). Just try it, as it's likely more understandable by doing than by reading this...

Showing all lines, with wrapping and numbers enabled, colorizing lines as a whole instead of just keywords:

![Screenshot searchf 2](https://user-images.githubusercontent.com/15265841/147425069-609e346d-c84d-452c-bfb2-8e32cadf10d5.png)

## Why this utility?

This tool is born from my need to be able to efficiently explore log files in interactive fashion, searching for cues, hitting dead ends and backtracking (hence the use of push/pop of filter and keyword), but also going down some exploratory paths on the side (hence the support of views).

To be more specific, I had to dig into build log files, which were a raw aggregate of many heterogenous sources (numerous compiler output, deployment scripts, test run and results, ...) resulting in rather unstructured output. The only commonality being that everything was somehow and more or less line-oriented... When a build failure occured, hints of the root caused could be hiding about anywhere.

So this tool ended making little or no assumption on the input file, which can be anything, unstructured and heterogenous, as long as it is line oriented.

## Development

If working from the sources (ie not an installed package), the application can be launched as a module:

`python3 -m searchf.app <FILE>`

### How to run the test?

- `pytest` runs unit test
- `python3 -m searchf.test.all` runs the application tests

### What about coverage?

Unit test coverage is relatively poor at 25% as `pytest --cov=searchf` returns:

```
Name                            Stmts   Miss  Cover
---------------------------------------------------
searchf/__init__.py                 1      0   100%
searchf/app.py                    534    534     0%
searchf/models.py                 101      0   100%
searchf/segments.py                46      0   100%
searchf/test/__init__.py            0      0   100%
searchf/test/all.py               134    134     0%
searchf/test/color.py              49     49     0%
searchf/test/test_models.py        48      0   100%
searchf/test/test_segments.py      47      0   100%
---------------------------------------------------
TOTAL                             960    717    25%

```

Application test coverage is better at 98%. Indeed, `coverage run -m searchf.test.all` then `coverage report` shows:

```
Name                            Stmts   Miss  Cover
---------------------------------------------------
searchf/__init__.py                 1      0   100%
searchf/app.py                    534      9    98%
searchf/models.py                 101      0   100%
searchf/segments.py                46      0   100%
searchf/test/__init__.py            0      0   100%
searchf/test/all.py               134      5    96%
searchf/test/test_models.py        48      0   100%
searchf/test/test_segments.py      47      0   100%
---------------------------------------------------
TOTAL                             911     14    98%
```

## Known Issues

- Does not work on Windows
