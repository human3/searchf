'''Module that wraps curses color support into higher level palettes.'''

import curses

from . import types

Pair = int
PairId = int
ColorId = int

# The first 64 color pair ids are reserved to render SGR
# https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_(Select_Graphic_Rendition)_parameters
SGR_COLOR_PAIR_ID_COUNT = 64

# Status bar color pair id and background color
BAR_COLOR_PAIR_ID = SGR_COLOR_PAIR_ID_COUNT
BAR_COLOR_BG = 39  # 249

# First color pair id reserved for filters. The actual number of color reserved
# depends on the number of colors in the palette.
FIRST_FILTER_COLOR_PAIR_ID = BAR_COLOR_PAIR_ID + 1

# https://stackoverflow.com/questions/18551558/how-to-use-terminal-color-palette-with-curses
PALETTES = [
    # Dark theme, "error" in red first
    [
        196,  # Red
        208,  # Orange
        190,  # Yellow
        46,   # Green
        33,   # Blue
        201,  # Purple
        219,  # Pink
    ],
    # Light theme, "error" in red first
    [
        1,    # Red
        208,  # Orange
        3,    # Yellow
        2,    # Green
        12,   # Blue
        129,  # Purple
        201,  # Pink
    ],
    # Dark theme, "ok" in green first
    [
        46,   # Green
        190,  # Yellow
        208,  # Orange
        196,  # Red
        33,   # Blue
        201,  # Purple
        219,  # Pink
    ],
    # Light theme, "ok" in green first
    [
        2,    # Green
        3,    # Yellow
        208,  # Orange
        1,    # Red
        12,   # Blue
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
        12,   # Blue
        129,  # Purple
        201,  # Pink
        3,    # Yellow
        2,    # Green
        208,  # Orange
        1,    # Red
    ],
]


def cycle_palette(
        palette_id: types.PaletteId,
        forward: bool,
) -> types.PaletteId:
    '''Returns the palette index after the given one in the given direction.'''
    assert palette_id >= 0
    assert palette_id < len(PALETTES)
    incr = 1 if forward else -1
    return (palette_id + incr) % len(PALETTES)


def apply_palette(
        palette_id: types.PaletteId,
        reverse: bool,
) -> None:
    '''Applies given palette to curses.'''
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
        filter_index: int,
) -> Pair:
    '''Gets the curses.color_pair associated with given palette and filter.'''
    if filter_index < 0:
        return curses.color_pair(0)
    colors_count = len(PALETTES[palette_id])
    pair_id = FIRST_FILTER_COLOR_PAIR_ID + (filter_index % colors_count)
    return curses.color_pair(pair_id)


def get_color_pair_id(
        fg: ColorId,
        bg: ColorId,
) -> PairId:
    '''Gets color pair associated with given foreground and background.'''
    assert -1 <= fg <= 15, fg
    assert -1 <= bg <= 15, bg
    assert bg != -1 or fg != -1
    if bg == -1:
        return fg
    if fg == -1:
        return 16 + bg
    if fg == bg:
        return 32 + fg
    return 48 + bg


def get_fg_bg_color_pair(
        fg: ColorId,
        bg: ColorId
) -> Pair:
    '''Returns the color pair use to display the given fg and bg colors.'''
    return curses.color_pair(get_color_pair_id(fg, bg))


def init_color_pairs():
    '''Initiliazes the color pairs we depend on.'''
    curses.init_pair(BAR_COLOR_PAIR_ID, 0, BAR_COLOR_BG)
    for i in range(16):
        curses.init_pair(i, i, -1)
        curses.init_pair(i + 16, -1, i)
        curses.init_pair(i + 32, i, i)
        curses.init_pair(i + 48, 15, i)


def init():
    '''Initializes color support.'''
    assert curses.has_colors()
    assert curses.COLORS >= 256, 'Not enough colors (try TERM=screen-256color)'
    curses.start_color()
    curses.use_default_colors()
    init_color_pairs()
