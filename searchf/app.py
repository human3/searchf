'''https://github.com/human3/searchf'''

# This code tries to abide by the following principles:
# - Simplicity comes first
# - Don't Repeat Yourself (aka DRY)
# - no-use-before-define

# pylint: disable=invalid-name
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-arguments

from curses.textpad import Textbox
from enum import Enum, auto
import argparse
import curses
import os
import re
import sys

import searchf
from searchf import segments
from searchf import models

# Changes layout to show a debug window in which debug() function will output
USE_DEBUG = False

# https://stackoverflow.com/questions/18551558/how-to-use-terminal-color-palette-with-curses
PALETTES = [
    # Dark theme, "error" first
    [
        196, # Red
        208, # Orange
        190, # Yellow
        46,  # Green
        33,  # Blue
        201, # Purple
        219, # Pink
    ],
    # Light theme, "error" first
    [
        1,   # Red
        208, # Orange
        3,   # Yellow
        22,  # Green
        20,  # Blue
        129, # Purple
        201, # Pink
    ],
    # Dark theme, "ok" first
    [
        46,  # Green
        190, # Yellow
        208, # Orange
        196, # Red
        33,  # Blue
        201, # Purple
        219, # Pink
    ],
    # Light theme, "ok" first
    [
        22,  # Green
        3,   # Yellow
        208, # Orange
        1,   # Red
        20,  # Blue
        129, # Purple
        201, # Pink
    ],
    # Dark theme, "neutral"
    [
        33,  # Blue
        201, # Purple
        219, # Pink
        190, # Yellow
        46,  # Green
        208, # Orange
        196, # Red
    ],
    # Light theme, "neutral"
    [
        20,  # Blue
        129, # Purple
        201, # Pink
        3,   # Yellow
        22,  # Green
        208, # Orange
        1,   # Red
    ],
]

BAR_COLOR_PAIR_ID = 1
BAR_COLOR_BG = 39 # 249

FIRST_FILTER_COLOR_PAIR_ID = BAR_COLOR_PAIR_ID + 1

def apply_palette(pal, reverse):
    '''Apply given palette to curses.'''
    for i, color in enumerate(pal):
        pair_id = FIRST_FILTER_COLOR_PAIR_ID + i
        if reverse:
            curses.init_pair(pair_id, 0, color)
        else:
            curses.init_pair(pair_id, color, -1)
        debug(f'pal {i}:{pair_id} {color}')

def init_colors():
    '''Initializes color support.'''
    assert curses.has_colors()
    assert curses.COLORS == 256, 'Try setting TERM env var to screen-256color'
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(BAR_COLOR_PAIR_ID, 0, BAR_COLOR_BG)

def get_max_yx(scr):
    '''This function is a test artifact that wraps getmaxyx() from curses
so that we can overwrite it and test specific dimensions.'''
    return scr.getmaxyx()

def get_ch(scr):
    '''This function is a test artifact that wraps getch() from curses so
that we can overwrite it and inject keys while testing.'''
    return scr.getch()

class EscapeException(Exception):
    '''Signals that Escape key has been pressed'''

def _validate(c):
    if c == curses.ascii.DEL:
        c = curses.KEY_BACKSPACE
    elif c == curses.ascii.ESC:
        raise EscapeException()
    return c

def _get_text(scr, y, x, prompt, handler):
    scr.addstr(y, x, prompt)
    x += len(prompt)
    editwin = curses.newwin(1, 30, y, x)
    scr.refresh()
    box = Textbox(editwin)
    text = ''
    try:
        handler(box)
        text = box.gather().strip()
    except EscapeException:
        pass

    editwin.clear()
    editwin.refresh()
    clear(scr, y, 0, len(prompt))
    return text if text else ''

def get_text(scr, y, x, prompt):
    '''Prompts user to enter some text.'''
    def handle(box):
        box.edit(validate=_validate)
    return _get_text(scr, y, x, prompt, handle)

