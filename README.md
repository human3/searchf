# [searchf](https://github.com/human3/searchf)

Utility program to interactively search for keywords in text files (log files, build output files, etc.), colorize matching lines and help you discover the things you should care about, "squeezing" useful information out of files. Works in terminals, uses curses for text base UI.

![Screenshot searchf 1](https://user-images.githubusercontent.com/15265841/145870066-a5411df9-e8e2-4f3e-ba14-c4cd55f22778.png)

A filter is a list of keywords that a line must contain to match and get highlighted in a specific color. All keywords in the same filter are ANDed together. By defining multiple filters, you can reveal more content of the file. By default, lines not matching any filter are hidden, but their visibility can be toggled by pressing `m`. Filters are evaluated in the order that they are defined, meaning lines are shown in the color of the first filter they match.

In the above screenshot, 3 filters have been defined:
- `def AND init` reveals 6 lines in red
- `def AND push` reveals 3 lines in orange
- `keyword` reveals 44 lines in yellow

Why this utility? I had to dig into build log files, which were a raw aggregate of many heterogenous sources (numerous compiler output, deployment scripts, test run and results, ...) resulting in rather unstructured output. The only commonality being that everything was somehow and more or less line-oriented... When a build failure occured, hints of the root caused could be hiding about anywhere. So this tool is born from my need to be able to explore log files in interactive fashion, searching for cues, going down some exploratory paths pm the side (hence the support of views), hitting dead ends and backtracking (hence the use of push/pop of filter and keyword), etc. Little or no assumption is made on the input file, which can be anything, unstructured and heterogenous, as long as it is line oriented.

## Installation

`pip install searchf`

## Usage

`searchf <file>`

- Press `f` to enter keyword in a new filter
- Press `?` for help
 
![Screenshot searchf help](https://user-images.githubusercontent.com/15265841/145870427-25009b65-fd35-446c-bf27-a1e350cc224f.png)

When all lines are shown, including the ones not matching any filter, it can be usefull to scroll to next match with `n` or previous one with `p`. When all lines are displayed, it can be hard to identify which ones that are matching which filter, so you can either show the line numbers by pressing `l`, which will show the matching lines with colorized output, or change the highlight mode by pressing `h`, to colorize lines as a whole (and not just keywords). Just try it, as it's likely more understandable by doing than by reading this...

Showing all lines, with wrapping and numbers enabled, colorizing lines as a whole instead of just keywords:

![Screenshot searchf 2](https://user-images.githubusercontent.com/15265841/145871759-74e6d755-4d02-43a2-8bbb-c3fdec18c61f.png)

## Warning

- Better alternatives are likely many, I just couldn't find any that suits me so far. I considered lnav, few VSCode extensions, `cat | grep` and alikes ...
- This script loads everything in memory, so...

## Tips

- Make sure to enable UTF-8 (eg. start tmux like this "tmux -u")

## Known Issues

- Does not work on Windows... No color there... It can run, but it's hard:
  - py -m pip install windows-curses
    https://www.lfd.uci.edu/~gohlke/pythonlibs/#curses
  - py -m pip install "YOUR\_DOWNLOADS\curses-2.2.1+utf8-cp310-cp310-win_amd64.whl"
  - mingw64 + winpty py searchf.py

## Wish list

- More palettes
- Cleanup code! Remove COLOR_BAR hack in source (inner beauty's sake)
- Tail function that automatically reload (instead of having to press `t`)
- Screen dynamic resizing
- Bookmark
- Ability to save/load filters
- Ability to save filtered file
