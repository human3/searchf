# Testing colors used by searchf
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import curses
import sys
import re
from curses.textpad import Textbox, rectangle
from curses import wrapper

import searchf

# https://stackoverflow.com/questions/18551558/how-to-use-terminal-color-palette-with-curses

default_palette = range(16)

def showPalette(stdscr, name, p):
    stdscr.addstr(f'{name:>10}')
    # for i in range(len(p)):
    #     stdscr.addstr(f' {i}', curses.color_pair(p[i]) | curses.A_BOLD)
    # stdscr.addstr('\n')
    for i in range(len(p)):
        stdscr.addstr(f' TEST{p[i]:<3}', curses.color_pair(p[i]))
    stdscr.addstr('\n')

def main(stdscr):
    assert curses.has_colors()
    #assert curses.can_change_color()

    searchf.init_colors()

    # for i in range(curses.COLORS-1):
    #     curses.init_pair(i + 1, i, 248)
    # for i in range(curses.COLORS-1):
    #     stdscr.addstr(f'{i}', curses.color_pair(i))

    # stdscr.addstr('\n', curses.color_pair(1))
    # stdscr.refresh()
    # stdscr.getch()

    # for i in range(curses.COLORS-1):
    #     curses.init_pair(i + 1, i, -1)

    # maxh, maxw = stdscr.getmaxyx()

    stdscr.addstr('Palettes:\n')
    showPalette(stdscr, 'default', default_palette)

    for i, p in enumerate(searchf.PALETTES):
        showPalette(stdscr, f'{i}', p)

    stdscr.refresh()
    stdscr.getch()

    stdscr.addstr('Flat list of color:\n')
    for i in range(curses.COLORS-1):
        stdscr.addstr(f'{i}', curses.color_pair(i))
    stdscr.addstr('\n')

    bgs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 39, 28, 33, 245, 246]
    for bg in bgs:
        for i in range(curses.COLORS-1):
            curses.init_pair(i + 1, i, bg)
        stdscr.addstr(0, 0, f'{bg}')
        stdscr.refresh()
        stdscr.getch()

    stdscr.refresh()
    stdscr.getch()


print('Starting')
stdscr = curses.initscr()
wrapper(main)
print('Done')
