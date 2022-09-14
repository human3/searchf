'''https://github.com/human3/searchf'''

# pylint: disable=invalid-name
# pylint: disable=too-many-instance-attributes
# pylint: disable=too-many-arguments
# pylint: disable=no-member

from curses.textpad import Textbox
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple

import argparse
import curses
import curses.ascii
import os
import re
import sys
import copy

from . import __version__
from . import utils
from . import enums
from . import models
from . import segments
from . import colors


# Changes layout to show a debug window in which debug() function will output
USE_DEBUG = False

# Do not use curses.A_BOLD on Windows as it just renders horribly when highlighting
USE_BOLD = 0 if sys.platform == 'win32' else curses.A_BOLD

StatusText = str

STATUS_EMPTY = ''

Size = Tuple[int, int]

def get_max_yx(scr) -> Size:
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


def _get_text(scr, y, x, prompt, handler, text):
    scr.addstr(y, x, prompt)
    x += len(prompt)
    editwin = curses.newwin(1, 30, y, x)
    scr.refresh()
    box = Textbox(editwin)
    for c in text:
        box.do_command(ord(c))
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


def get_text(scr, y, x, prompt, text):
    '''Prompts user to enter some text.'''
    def handle(box):
        box.edit(validate=_validate)
    return _get_text(scr, y, x, prompt, handle, text)


def clear(scr, y, x, length):
    '''Prints "length" spaces at the given position'''
    _, maxw = get_max_yx(scr)
    blank = f'{" ":>{length}}'
    scr.addstr(y, x, blank[:maxw-(x+1)])
    scr.move(y, x)


class ViewConfig:
    '''Holds the configuration of a view, like filters to use or the
    display modes, typically changed by end users to match their
    need. Does not contain any data related to file content. Should be
    serialized at some point to persist somewhere and get re-used accross
    session.
    '''
    line_numbers: bool = True
    wrap: bool = True
    bullets: bool = False
    reverse_matching: bool = False
    line_visibility: enums.LineVisibility = enums.LineVisibility.ALL
    show_all_lines: bool = True
    show_spaces: bool = False
    colorize_mode: enums.ColorizeMode = enums.ColorizeMode.KEYWORD_HIGHLIGHT
    palette_index: int = 0

    def __init__(self) -> None:
        self.filters: List[models.Filter] = []

    def get_filters_count(self) -> int:
        '''Returns the number of filters currently defined'''
        return len(self.filters)

    def has_filters(self) -> bool:
        '''Returns whether or not there is any filter'''
        return len(self.filters) > 0

    def top_filter(self) -> models.Filter:
        '''Returns top level filter (most recently added)'''
        count = len(self.filters)
        assert count > 0
        return self.filters[count-1]

    def push_filter(self, f: models.Filter) -> None:
        '''Pushes the given filter'''
        self.filters.append(f)

    def swap_filters(self, i, j) -> None:
        '''Swaps the given filters'''
        count = len(self.filters)
        assert 0 <= i < count
        assert 0 <= j < count
        self.filters[i], self.filters[j] = self.filters[j], self.filters[i]

    def get_color_pair(self, filter_index: int) -> StatusText:
        '''Returns the id of the color pair associated with given filter index'''
        return colors.get_color_pair(self.palette_index, filter_index)

    def cycle_palette(self, forward: bool) -> int:
        '''Select the next palette in the given direction'''
        self.palette_index = colors.cycle_palette_index(self.palette_index, forward)
        return self.palette_index


def bool_to_text(value: bool) -> str:
    '''Converts a boolean value to text.'''
    return 'enabled' if value else 'disabled'


CASE_COL_TEXTS = ['Case', 'ignored', 'sensitive']
CASE_COL_LEN = len(max(CASE_COL_TEXTS, key=len))

SHOWN_COL_TEXTS = ['Shown', 'no', 'yes']
SHOWN_COL_LEN = len(max(SHOWN_COL_TEXTS , key=len))


class PrefixInfo(NamedTuple):
    '''Line prefix infos.'''
    length: int       # Total length of prefix
    digit_count: int  # Number of digits of the largest line number
    separator: str    # Separator between things on left (line number,
                      # bullet), and things on right (line)


