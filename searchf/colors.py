'''Module that wraps curses color support into higher level palettes.'''

import curses

from . import types

BAR_COLOR_PAIR_ID = 1
BAR_COLOR_BG = 39  # 249

FIRST_FILTER_COLOR_PAIR_ID = BAR_COLOR_PAIR_ID + 1

# https://stackoverflow.com/questions/18551558/how-to-use-terminal-color-palette-with-curses
PALETTES = [
    # Dark theme, "error" first
    [
        196,  # Red
        208,  # Orange
        190,  # Yellow
        46,   # Green
        33,   # Blue
        201,  # Purple
        219,  # Pink
    ],
    # Light theme, "error" first
    [
        1,    # Red
        208,  # Orange
        3,    # Yellow
        22,   # Green
        20,   # Blue
        129,  # Purple
        201,  # Pink
    ],
    # Dark theme, "ok" first
    [
        46,   # Green
        190,  # Yellow
        208,  # Orange
        196,  # Red
        33,   # Blue
        201,  # Purple
        219,  # Pink
    ],
    # Light theme, "ok" first
    [
        22,   # Green
        3,    # Yellow
        208,  # Orange
        1,    # Red
        20,   # Blue
        129,  # Purple
        201,  # Pink
    ],
    # Dark theme, "neutral"
    [
        33,   # Blue
        201,  # Purple
        219,  # Pink
        190,  # Yellow
        46,   # Green
        208,  # Orange
        196,  # Red
    ],
    # Light theme, "neutral"
    [
        20,   # Blue
        129,  # Purple
        201,  # Pink
        3,    # Yellow
        22,   # Green
        208,  # Orange
        1,    # Red
    ],
]


def cycle_palette(
        palette_id: types.PaletteId,
        forward: bool
        ) -> types.PaletteId:
    '''Select the palette index after the given one in the given direction'''
    assert palette_id >= 0
    assert palette_id < len(PALETTES)
    incr = 1 if forward else -1
    return (palette_id + incr) % len(PALETTES)


def apply_palette(palette_id: types.PaletteId, reverse: bool) -> None:
    '''Apply given palette to curses.'''
    # Note: python raises IndexError for us if palette_index is out of range
    pal = PALETTES[palette_id]
    for i, color in enumerate(pal):
        pair_id = FIRST_FILTER_COLOR_PAIR_ID + i
        if reverse:
            curses.init_pair(pair_id, 0, color)
        else:
            curses.init_pair(pair_id, color, -1)


def get_color_pair(
        palette_id: types.PaletteId,
        filter_index: int
        ) -> types.ColorPair:
    '''Gets the curses.color_pair associated with given palette and filter'''
    if filter_index < 0:
        return curses.color_pair(0)
    colors_count = len(PALETTES[palette_id])
    pair_id = FIRST_FILTER_COLOR_PAIR_ID + (filter_index % colors_count)
    return curses.color_pair(pair_id)


def init():
    '''Initializes color support.'''
    assert curses.has_colors()
    assert curses.COLORS >= 256, 'Not enough colors (try TERM=screen-256color)'
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(BAR_COLOR_PAIR_ID, 0, BAR_COLOR_BG)
