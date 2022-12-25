# [searchf](https://github.com/human3/searchf)

![Latest Version](https://img.shields.io/pypi/v/searchf)

Utility program to interactively search and colorize keywords in text files, select relevant lines, remove noise and help you discover the things you should care about. Works in terminals and uses stack-based interactions to minimize the number of key presses (think HP calculators).

Press `ENTER` to define the first keyword of a filter and reveal only the lines containing that keyword. Press `+` to add another keyword to the current filter in order to further narrow down the lines currently displayed.

![Peek 2021-12-31 21-05](https://user-images.githubusercontent.com/15265841/147842653-46e2fc0f-fdac-424e-9e5a-2e806d86440e.gif)

A filter is a list of keywords that a line must contain to match and get highlighted in a specific color. All keywords in the same filter are ANDed together. By defining multiple filters, you can reveal more content of the file (filters are ORed...). By default, lines not matching any filter are hidden, but their visibility can be toggled by pressing `m`. Filters are evaluated in the order that they are defined, meaning keywords and lines are shown using the color of the first filter they match.

## Features

- Can filter out non matching lines or display everything (you choose with `m`)
- Supports "reverse matching" mode to hide matching lines (try `M`)
- Multiple highlight and colorization modes (press `h` to cycle through all modes)
- Color palettes (press `c` to cycle through all palettes)
- Various other display modes (`l` toggles line numbers visibility, `k` toggles line wrapping, ...)
- Multiple views (press `1`, `2`, `3` to switch) with possibility to pass filters of one view to another view (try `!`, `@`, `#`)
- Common search key bindings (`/`, then `n` for next, `p` for previous)
- Common key bindings to scroll up/down pages or goto line

## Installation

`pip install searchf`

then run

`searchf-test`

to run builtin application tests and verify your installation. Please note that your terminal must supports color (`TERM=screen-256color` or `TERM=xterm-256color`) and must be UTF-8 enabled (eg. start tmux with "tmux -u").

## Usage

`searchf <FILE>`

- Press `f` to enter keyword in a new filter
- Press `?` for help

![Screenshot searchf help](https://user-images.githubusercontent.com/15265841/209476860-4e4e4600-0333-43f2-9cd7-65777448f927.png)

When all lines are shown, including the ones not matching any filter, it can be usefull to scroll to next match with `n` or previous one with `p`. When all lines are displayed, it can be hard to identify which ones that are matching which filter, so you can either show the line numbers by pressing `l`, which will show the matching lines with colorized output, or change the highlight mode by pressing `h`, to colorize lines as a whole (and not just keywords). Just try it, as it's likely more understandable by doing than by reading this...

Showing all lines, with wrapping and numbers enabled, colorizing lines as a whole instead of just keywords:

![Screenshot searchf 2](https://user-images.githubusercontent.com/15265841/147425069-609e346d-c84d-452c-bfb2-8e32cadf10d5.png)

## Why this utility?

This tool is born from my need to be able to efficiently explore log files in interactive fashion, searching for cues, hitting dead ends and backtracking (hence the use of push/pop of filter and keyword), but also going down some exploratory paths on the side (hence the support of views).

To be more specific, I had to dig into build log files, which were a raw aggregate of many heterogenous sources (numerous compiler output, deployment scripts, test run and results, ...) resulting in rather unstructured output. The only commonality being that everything was somehow and more or less line-oriented... When a build failure occured, hints of the root caused could be hiding about anywhere.

So this tool ended making little or no assumption on the input file, which can be anything, unstructured and heterogenous, as long as it is line oriented.

## Development

Please refer to [DEV.md](DEV.md) for further information.