class TextView:
    '''Display selected content of a file, using filters and keyword to
    highlight specific text.'''
    def __init__(self, scr, name: str, path: str) -> None:
        self._model: models.Model = models.Model()
        self._vm: models.ViewModel = models.ViewModel()
        self._config: ViewConfig = ViewConfig()
        self._scr = scr
        self._name: str = name
        self._basename = os.path.basename(path)
        self._max_visible_lines_count = 0
        self._win: Optional[curses._CursesWindow] = None
        self._size: Size = (0, 0)
        self._ruler: str = ''

    def get_config(self) -> ViewConfig:
        '''Gets the config'''
        return self._config

    def name(self) -> str:
        '''Gets the name of the view.'''
        return self._name

    def layout(self, h: int, w: int, y: int, x: int) -> None:
        '''Sets dimension of the view. Must be call before everything and
        only once (no dynamic layout supported)'''

        # _size stores number of lines and columns available to draw content
        self._size = (h, w)
        self._win = curses.newwin(h, w, y, x)

    def _get_prefix_info(self) -> PrefixInfo:
        if self._config.line_numbers:
            number_length = self._model.line_number_length()
            sep = ' │ '
        elif self._config.wrap:
            number_length = 0
            sep = '◆ ' if self._config.bullets else ''  # curses.ACS_DIAMOND
        else:
            number_length = 0
            sep = ''
        return PrefixInfo(number_length + len(sep), number_length, sep)

    def _draw_bar(self, y):
        '''Draws the status bar and the filter stack underneath'''

        _, w = self._size
        style = curses.color_pair(colors.BAR_COLOR_PAIR_ID)
        self._win.hline(y, 0, curses.ACS_HLINE, w, style)

        if not self._config.has_filters():
            self._win.addstr(' No filter ', style)
        else:
            self._win.addstr(f'{self._model.hits_count():>8}', style)
            self._win.addstr(f' | {"Case":^{CASE_COL_LEN}}', style)
            self._win.addstr(f' | {"Shown":^{SHOWN_COL_LEN}}', style)
            self._win.addstr(' | Keywords ', style)

        # Print from right to left
        def move_left_for(x, text):
            return max(0, x - len(text) - 1)

        x = w
        text = f' {self._name} '
        x = move_left_for(x, text)
        self._win.addstr(y, x, text, style)

        text = ''.ljust(5)  # voffest_desc is not always shown, but at most 5 char long
        x = move_left_for(x, text)
        if len(self._vm.voffset_desc) > 0:
            text = f' {self._vm.voffset_desc:>3} '
            self._win.addstr(y, x, text, style)

        text = f' {self._model.line_count()} lines '
        x = move_left_for(x, text)
        self._win.addstr(y, x, text, style)

        text = f' {self._basename} '
        x = move_left_for(x, text)
        self._win.addstr(y, x, text, style | USE_BOLD)

        assert len(self._model.hits) == self._config.get_filters_count()
        for i, f in enumerate(self._config.filters):
            x = 0
            y += 1
            self._win.addstr(y, 0, f'{self._model.hits[i]:>8}')
            text = CASE_COL_TEXTS[1 if f.ignore_case else 2]
            self._win.addstr(f' | {text:^{CASE_COL_LEN}}')
            text = SHOWN_COL_TEXTS[1 if f.hiding else 2]
            self._win.addstr(f' | {text:^{SHOWN_COL_LEN}} | ')
            text = ' AND '.join(f.keywords)
            color = 0 if f.hiding else self._config.get_color_pair(i)
            self._win.addstr(text, color)

    def _draw_prefix(self, y, prefix_info, line_idx, color):
        _, w_index, sep = prefix_info
        if w_index > 0:
            assert line_idx >= 0
            self._win.addstr(y, 0, f'{line_idx:>{w_index}}', color | USE_BOLD)
        self._win.addstr(y, w_index, f'{sep}')

    def _draw_content(self, position, text, matching_segments, offset, color):
        y, x = position
        vend = offset + self._vm.size[1]
        if self._config.show_spaces:
            text = text.replace(' ', '·')  # Note: this is curses.ACS_BULLET
        if self._config.colorize_mode == enums.ColorizeMode.LINE:
            text = text[offset:vend]
            text = f'{text:<{self._vm.size[1]}}'
            self._win.addnstr(y, x, text, self._size[1], color)
        else:
            for match, start, end in segments.iterate(offset, vend, matching_segments):
                assert start < end
                c = color if match else 0
                length = end - start
                self._win.addnstr(y, x, text[start:end], length, c)
                x += length

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
            if line_idx == models.RULER_INDEX:
                self._win.addstr(y, 0, self._ruler)
                continue
            color = self._config.get_color_pair(filter_idx)
            # If offset is not 0, this means the original content line
            # is being wrapped on to multiple lines on the screen. We
            # only draw the prefix on the first line, which has offset
            # 0.
            if offset == 0:
                self._draw_prefix(y, prefix_info, line_idx, color)
            offset += self._vm.hoffset
            self._draw_content((y, prefix_info.length), text, matching_segments, offset, color)

        self._draw_bar(self._max_visible_lines_count)

        self._win.refresh()

    def _layout(self, redraw):
        '''Propagate layout changes: evaluates the available space and calls
layout of the view model.

        '''

        # Compute space available for file content
        h, w = self._size
        self._ruler = '-' * w
        prefix_len, _, _ = self._get_prefix_info()
        h = max(0, h - 1 - self._config.get_filters_count())
        w = max(0, w - prefix_len)

        self._vm.layout(h, w, self._model.data, self._config.wrap)
        self._max_visible_lines_count = h

        # Try preserve current voffset, but make sure we comply with
        # constraints which might just have changed.
        self.set_v_offset(self._vm.voffset, False)

        assert self._vm.voffset == 0 or self._vm.voffset < self._vm.lines_count()

        if redraw:
            self.draw()

    def _sync(self, redraw: bool) -> None:
        self._model.sync(self._config.filters, self._config.line_visibility)
        self._layout(redraw)

    def set_config(self, config: ViewConfig) -> None:
        '''Sets the configuration.'''
        self._config = config
        self._sync(False)

    def set_lines(self, lines: List[str]) -> None:
        '''Sets the content of this view. Assumes the view is offscreen and does
        not trigger a redraw.'''
        self._model.set_lines(lines)
        self._sync(False)

    def _pop_filter(self) -> StatusText:
        if self._config.has_filters():
            self._config.filters.pop()
            self._sync(True)
            return 'Filter removed'
        return 'No filter to remove'

    def push_keyword(self, keyword: str, new_filter: bool) -> StatusText:
        '''Pushes a new keyword in current top level filter (if new_filter is
        False) or in a brand new filter (if new_filter is True).'''
        if len(keyword) <= 0:
            return 'No keyword added'
        try:
            re.compile(keyword)
        except re.error:
            return 'Invalid python regex pattern'
        if not self._config.has_filters():
            new_filter = True  # Force a new filter since we have none
        if new_filter:
            f = models.Filter()
            f.ignore_case = keyword.lower() == keyword
            self._config.push_filter(f)

        self._config.top_filter().add(keyword)
        self._sync(True)
        return 'New filter created' if new_filter else 'Keyword added'

    def _pop_keyword(self) -> StatusText:
        if not self._config.has_filters():
            return 'No keyword to remove'
        f = self._config.top_filter()
        k_count = len(f.keywords)
        if k_count <= 1:
            return self._pop_filter()
        f.pop()
        self._sync(True)
        return 'Keyword removed'

    def get_last_keyword(self) -> Tuple[int, Optional[str]]:
        '''Returns total number of keywords in top level filter (0 if none),
        and the keyword that was last entered by user.'''
        if not self._config.has_filters():
            return 0, ''
        f = self._config.top_filter()
        return f.get_count_and_last_keyword()

    def _toggle_line_numbers(self) -> StatusText:
        self._config.line_numbers = not self._config.line_numbers
        self._layout(True)
        return f'Line numbers {bool_to_text(self._config.line_numbers)}'

    def _toggle_wrap(self) -> StatusText:
        self._config.wrap = not self._config.wrap
        self._layout(True)
        return f'Line wrapping {bool_to_text(self._config.wrap)}'

    def _toggle_bullets(self) -> StatusText:
        self._config.bullets = not self._config.bullets
        self._layout(True)
        return f'Bullets {bool_to_text(self._config.bullets)}'

    def _toggle_show_spaces(self) -> StatusText:
        self._config.show_spaces = not self._config.show_spaces
        self.draw()
        return f'Show spaces {bool_to_text(self._config.show_spaces)}'

    def _cycle_colorize_mode(self, forward: bool) -> StatusText:
        f = enums.ColorizeMode.get_next if forward else enums.ColorizeMode.get_prev
        self._config.colorize_mode = f(self._config.colorize_mode)
        self.show()
        return f'Colorize mode: {self._config.colorize_mode}'

    def _cycle_line_visibility(self, forward: bool) -> StatusText:
        f = enums.LineVisibility.get_next if forward else enums.LineVisibility.get_prev
        self._config.line_visibility = f(self._config.line_visibility)
        self._sync(True)
        return f'{self._config.line_visibility}'

    def _toggle_ignore_case(self) -> StatusText:
        if not self._config.has_filters():
            return 'Cannot change case sentitivity (no keyword)'
        f = self._config.top_filter()
        f.ignore_case = not f.ignore_case
        self._sync(True)
        return f'Ignore case set to {f.ignore_case}'

    def _toggle_hiding(self) -> StatusText:
        if not self._config.has_filters():
            return 'Cannot change case sentitivity (no keyword)'
        f = self._config.top_filter()
        f.hiding = not f.hiding
        self._sync(True)
        action = 'hidden' if f.hiding else 'shown'
        return f'Lines matching filter are now {action}'

    def _apply_palette_and_draw(self) -> None:
        colors.apply_palette(self._config.palette_index,
                             self._config.colorize_mode == enums.ColorizeMode.KEYWORD_HIGHLIGHT)
        self.draw()

    def show(self) -> None:
        '''Shows the view, after it was hidden by another one'''
        self._apply_palette_and_draw()

    def _cycle_palette(self, forward: bool) -> StatusText:
        idx = self._config.cycle_palette(forward)
        self._apply_palette_and_draw()
        return f'Using color palette #{idx}'

    def _set_h_offset(self, offset: int) -> StatusText:
        if self._vm.set_h_offset(offset):
            self.draw()
        return STATUS_EMPTY

    def set_v_offset(self, offset: int, redraw: int) -> StatusText:
        '''Sets the vertical offset of the view.'''
        if self._vm.set_v_offset(offset) and redraw:
            self.draw()
        return STATUS_EMPTY

    def _hscroll(self, delta: int) -> StatusText:
        self._set_h_offset(self._vm.hoffset + delta)
        return STATUS_EMPTY

    def _vscroll(self, delta: int) -> StatusText:
        self.set_v_offset(self._vm.voffset + delta, True)
        return STATUS_EMPTY

    def goto_line(self, line_text: str) -> StatusText:
        '''Makes sure the given line is visible, making it the first line on
        the screen unless that would make last line of the file not
        displayed at the bottom.'''
        try:
            line = int(line_text)
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

    def has_filters(self) -> bool:
        '''Returns whether the view has any filter or not.'''
        return self._config.has_filters()

    def swap_filters(self) -> StatusText:
        '''Swaps the top 2 filters'''
        count = self._config.get_filters_count()
        if self._config.get_filters_count() < 2:
            return 'Not enough filters'
        self._config.swap_filters(count - 1, count - 2)
        # We call _sync to recompute everything. We could just go through the rendering data
        # and just swap the filter indexes...
        self._sync(True)
        return 'Filters swapped'

    def _vscroll_to_match(self, starting: bool, direction: int) -> StatusText:
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

    def search(self, keyword: str) -> StatusText:
        '''Searches for the given keyword. This function assumes the view
        currently has no filter.'''
        assert not self.has_filters()
        if len(keyword) > 0:
            self._config.reverse_matching = False
            self._config.line_visibility = enums.LineVisibility.ALL
            self.push_keyword(keyword, True)
            self._vscroll_to_match(True, 1)
        return STATUS_EMPTY

    def _vpagescroll(self, delta: int) -> StatusText:
        self._vscroll(delta * self._max_visible_lines_count)
        return STATUS_EMPTY

    def execute(self, command: enums.TextViewCommand) -> StatusText:
        '''Executes the given command.'''
        dispatch = {
            enums.TextViewCommand.GO_UP:                 lambda: self._vscroll(-1),
            enums.TextViewCommand.GO_DOWN:               lambda: self._vscroll(1),
            enums.TextViewCommand.GO_LEFT:               lambda: self._hscroll(-1),
            enums.TextViewCommand.GO_RIGHT:              lambda: self._hscroll(1),
            enums.TextViewCommand.GO_HOME:               lambda: self.set_v_offset(0, True),
            enums.TextViewCommand.GO_END:                lambda: self.set_v_offset(
                sys.maxsize, True),
            enums.TextViewCommand.GO_NPAGE:              lambda: self._vpagescroll(1),
            enums.TextViewCommand.GO_PPAGE:              lambda: self._vpagescroll(-1),
            enums.TextViewCommand.GO_SLEFT:              lambda: self._hscroll(-20),
            enums.TextViewCommand.GO_SRIGHT:             lambda: self._hscroll(20),
            enums.TextViewCommand.VSCROLL_TO_NEXT_MATCH: lambda: self._vscroll_to_match(
                False, 1),
            enums.TextViewCommand.VSCROLL_TO_PREV_MATCH: lambda: self._vscroll_to_match(
                False, -1),
            enums.TextViewCommand.NEXT_COLORIZE_MODE:    lambda: self._cycle_colorize_mode(True),
            enums.TextViewCommand.PREV_COLORIZE_MODE:    lambda: self._cycle_colorize_mode(False),
            enums.TextViewCommand.NEXT_PALETTE:          lambda: self._cycle_palette(True),
            enums.TextViewCommand.PREV_PALETTE:          lambda: self._cycle_palette(False),
            enums.TextViewCommand.NEXT_LINE_VISIBILITY:  lambda: self._cycle_line_visibility(True),
            enums.TextViewCommand.PREV_LINE_VISIBILITY:  lambda: self._cycle_line_visibility(False),
            enums.TextViewCommand.POP_FILTER:            self._pop_filter,
            enums.TextViewCommand.POP_KEYWORD:           self._pop_keyword,
            enums.TextViewCommand.TOGGLE_LINE_NUMBERS:   self._toggle_line_numbers,
            enums.TextViewCommand.TOGGLE_WRAP:           self._toggle_wrap,
            enums.TextViewCommand.TOGGLE_BULLETS:        self._toggle_bullets,
            enums.TextViewCommand.TOGGLE_SHOW_SPACES:    self._toggle_show_spaces,
            enums.TextViewCommand.TOGGLE_IGNORE_CASE:    self._toggle_ignore_case,
            enums.TextViewCommand.TOGGLE_HIDING:         self._toggle_hiding,
            enums.TextViewCommand.SWAP_FILTERS:          self.swap_filters,
        }
        assert command in dispatch, f'command {command}'
        return dispatch[command]()


