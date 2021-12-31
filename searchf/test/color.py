'''Testing colors used by searchf'''

import curses
import searchf
import searchf.app

# https://stackoverflow.com/questions/18551558/how-to-use-terminal-color-palette-with-curses

default_palette = range(16)

def show_palette(scr, name, pal):
    '''Draw sample text on screen using the given palette'''
    scr.addstr(f'{name:>10}')
    # for i in range(len(pal)):
    #     stdscr.addstr(f' {i}', curses.color_pair(p[i]) | curses.A_BOLD)
    # stdscr.addstr('\n')
    for i, color in enumerate(pal):
        scr.addstr(f' TEST{pal[i]:<3}', curses.color_pair(color))
    scr.addstr('\n')

def main(scr):
    '''Module entry point'''
    assert curses.has_colors()
    #assert curses.can_change_color()

    searchf.app.init_colors()

    # for i in range(curses.COLORS-1):
    #     curses.init_pair(i + 1, i, 248)
    # for i in range(curses.COLORS-1):
    #     scr.addstr(f'{i}', curses.color_pair(i))

    # scr.addstr('\n', curses.color_pair(1))
    # scr.refresh()
    # scr.getch()

    # for i in range(curses.COLORS-1):
    #     curses.init_pair(i + 1, i, -1)

    # maxh, maxw = scr.getmaxyx()

    scr.addstr('Palettes:\n')
    show_palette(scr, 'default', default_palette)

    for i, pal in enumerate(searchf.app.PALETTES):
        show_palette(scr, f'{i}', pal)

    scr.refresh()
    scr.getch()

    scr.addstr('Flat list of color:\n')
    for i in range(curses.COLORS-1):
        scr.addstr(f'{i}', curses.color_pair(i))
    scr.addstr('\n')

    bgs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 39, 28, 33, 245, 246]
    for background in bgs:
        for i in range(curses.COLORS-1):
            curses.init_pair(i + 1, i, background)
        scr.addstr(0, 0, f'{background}')
        scr.refresh()
        scr.getch()

    scr.refresh()
    scr.getch()

curses.wrapper(main)