def clear(scr, y, x, length):
    '''Prints "length" spaces at the given position'''
    _, maxw = get_max_yx(scr)
    blank = f'{" ":>{length}}'
    scr.addstr(y, x, blank[:maxw-(x+1)])
    scr.move(y, x)

COLORIZE_MODES = [ 'Keyword', 'Keyword highlight', 'Line' ]

class ViewConfig:
    '''Holds the configuration of a view, like filters to use or the
display modes, typically changed by end users to match their
need. Does not contain any data related to file content. Should be
serialized at some point to persist somewhere and get re-used accross
session.

    '''
    line_numbers: bool = False
    wrap: bool = True
    bullets: bool = False
    only_matching: bool = True
    show_spaces: bool = False
    colorize_mode: int = 0
    palette_index: int = 0

    def __init__(self):
        self.filters = []

    def has_filters(self):
        '''Returns whether or not there is any filter'''
        return len(self.filters) > 0

    def highlights_whole_line(self):
        '''Returns whether or not whole line should be hightlighted'''
        return self.colorize_mode == 2

    def uses_reverse_palette(self):
        '''Returns whether or not palette color should be reversed'''
        return self.colorize_mode == 1

    def colorize_mode_text(self):
        '''Returns a text reprentation of the current colorize mode'''
        return COLORIZE_MODES[self.colorize_mode]

    def next_colorize_mode(self):
        '''Selects the next colorization modes, cycling through all of them'''
        self.colorize_mode = (self.colorize_mode + 1 ) % len(COLORIZE_MODES)

    def top_filter(self):
        '''Returns top level filter (most recently added)'''
        count = len(self.filters)
        assert count > 0
        return self.filters[count-1]

    def push_filter(self, f):
        '''Pushes the given filter'''
        self.filters.append(f)

    def get_color_pair_id(self, fidx):
        '''Returns the id of the color pair associated with given filter index'''
        palette = PALETTES[self.palette_index]
        pair_id = FIRST_FILTER_COLOR_PAIR_ID + (fidx % len(palette))
        f, b = curses.pair_content(pair_id)
        debug(f'{fidx} {pair_id} {f} {b}')
        return pair_id

    def next_palette(self):
        '''Select the "next" palette'''
        self.palette_index = (self.palette_index + 1) % len(PALETTES)
        return self.palette_index

class TextViewCommand(Enum):
    '''Simple commands accepted by TextView class, that do not take any argument.'''
    GO_UP = auto()
    GO_DOWN = auto()
    GO_LEFT = auto()
    GO_RIGHT = auto()
    GO_HOME = auto()
    GO_END = auto()
    GO_NPAGE = auto()
    GO_PPAGE = auto()
    GO_SLEFT = auto()
    GO_SRIGHT = auto()
    POP_FILTER = auto()
    POP_KEYWORD = auto()
    VSCROLL_TO_NEXT_MATCH = auto()
    VSCROLL_TO_PREV_MATCH = auto()
    TOGGLE_ONLY_MATCHING = auto()
    TOGGLE_LINE_NUMBERS = auto()
    TOGGLE_WRAP = auto()
    TOGGLE_BULLETS = auto()
    TOGGLE_SHOW_SPACES = auto()
    NEXT_COLORIZE_MODE = auto()
    TOGGLE_IGNORE_CASE = auto()
    NEXT_PALETTE = auto()

def bool_to_text(value):
    '''Converts a boolean value to text.'''
    return 'enabled' if value else 'disabled'

CASE_MODE_TEXT = ['ignored', 'sensitive']
CASE_MODE_LEN = len(max(CASE_MODE_TEXT, key=len))

