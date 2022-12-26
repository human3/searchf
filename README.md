# [searchf](https://github.com/human3/searchf)

![Latest Version](https://img.shields.io/pypi/v/searchf)

Utility program to interactively search keywords in text files. Works in terminals thanks to curses.

[searchf_1_11.webm](https://user-images.githubusercontent.com/15265841/209586800-ce59aa42-e0de-4602-a928-c7e675feb12b.webm)

## Installation

`pip install searchf`

Please note that your terminal must supports color (`TERM=screen-256color` or `TERM=xterm-256color`) and must be UTF-8 enabled (eg. start tmux with "tmux -u").

## Features

- Multiple highlight and colorization modes (press `h` to cycle through all modes)
- Color palettes (press `c` to cycle through all palettes)
- Various other display modes (`l` toggles line numbers visibility, `k` toggles line wrapping, ...)
- Multiple views (press `1`, `2`, `3` to switch) with possibility to pass filters of one view to another view (try `!`, `@`, `#`)
- Common search key bindings (`/`, then `n` for next, `p` for previous)
- Common key bindings to scroll up/down pages or goto line
- Filters can persist to disk

## Usage

`searchf <FILE>`

- Press `f` to enter keyword in a new filter
- Press `?` for help

Press `ENTER` to define the first keyword of a filter and reveal only the lines containing that keyword. Press `+` to add another keyword to the current filter in order to further narrow down the lines currently displayed.

A filter is a list of keywords that a line must contain to match and get highlighted in a specific color. By defining multiple filters, you can reveal more content of the file. By default, lines not matching any filter are hidden, but you can progressively reveal context surrounding matching lines by pressing `m` multiple times, all the way to the whole content of the file. Filters can also be used to filter out content you do not want to see (press `x` to toggle this mode).

![Screenshot searchf help](https://user-images.githubusercontent.com/15265841/209476860-4e4e4600-0333-43f2-9cd7-65777448f927.png)

## Why?

This tool is born from my need to interactively search into log files, with the ability to backtrack when hitting dead ends (hence the use of push/pop of filter and keyword), and to go down some exploratory paths on the side (hence the support of views). I use it most when I'm not fully aware of what I am searching for...

To be more specific, I often have to dig into build log files, which are a raw aggregate of many heterogenous sources (numerous compiler output, deployment scripts, test run and results, ...) resulting in rather unstructured output. The only commonality being that everything is more or less line-oriented. When a build failure occurs, searchf helps me find hints of the root cause which can be hiding about anywhere.

So this tool ends up making little or no assumption on the input file, which can be anything, unstructured and heterogenous, as long as it is line oriented.

## Development

Please refer to [DEV.md](https://github.com/human3/searchf/blob/master/docs/DEV.md) for further information.
