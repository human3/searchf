'''Interactive test of colors used by searchf'''

import curses
import sys
from .. import colors

# https://stackoverflow.com/questions/18551558/how-to-use-terminal-color-palette-with-curses

DEFAULT_PALETTE = range(16)
DEFAULT_PALETTE_EXT = range(16, 32)


def _reset():
    for i in range(curses.COLORS-1):
        curses.init_pair(i, i, -1)
    for i in range(16):
        curses.init_pair(i + 16, -1, i)
        curses.init_pair(i + 32, i, i)
        curses.init_pair(i + 48, 15, i)


def _show_all(scr):
    scr.move(0, 0)
    scr.addstr('Flat list of color:\n')
    for i in range(8):
        fgc, bgc = curses.pair_content(i)
        scr.addstr(f'{i} {fgc} {bgc} ', curses.color_pair(i))
    scr.addstr('\n')
    for i in range(curses.COLORS-1):
        scr.addstr(f'{i}', curses.color_pair(i))
    scr.addstr('\n')


def _show_palette(scr, name, pal):
    '''Draw sample text on screen using the given palette'''
    scr.addstr(f'{name:12}')
    for _, color in enumerate(pal):
        scr.addstr(f' {color:<3}', curses.color_pair(color))
    scr.addstr('\n')


def _wait(scr):
    scr.addstr('\n<Press q to quit, any other key to continue>\n')
    scr.refresh()
    key = scr.getch()
    if key == ord('q'):
        sys.exit(0)


def _show_all_and_wait(scr):
    _show_all(scr)
    _wait(scr)


def _show_all_palettes(scr):
    _reset()
    _show_all_and_wait(scr)
    for i, _ in enumerate(colors.PALETTES):
        colors.apply_palette(i, False)
        _show_all_and_wait(scr)

        colors.apply_palette(i, True)
        _show_all_and_wait(scr)


def _one_screen(scr):
    _reset()
    scr.move(0, 0)
    name = 'Palette/idx'
    scr.addstr(f'{name:12}')
    for i in range(16):
        scr.addstr(f' {i:<3}')
    scr.addstr('\n')

    for i, pal in enumerate(colors.PALETTES):
        _show_palette(scr, f'{i}', pal)

    _show_palette(scr, 'default', DEFAULT_PALETTE)
    _show_palette(scr, '', DEFAULT_PALETTE_EXT)
    _wait(scr)


def main(scr):
    '''Module entry point'''
    assert curses.has_colors()
    colors.init()
    _show_all_palettes(scr)
    _one_screen(scr)


curses.wrapper(main)