class TextView:
    '''Display selected content of a file, using filters and keyword to
    highlight specific text.'''
    def __init__(self, scr, name, path):
        self._model = models.Model()
        self._vm = models.ViewModel()
        self._config = ViewConfig()
        self._scr = scr
        self._name = name
        self._basename = os.path.basename(path)
        self._max_visible_lines_count = 0
        self._win = None
        self._size = (0, 0)

    def name(self):
        '''Gets the name of the view.'''
        return self._name

    def layout(self, h, w, y, x):
        '''Sets dimension of the view. Must be call before everything and
        only once (no dynamic layout supported)'''

        # _size stores number of lines and columns available to draw content
        self._size = (h, w)
        self._win = curses.newwin(h, w, y, x)

    def _get_prefix_info(self):
        '''Returns total length of prefix, the number of digits of the largest
line number and separator'''
        if self._config.line_numbers:
            number_length = self._model.line_number_length()
            sep = ' │ '
        elif self._config.wrap:
            number_length = 0
            sep = '◆ ' if self._config.bullets else '' # curses.ACS_DIAMOND
        else:
            number_length = 0
            sep = ''
        return number_length + len(sep), number_length, sep

    def _draw_bar(self, y):
        '''Draws the status bar and the filter stack underneath'''

        _, w = self._size
        style = curses.color_pair(BAR_COLOR_PAIR_ID)
        self._win.hline(y, 0, curses.ACS_HLINE, w, style)

        x = 1
        if not self._config.has_filters():
            text = ' No filter '
            self._win.addstr(y, x, text, style)
        else:
            text = ' Case '
            self._win.addstr(y, x, f'{text}', style)

            x = CASE_MODE_LEN + 1
            text = f'{self._model.hits_count():>8} hits '
            self._win.addstr(y, x, text, style)

        # Print from right to left
        def move_left_for(x, text):
            return max(0, x - len(text) - 1)
        x = w

        text = f' {self._name} '
        x = move_left_for(x, text)
        self._win.addstr(y, x, text, style)

        text = ''.ljust(5) # voffest_desc is not always shown, but at most 5 char long
        x = move_left_for(x, text)
        if len(self._vm.voffset_desc) > 0:
            text = f' {self._vm.voffset_desc:>3} '
            self._win.addstr(y, x, text, style)

        text = f' {self._model.line_count()} lines '
        x = move_left_for(x, text)
        self._win.addstr(y, x, text, style)

        text = f' {self._basename} '
        x = move_left_for(x, text)
        self._win.addstr(y, x, text, style | curses.A_BOLD)

        assert len(self._model.hits) == len(self._config.filters)
        for i, f in enumerate(self._config.filters):
            color = curses.color_pair(self._config.get_color_pair_id(i))

            x = 0
            text = CASE_MODE_TEXT[0 if f.ignore_case else 1]
            self._win.addstr(y + 1 + i, x, text)

            x += CASE_MODE_LEN + 1
            text = ' AND '.join(f.keywords)
            self._win.addstr(y + 1 + i, x, f'{self._model.hits[i]:>8} {text}', color)

    def _draw_prefix(self, y, prefix_info, line_idx, color):
        _, w_index, sep = prefix_info
        if w_index > 0:
            self._win.addstr(y, 0, f'{line_idx:>{w_index}}', color | curses.A_BOLD)
        self._win.addstr(y, w_index, f'{sep}')

    def _draw_content(self, position, text, matching_segments, offset, color):
        y, x = position
        vend = offset + self._vm.size[1]
        if self._config.show_spaces:
            text = text.replace(' ', '·') # Note: this is curses.ACS_BULLET
        if self._config.highlights_whole_line():
            text = text[offset:vend]
            text = f'{text:<{self._vm.size[1]}}'
            self._win.addnstr(y, x, text, self._size[1], color)
        else:
            for match, start, end in segments.iterate(offset, vend, matching_segments):
                assert start < end
                c = color if match else 0
                l = end - start
                self._win.addnstr(y, x, text[start:end], l, c)
                x += l

    def draw(self):
        '''Draws the view'''
        # debug(f'{self._name} draw {self._vm.voffset}')
        self._win.clear()

        prefix_info = self._get_prefix_info()

        # Only draw what we need: we are going to pull at most
        # _max_visible_lines_count lines from the data model, possibly
        # less if some content needs multiple lines (wrapping)
        iddata = self._vm.voffset
        iddatamax = self._vm.lines_count()

        for y in range(self._max_visible_lines_count):
            if iddata >= iddatamax:
                break
            idata, offset = self._vm.data[iddata]
            iddata += 1
            line_idx, filter_idx, text, matching_segments = self._model.data[idata]
            color = 0 if filter_idx < 0 else self._config.get_color_pair_id(filter_idx)
            color = curses.color_pair(color)
            # If offset is not 0, this means the original content line
            # is being wrapped on to multiple lines on the screen. We
            # only draw the prefix on the first line, which has offset
            # 0.
            if offset == 0:
                self._draw_prefix(y, prefix_info, line_idx, color)
            offset += self._vm.hoffset
            self._draw_content((y, prefix_info[0]), text, matching_segments, offset, color)

        self._draw_bar(self._max_visible_lines_count)

        self._win.refresh()

    def _layout(self, redraw):
        '''Propagate layout changes: evaluates the available space and calls
layout of the view model.

        '''

        # Compute space available for file content
        h, w = self._size
        prefix_len, _, _ = self._get_prefix_info()
        h = max(0, h - 1 - len(self._config.filters))
        w = max(0, w - prefix_len)

        self._vm.layout(h, w, self._model.data, self._config.wrap)
        self._max_visible_lines_count = h

        # Try preserve current voffset, but make sure we comply with
        # constraints which might just have changed.
        self.set_v_offset(self._vm.voffset, False)

        assert self._vm.voffset == 0 or self._vm.voffset < self._vm.lines_count()

        if redraw:
            self.draw()

    def _sync(self, redraw):
        self._model.sync(self._config.filters, self._config.only_matching)
        self._vm.reset_offsets()
        self._layout(redraw)

    def set_lines(self, lines):
        '''Sets the content of this view. Assumes the view is offscreen and does
        not trigger a redraw.'''
        self._model.set_lines(lines)
        self._sync(False)

    def _pop_filter(self):
        if self._config.has_filters():
            self._config.filters.pop()
            self._sync(True)

    def push_keyword(self, keyword, new_filter):
        '''Pushes a new keyword in current top level filter (if new_filter is
        False) or in a brand new filter (if new_filter is True).'''
        if len(keyword) <= 0:
            return 'No keyword added'
        try:
            re.compile(keyword)
        except re.error:
            return 'Invalid python regex pattern'
        if not self._config.has_filters():
            new_filter = True # Force a new filter since we have none
        if new_filter:
            f = models.Filter()
            f.ignore_case = keyword.lower() == keyword
            self._config.push_filter(f)

        self._config.top_filter().add(keyword)
        self._sync(True)
        return 'New filter created' if new_filter else 'Keyword added'

    def _pop_keyword(self):
        if not self._config.has_filters():
            return
        f = self._config.top_filter()
        k_count = len(f.keywords)
        if k_count <= 1:
            self._pop_filter()
        else:
            f.pop()
            self._sync(True)

    def _toggle_line_numbers(self):
        self._config.line_numbers = not self._config.line_numbers
        self._layout(True)
        return f'Line numbers {bool_to_text(self._config.line_numbers)}'

    def _toggle_wrap(self):
        self._config.wrap = not self._config.wrap
        self._layout(True)
        return f'Line wrapping {bool_to_text(self._config.wrap)}'

    def _toggle_bullets(self):
        self._config.bullets = not self._config.bullets
        self._layout(True)
        return f'Bullets {bool_to_text(self._config.bullets)}'

    def _toggle_only_matching(self):
        self._config.only_matching = not self._config.only_matching
        self._sync(True)
        return f'Only matching lines {bool_to_text(self._config.only_matching)}'

    def _toggle_show_spaces(self):
        self._config.show_spaces = not self._config.show_spaces
        self.draw()
        return f'Show spaces {bool_to_text(self._config.show_spaces)}'

    def _next_colorize_mode(self):
        self._config.next_colorize_mode()
        self.show()
        return f'Colorize mode: {self._config.colorize_mode_text()}'

    def _toggle_ignore_case(self):
        if not self._config.has_filters():
            return 'Cannot change case sentitivity (no keyword)'
        f = self._config.top_filter()
        f.ignore_case = not f.ignore_case
        self._sync(True)
        return f'Ignore case set to {f.ignore_case}'

    def _apply_palette_and_draw(self):
        apply_palette(PALETTES[self._config.palette_index],
                      self._config.uses_reverse_palette())
        self.draw()

    def show(self):
        '''Shows the view, after it was hidden by another one'''
        self._apply_palette_and_draw()

    def _next_palette(self):
        idx = self._config.next_palette()
        self._apply_palette_and_draw()
        return f'Using color palette #{idx}'

    def _set_h_offset(self, offset):
        if self._vm.set_h_offset(offset):
            self.draw()

    def set_v_offset(self, offset, redraw):
        '''Sets the vertical offset of the view.'''
        if self._vm.set_v_offset(offset) and redraw:
            self.draw()

    def _hscroll(self, delta):
        self._set_h_offset(self._vm.hoffset + delta)

    def _vscroll(self, delta):
        self.set_v_offset(self._vm.voffset + delta, True)

    def goto_line(self, line):
        '''Makes sure the given line is visible, making it the first line on
        the screen unless that would make last line of the file not
        displayed at the bottom.'''
        try:
            line = int(line)
        except ValueError:
            return 'Not a number'
        if line <= 0:
            self.set_v_offset(0, True)
        elif line >= self._vm.lines_count():
            self.set_v_offset(sys.maxsize, True)
        else:
            voffset = 0
            for idata, _ in self._vm.data:
                i, _, _, _ = self._model.data[idata]
                if i >= line:
                    self.set_v_offset(voffset, True)
                    break
                voffset += 1
        return f'Goto line {line}'

    def has_filters(self):
        '''Returns whether the view has any filter or not.'''
        return self._config.has_filters()

    def _vscroll_to_match(self, starting, direction):
        iddata = self._vm.voffset
        idatamax = len(self._model.data)
        idata, _ = self._vm.data[iddata]
        if not starting:
            idata += direction
        while 0 <= idata < idatamax:
            _, fidx, _, _ = self._model.data[idata]
            if fidx >= 0:
                iddata = self._vm.firstdlines[idata]
                break
            idata += direction
        # Remember current offset to be able to return a side-effect
        # description
        prev_offset = self._vm.voffset
        self.set_v_offset(iddata, True)
        if prev_offset == self._vm.voffset:
            return '(END)' if direction > 0 else '(BEGIN)'
        return 'Next match' if direction > 0 else 'Previous match'

    def search(self, keyword):
        '''Searches for the given keyword. This function assumes the view
        currently has no filter.'''
        assert not self.has_filters()
        if len(keyword) > 0:
            self._config.only_matching = False
            self.push_keyword(keyword, True)
            self._vscroll_to_match(True, 1)

    def _vscroll_to_next_match(self):
        return self._vscroll_to_match(False, 1)

    def _vscroll_to_prev_match(self):
        return self._vscroll_to_match(False, -1)

    def _vpagescroll(self, delta):
        self._vscroll(delta * self._max_visible_lines_count)

    def execute(self, command):
        '''Executes the given command.'''
        dispatch = {
            TextViewCommand.GO_UP:                 lambda: self._vscroll(-1),
            TextViewCommand.GO_DOWN:               lambda: self._vscroll(1),
            TextViewCommand.GO_LEFT:               lambda: self._hscroll(-1),
            TextViewCommand.GO_RIGHT:              lambda: self._hscroll(1),
            TextViewCommand.GO_HOME:               lambda: self.set_v_offset(0, True),
            TextViewCommand.GO_END:                lambda: self.set_v_offset(sys.maxsize, True),
            TextViewCommand.GO_NPAGE:              lambda: self._vpagescroll(1),
            TextViewCommand.GO_PPAGE:              lambda: self._vpagescroll(-1),
            TextViewCommand.GO_SLEFT:              lambda: self._hscroll(-20),
            TextViewCommand.GO_SRIGHT:             lambda: self._hscroll(20),
            TextViewCommand.POP_FILTER:            self._pop_filter,
            TextViewCommand.POP_KEYWORD:           self._pop_keyword,
            TextViewCommand.VSCROLL_TO_NEXT_MATCH: self._vscroll_to_next_match,
            TextViewCommand.VSCROLL_TO_PREV_MATCH: self._vscroll_to_prev_match,
            TextViewCommand.TOGGLE_ONLY_MATCHING:  self._toggle_only_matching,
            TextViewCommand.TOGGLE_LINE_NUMBERS:   self._toggle_line_numbers,
            TextViewCommand.TOGGLE_WRAP:           self._toggle_wrap,
            TextViewCommand.TOGGLE_BULLETS:        self._toggle_bullets,
            TextViewCommand.TOGGLE_SHOW_SPACES:    self._toggle_show_spaces,
            TextViewCommand.NEXT_COLORIZE_MODE:    self._next_colorize_mode,
            TextViewCommand.TOGGLE_IGNORE_CASE:    self._toggle_ignore_case,
            TextViewCommand.NEXT_PALETTE:          self._next_palette,
        }
        assert command in dispatch, f'command {command}'
        return dispatch[command]()