HELP = f'''  ~ Searchf Help ~

  Version: {__version__}
  More info: https://github.com/human3/searchf

  Utility to interactively search for keywords in text files.

  General keys:
    q          Quit program, or close this help view
    ?          Show this help
    1 2 3      Switch to view #1, #2 or #3
    ! @ #      Switch to view #1, #2 or #3 with current filters
    r          Reload file
    t          Reload file and scroll to end (tail)

  Filters:
    f ENTER    Enter first keyword of a new filter
    F          Pop top level filter
    + =        Add a new keyword to current filter
    - _        Remove last keyword from filter
    e          Edit last keyword
    s          Swap the top 2 filters
    i          Toggle whether or not current filter ignores case
    x          Toggle whether or not lines matching current filter are shown

  Display modes:
    l          Toggles line numbers visibility
    k          Toggles line wrapping
    *          Toggles diamonds visibility at line starts (when wrapping)
    .          Enable/disable space displaying as bullets
    c/C        Next/previous color palette
    h/H        Next/previous highlight and colorization mode
    m/M        Next/previous line visibility mode

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
    def __init__(self, scr, size: Size, position: Tuple[int, int]) -> None:
        self._scr = scr
        self._lines: List[str] = []
        self._size = size
        h, w = size
        y, x = position
        self._win = curses.newwin(h, w, y, x)

    def draw(self) -> None:
        '''Draws the debug view on the screen'''
        _, w = self._size
        for i, line in enumerate(self._lines):
            try:
                self._win.addstr(i, 0, f'{line:<{w}}')
            except curses.error:
                pass

        self._win.refresh()

    def out(self, *argv) -> None:
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
    def __init__(self) -> None:
        self.debug = None
        self._scr = None
        self._path: str = ''
        self._content: List[TextView] = []
        self._current: int = -1
        self._hidden_view: int = -1
        self._y_get_text: int = 0

    def _layout(self) -> None:
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

    def _set_view(self, idx: int, propagate_config: bool) -> StatusText:
        assert 0 <= idx < len(self._content)
        if self._current != idx:
            config = self._content[self._current].get_config()
            self._current = idx
            if propagate_config:
                self._content[idx].set_config(copy.deepcopy(config))
            self._content[idx].show()
        return f'Switched to {self._content[idx].name()}'

    def _help_view_push(self) -> StatusText:
        self._hidden_view = self._current
        return self._set_view(3, False)

    def _help_view_pop(self) -> StatusText:
        idx = self._hidden_view
        self._hidden_view = -1
        return self._set_view(idx, False)

    def _reload(self, scroll_to: int) -> StatusText:
        with open(self._path, encoding='utf-8') as f:
            lines = f.readlines()
            for i, v in enumerate(self._content):
                if i == len(self._content) - 1:
                    v.set_lines(HELP.split('\n'))
                else:
                    v.set_lines(lines)
                    v.set_v_offset(scroll_to, False)
        self._content[self._current].draw()
        return 'File reloaded'

    def create(self, scr, path: str) -> None:
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
        self._set_view(0, False)

    def get_text(self, prompt: str, text: Optional[str]) -> str:
        '''Prompts user to enter or edit some text.'''
        return get_text(self._scr, self._y_get_text, 0, prompt, text)

    def _get_keyword(self) -> str:
        return self.get_text('Keyword: ', '')

    def try_start_search(self) -> StatusText:
        '''Tries to initiate a less like search.'''
        v = self._content[self._current]
        if v.has_filters():
            return 'Cannot start search when filters already defined'
        t = self._get_keyword()
        return v.search(t)

    def handle_key(self, key) -> Tuple[bool, StatusText]:
        '''Handles the given key, propagating it to the proper view.'''

        # Local functions redirecting to current view v
        v = self._content[self._current]

        def new_keyword(new_filter) -> StatusText:
            keyword = self._get_keyword()
            return v.push_keyword(keyword, new_filter)

        def goto_line() -> StatusText:
            line_as_text = self.get_text('Enter line: ', '')
            return v.goto_line(line_as_text)

        def edit_keyword() -> StatusText:
            count, keyword = v.get_last_keyword()
            if count <= 0:
                return 'No keyword to edit'
            keyword = self.get_text('Edit: ', keyword)
            if len(keyword) <= 0:
                return 'No change made'
            v.execute(enums.TextViewCommand.POP_KEYWORD)
            v.push_keyword(keyword, count == 1)
            return 'Keyword updated'

        # Map keys to simple text view commands that don't take any
        # argument and that can be directly handled by calling v.execute()
        keys_to_command = {
            ord('F'):              enums.TextViewCommand.POP_FILTER,
            curses.KEY_BACKSPACE:  enums.TextViewCommand.POP_FILTER,
            ord('-'):              enums.TextViewCommand.POP_KEYWORD,
            ord('_'):              enums.TextViewCommand.POP_KEYWORD,
            ord('n'):              enums.TextViewCommand.VSCROLL_TO_NEXT_MATCH,
            ord('p'):              enums.TextViewCommand.VSCROLL_TO_PREV_MATCH,
            ord('l'):              enums.TextViewCommand.TOGGLE_LINE_NUMBERS,
            ord('k'):              enums.TextViewCommand.TOGGLE_WRAP,
            ord('*'):              enums.TextViewCommand.TOGGLE_BULLETS,
            ord('.'):              enums.TextViewCommand.TOGGLE_SHOW_SPACES,
            ord('c'):              enums.TextViewCommand.NEXT_PALETTE,
            ord('C'):              enums.TextViewCommand.PREV_PALETTE,
            ord('h'):              enums.TextViewCommand.NEXT_COLORIZE_MODE,
            ord('H'):              enums.TextViewCommand.PREV_COLORIZE_MODE,
            ord('m'):              enums.TextViewCommand.NEXT_LINE_VISIBILITY,
            ord('M'):              enums.TextViewCommand.PREV_LINE_VISIBILITY,
            ord('i'):              enums.TextViewCommand.TOGGLE_IGNORE_CASE,
            ord('x'):              enums.TextViewCommand.TOGGLE_HIDING,
            curses.KEY_UP:         enums.TextViewCommand.GO_UP,
            ord('w'):              enums.TextViewCommand.GO_UP,
            curses.KEY_DOWN:       enums.TextViewCommand.GO_DOWN,
            ord('s'):              enums.TextViewCommand.GO_DOWN,
            curses.KEY_LEFT:       enums.TextViewCommand.GO_LEFT,
            ord('a'):              enums.TextViewCommand.GO_LEFT,
            curses.KEY_RIGHT:      enums.TextViewCommand.GO_RIGHT,
            ord('d'):              enums.TextViewCommand.GO_RIGHT,
            curses.KEY_HOME:       enums.TextViewCommand.GO_HOME,
            ord('g'):              enums.TextViewCommand.GO_HOME,
            ord('<'):              enums.TextViewCommand.GO_HOME,
            curses.KEY_END:        enums.TextViewCommand.GO_END,
            ord('G'):              enums.TextViewCommand.GO_END,
            ord('>'):              enums.TextViewCommand.GO_END,
            curses.KEY_NPAGE:      enums.TextViewCommand.GO_NPAGE,
            ord(' '):              enums.TextViewCommand.GO_NPAGE,
            curses.KEY_PPAGE:      enums.TextViewCommand.GO_PPAGE,
            ord('b'):              enums.TextViewCommand.GO_PPAGE,
            curses.KEY_SLEFT:      enums.TextViewCommand.GO_SLEFT,
            ord('A'):              enums.TextViewCommand.GO_SLEFT,
            curses.KEY_SRIGHT:     enums.TextViewCommand.GO_SRIGHT,
            ord('D'):              enums.TextViewCommand.GO_SRIGHT,
            ord('s'):              enums.TextViewCommand.SWAP_FILTERS,
        }

        # Map keys to custom functions used to handle more complex commands
        # like ones taking arguments
        keys_to_func = {
            ord('1'):          lambda: self._set_view(0, False),
            ord('2'):          lambda: self._set_view(1, False),
            ord('3'):          lambda: self._set_view(2, False),
            ord('!'):          lambda: self._set_view(0, True),
            ord('@'):          lambda: self._set_view(1, True),
            ord('#'):          lambda: self._set_view(2, True),
            ord('?'):          self._help_view_push,
            ord('e'):          edit_keyword,
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

        intersection = keys_to_command.keys() & keys_to_func.keys()
        assert len(intersection) == 0, f'Some keys are mapped multiple times {intersection}'
        status: StatusText = ''

        # If help is shown, we hijack keys closing the view but forward all other keys
        # as if it is a regular view (which makes help searchable like a file...)
        if self._hidden_view >= 0 and key in (ord('q'), ord('Q'), curses.ascii.ESC):
            self._help_view_pop()
        elif key in keys_to_command:
            status = v.execute(keys_to_command[key])
        elif key in keys_to_func:
            status = StatusText(keys_to_func[key]())
        else:
            return False, 'Unknown key (? for help, q to quit)'

        return True, status


views = Views()


def debug(*argv) -> None:
    '''Function to output a debug string onto the curses managed screen.'''
    if views.debug:
        views.debug.out(*argv)


def main_loop(scr, path: str) -> None:
    '''Main curses entry point.'''
    colors.init()
    scr.refresh()  # Must be call once on empty screen?
    views.create(scr, path)

    max_y, max_x = get_max_yx(scr)

    status = ''
    status_x = max(0, min(10, max_x - 50))  # allow for 50 char of status
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


def init_env() -> argparse.ArgumentParser:
    '''Initialize environment and return argument parser'''
    # https://stackoverflow.com/questions/27372068/why-does-the-escape-key-have-a-delay-in-python-curses
    os.environ.setdefault('ESCDELAY', '25')

    os.environ['TERM'] = 'screen-256color'

    parser = argparse.ArgumentParser(
        description='Console application to search into text files and highlight keywords.',
        epilog='Press ? in the application for more information, or go to\
        https://github.com/human3/searchf')
    parser.add_argument('file')
    return parser


def main() -> None:
    '''Application entry point'''
    parser = init_env()
    args = parser.parse_args()
    utils.wrapper(False, curses.wrapper, main_loop, args.file)


if __name__ == '__main__':
    main()
