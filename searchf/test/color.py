'''Testing colors used by searchf'''

# pylint: disable=invalid-name

import curses
from .. import app

# https://stackoverflow.com/questions/18551558/how-to-use-terminal-color-palette-with-curses

default_palette = range(16)

def _reset():
    for i in range(curses.COLORS-1):
        curses.init_pair(i, i, -1)

def _show_all(scr):
    scr.move(0,0)
    scr.addstr('Flat list of color:\n')
    for i in range(8):
        fg, bg  = curses.pair_content(i)
        scr.addstr(f'{i} {fg} {bg} ', curses.color_pair(i))
    scr.addstr('\n')
    for i in range(curses.COLORS-1):
        scr.addstr(f'{i}', curses.color_pair(i))
    scr.addstr('\n')
    scr.refresh()

def _show_palette(scr, name, pal):
    '''Draw sample text on screen using the given palette'''
    scr.addstr(f'{name:12}')
    for i, color in enumerate(pal):
        scr.addstr(f' {pal[i]:<3}', curses.color_pair(color))
    scr.addstr('\n')

def main(scr):
    '''Module entry point'''
    assert curses.has_colors()
    assert curses.can_change_color()

    app.init_colors()
    _reset()

    _show_all(scr)
    scr.getch()

    for i, pal in enumerate(app.PALETTES):
        app.apply_palette(pal, False)
        _show_all(scr)
        scr.getch()

        app.apply_palette(pal, True)
        _show_all(scr)
        scr.getch()

    _reset()

    name = 'Palette/idx'
    scr.addstr(f'{name:12}')
    for i in range(16):
        scr.addstr(f' {i:<3}')
    scr.addstr('\n')

    for i, pal in enumerate(app.PALETTES):
        _show_palette(scr, f'{i}', pal)

    _show_palette(scr, 'default', default_palette)

    scr.refresh()
    scr.getch()

curses.wrapper(main)