HELP = f'''  ~ Searchf Help ~

  Version: {searchf.__VERSION__}
  More info: https://github.com/human3/searchf

  Utility to interactively search into line-oriented text files.

  General keys:
    q          Quit program, or close this help view
    ?          Show this help
    1 2 3      Switch to view #1, #2 or #3
    r          Reload file
    t          Reload file and scroll to end (tail)

  Filters:
    f ENTER    Enter first keyword of a new filter
    F          Pop top level filter
    + =        Add a new keyword to current filter
    - _        Remove last keyword from filter

  Display mode:
    m          Show/hide only matching lines
    l          Show/hide line numbers
    k          Enable/disables line wrapping
    *          Show/hide diamonds at line starts (when wrapping)
    .          Enable/disable space displaying as bullets
    c          Cycle/change color palette
    h          Cycle/change keyword colorization mode
    i          Toggle whether or not current filter ignores case

  Navigation:
    SPACE      Scroll down a page
    b          Scroll back a page
    ARROWS     Scroll up/down/left/right (also wasd)
    <  g       Scroll to the top
    >  G       Scroll to the bottom
    p          Scroll to previous matching line
    n          Scroll to next matching line
    TAB  ^g    Goto line number
    /          Start a search, kinda like "less", but only if
               there are currently no filter defined...

Type 'q' to close this help'''

