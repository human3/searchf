'''Unit tests for colors'''

# To properly test colors and palette support, or visualize existing
# palette definition, run python3 -m searchf.test.color

import os
import curses

from .. import colors

TERM = os.environ.get('TERM', None)


def _setup():
    print(f'TERM={TERM}')
    if TERM is None:
        return False
    curses.initscr()
    # curses will not have COLORS attribute when running within pytest,
    # so we artificially provide one
    curses.COLORS = 256
    return True


def test_init():
    '''Test colors.init()'''
    if not _setup():
        return
    # WARNING: this is not a real test since function has side-effects
    # we are not validating
    colors.init()


def test_cycle_palette_index():
    '''Test colors.cycle_palette_index()'''
    max_index = len(colors.PALETTES) - 1
    assert colors.cycle_palette_index(0, True) == 1
    assert colors.cycle_palette_index(0, False) == max_index
    assert colors.cycle_palette_index(max_index, True) == 0
    assert colors.cycle_palette_index(max_index, False) == max_index - 1


def test_apply_palette():
    '''Tests colors.apply_palette()'''
    if not _setup():
        return
    # WARNING: this is not a real test since function has side-effects
    # we are not validating
    for index in range(len(colors.PALETTES)):
        colors.apply_palette(index, False)
        colors.apply_palette(index, True)


def test_get_color_pair():
    '''Tests colors.get_color_pair()'''
    if not _setup():
        return
    # WARNING: this is not a real test since function has side-effects
    # we are not validating
    colors.get_color_pair(0, -1)
    colors.get_color_pair(0, 0)