class DebugView:
    '''Displays few debug lines, convenient to debug layout while curses running.'''
    def __init__(self, scr, size, position):
        self._scr = scr
        self._lines = []
        self._size = size
        h, w = size
        y, x = position
        self._win = curses.newwin(h, w, y, x)

    def draw(self):
        '''Draws the debug view on the screen'''
        _, w = self._size
        for i, line in enumerate(self._lines):
            try:
                self._win.addstr(i, 0, f'{line:<{w}}')
            except curses.error:
                pass

        self._win.refresh()

    def out(self, *argv):
        '''Outputs the given arg to the debug view.'''
        assert self._scr
        h, _ = self._size
        self._lines.append(*argv)
        if len(self._lines) > h:
            self._lines.pop(0)
        self.draw()

class Views:
    '''Aggregates all views, controlling which ones are visible, handling
    key presses and command dispatching.'''
    def __init__(self):
        self.debug = None
        self._scr = None
        self._path = None
        self._content = []
        self._current = -1
        self._hidden_view = -1
        self._y_get_text = 0

    def _layout(self):
        assert self._scr
        scr = self._scr
        maxh, maxw = get_max_yx(scr)
        view_lines_count = maxh - 1
        x = 0
        y = 0

        if USE_DEBUG:
            dbg_size = (10, maxw)
            self.debug = DebugView(scr, dbg_size, (y, x))
            # Just add padding to expose layout issues in the app
            padding = 3
            maxh = max(0, maxh - (2 * padding + dbg_size[0]))
            maxw = max(0, maxw - 2 * padding)
            view_lines_count = maxh
            x = padding
            y = dbg_size[0] + padding

        for v in self._content:
            v.layout(view_lines_count, maxw, y, x)

        y += view_lines_count
        self._y_get_text = y

    def _set_view(self, idx):
        assert 0 <= idx < len(self._content)
        if self._current != idx:
            self._current = idx
            self._content[idx].show()
        return self._content[idx].name()

    def _reload(self, scroll_to):
        with open(self._path, encoding='utf-8') as f:
            lines = f.readlines()
            for i, v in enumerate(self._content):
                if i == len(self._content) - 1:
                    v.set_lines(HELP.split('\n'))
                else:
                    v.set_lines(lines)
                    v.set_v_offset(scroll_to, False)
        self._content[self._current].draw()

    def create(self, scr, path):
        '''Creates all views in the given screen, and loads the content from
        the given file.'''
        self._scr = scr
        self._path = path
        self._content.clear()
        self._content.append(TextView(scr, 'View 1', path))
        self._content.append(TextView(scr, 'View 2', path))
        self._content.append(TextView(scr, 'View 3', path))
        self._content.append(TextView(scr, 'Help', 'Help'))
        self._layout()
        self._reload(0)
        self._set_view(0)

    def get_text(self, prompt):
        '''Prompts user to enter some text.'''
        return get_text(self._scr, self._y_get_text, 0, prompt)

    def _get_keyword(self):
        return self.get_text('Keyword: ')

    def try_start_search(self):
        '''Tries to initiate a less like search.'''
        v = self._content[self._current]
        if not v.has_filters():
            t = self._get_keyword()
            v.search(t)

    def handle_key(self, key):
        '''Handles the given key, propagating it to the proper view.'''

        def help_view_push():
            self._hidden_view = self._current
            return self._set_view(3)

        def help_view_pop():
            idx = self._hidden_view
            self._hidden_view = -1
            return self._set_view(idx)

        # Local functions redirecting to current view v
        v = self._content[self._current]

        def new_keyword(new_filter):
            keyword = self._get_keyword()
            return v.push_keyword(keyword, new_filter)

        def goto_line():
            line_as_text = self.get_text('Enter line: ')
            return v.goto_line(line_as_text)

        # Map keys to simple text view commands that don't take any argument
        simple = {
            ord('F'):              TextViewCommand.POP_FILTER,
            curses.KEY_BACKSPACE:  TextViewCommand.POP_FILTER,
            ord('-'):              TextViewCommand.POP_KEYWORD,
            ord('_'):              TextViewCommand.POP_KEYWORD,
            ord('n'):              TextViewCommand.VSCROLL_TO_NEXT_MATCH,
            ord('p'):              TextViewCommand.VSCROLL_TO_PREV_MATCH,
            ord('m'):              TextViewCommand.TOGGLE_ONLY_MATCHING,
            ord('l'):              TextViewCommand.TOGGLE_LINE_NUMBERS,
            ord('k'):              TextViewCommand.TOGGLE_WRAP,
            ord('*'):              TextViewCommand.TOGGLE_BULLETS,
            ord('.'):              TextViewCommand.TOGGLE_SHOW_SPACES,
            ord('c'):              TextViewCommand.NEXT_PALETTE,
            ord('h'):              TextViewCommand.NEXT_COLORIZE_MODE,
            ord('i'):              TextViewCommand.TOGGLE_IGNORE_CASE,
            curses.KEY_UP:         TextViewCommand.GO_UP,
            ord('w'):              TextViewCommand.GO_UP,
            curses.KEY_DOWN:       TextViewCommand.GO_DOWN,
            ord('s'):              TextViewCommand.GO_DOWN,
            curses.KEY_LEFT:       TextViewCommand.GO_LEFT,
            ord('a'):              TextViewCommand.GO_LEFT,
            curses.KEY_RIGHT:      TextViewCommand.GO_RIGHT,
            ord('d'):              TextViewCommand.GO_RIGHT,
            curses.KEY_HOME:       TextViewCommand.GO_HOME,
            ord('g'):              TextViewCommand.GO_HOME,
            ord('<'):              TextViewCommand.GO_HOME,
            curses.KEY_END:        TextViewCommand.GO_END,
            ord('G'):              TextViewCommand.GO_END,
            ord('>'):              TextViewCommand.GO_END,
            curses.KEY_NPAGE:      TextViewCommand.GO_NPAGE,
            ord(' '):              TextViewCommand.GO_NPAGE,
            curses.KEY_PPAGE:      TextViewCommand.GO_PPAGE,
            ord('b'):              TextViewCommand.GO_PPAGE,
            curses.KEY_SLEFT:      TextViewCommand.GO_SLEFT,
            ord('A'):              TextViewCommand.GO_SLEFT,
            curses.KEY_SRIGHT:     TextViewCommand.GO_SRIGHT,
            ord('D'):              TextViewCommand.GO_SRIGHT,
        }

        # Map keys to other more complex commands taking arguments
        dispatch = {
            ord('1'):          lambda: self._set_view(0),
            ord('2'):          lambda: self._set_view(1),
            ord('3'):          lambda: self._set_view(2),
            ord('?'):          help_view_push,
            ord('f'):          lambda: new_keyword(True),
            ord('\n'):         lambda: new_keyword(True),
            ord('r'):          lambda: self._reload(0),
            ord('t'):          lambda: self._reload(sys.maxsize),
            ord('+'):          lambda: new_keyword(False),
            ord('='):          lambda: new_keyword(False),
            ord('/'):          self.try_start_search,
            curses.ascii.TAB:  goto_line,
            7:                 goto_line,
        }

        intersection = simple.keys() & dispatch.keys()
        assert len(intersection) == 0, f'Some keys are mapped multiple times {intersection}'
        status = ''

        # If help is shown, we hijack keys closing the view but forward all other keys
        # as if it is a regular view (which makes help searchable like a file...)
        if self._hidden_view >= 0 and key in (ord('q'), ord('Q'), curses.ascii.ESC):
            help_view_pop()
        elif key in simple:
            status = v.execute(simple[key])
        elif key in dispatch:
            status = dispatch[key]()
        else:
            return False, 'Unknown key (? for help, q to quit)'

        return True, status

views = Views()

def debug(*argv):
    '''Function to output a debug string onto the curses managed screen.'''
    if views.debug:
        views.debug.out(*argv)

def main_loop(scr, path):
    '''Main curses entry point.'''
    init_colors()
    scr.refresh() # Must be call once on empty screen?
    views.create(scr, path)

    max_y, max_x = get_max_yx(scr)

    status = ''
    status_x = max(0, min(10, max_x - 50)) # allow for 50 char of status
    status_y = max_y - 1

    while True:
        scr.refresh()
        scr.move(status_y, 0)
        try:
            key = get_ch(scr)
        except KeyboardInterrupt:
            break
        # debug(f'Key {key}')
        if key == curses.KEY_RESIZE:
            raise Exception('Sorry, resizing is not supported')

        clear(scr, status_y, status_x, len(status))
        handled, status = views.handle_key(key)
        if not handled and key in (ord('q'), ord('Q')):
            break
        if not status:
            status = ''
        scr.addstr(status_y, status_x, status[:max_x-1])

def init_env():
    '''Initialize environment and return argument parser'''
    # https://stackoverflow.com/questions/27372068/why-does-the-escape-key-have-a-delay-in-python-curses
    os.environ.setdefault('ESCDELAY', '25')

    parser = argparse.ArgumentParser(
        description='Console application to search into text files and highlight keywords.',
        epilog='Press ? in the application for more information, or go to\
        https://github.com/human3/searchf')
    parser.add_argument('file')
    return parser

def main():
    '''Application entry point'''
    parser = init_env()
    args = parser.parse_args()
    curses.wrapper(main_loop, args.file)

if __name__ == '__main__':
    main()
