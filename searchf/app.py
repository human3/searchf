'''https://github.com/human3/searchf'''

# This code tries to abide by the following principles:
# - Simplicity comes first
# - Don't Repeat Yourself (aka DRY)
# - no-use-before-define

# We want one letter variable name in simple functions.
# pylint: disable=invalid-name

# The no-member error fires on dynamically generated members of curses only, and
# nothing offending in our code, so disabling it...
# pylint: disable=no-member

from curses.textpad import Textbox
from enum import Enum, auto
import argparse
import curses
import math
import os
import re
import sys

import searchf
import searchf.segments as segments

# Changes layout to show a debug window in which debug() function will output
USE_DEBUG = False

BAR_COLOR_ID = 1 # Huge hack!! Must not match any index of any palette below
BAR_COLOR = 39 # 249

# https://stackoverflow.com/questions/18551558/how-to-use-terminal-color-palette-with-curses
PALETTES = [
    # Palettes working with dark background
    [
        197, # Red
        209, # Orange
        191, # Yellow
        47,  # Green
        34,  # Blue
        202, # Purple
        220, # Pink
    ],
    [
        202, # Purple
        34,  # Blue
        209, # Orange
        47,  # Green
        191, # Yellow
        197, # Red
        220, # Pink
    ],
    # Palettes working with light/clear backgrounds
    [
        2,   # Red
        209, # Orange
        4,   # Dark Yellow
        23,  # Green
        21,  # Blue
        130, # Purple
        7,   # Cyan?
    ],
    [
        130, # Purple
        21,  # Blue
        2,   # Red
        23,  # Green
        209, # Orange
        4,   # Dark Yellow
        7,   # Cyan?
    ],
]

def get_max_yx(scr):
    '''This function is a test artifact that wraps getmaxyx() from curses
so that we can overwrite it and test specific dimensions.'''
    return scr.getmaxyx()

def get_ch(scr):
    '''This function is a test artifact that wraps getch() from curses so
that we can overwrite it and inject keys while testing.'''
    return scr.getch()

def _get_text(scr, y, x, prompt, handler):
    scr.addstr(y, x, prompt)
    x += len(prompt)
    editwin = curses.newwin(1, 30, y, x)
    scr.refresh()
    box = Textbox(editwin)
    handler(box)
    text = box.gather().strip()
    editwin.clear()
    editwin.refresh()
    clear(scr, y, 0, len(prompt))
    return text if text else ''

def _box_edit(box):
    def validate(ch):
        if ch == curses.ascii.DEL:
            ch = curses.KEY_BACKSPACE
        elif ch == curses.ascii.ESC:
            raise EscapeInterrupt()
        return ch

    try:
        box.edit(validate=validate)
    except EscapeInterrupt:
        pass

def get_text(scr, y, x, prompt):
    '''Prompts user to enter some text.'''
    return _get_text(scr, y, x, prompt, _box_edit)

def clear(scr, y, x, length):
    '''Prints "length" spaces at the given position'''
    _, maxw = get_max_yx(scr)
    blank = f'{" ":>{length}}'
    scr.addstr(y, x, blank[:maxw-(x+1)])
    scr.move(y, x)

class EscapeInterrupt(Exception):
    '''Signals that Escape key has been pressed'''

class Filter:
    '''Represents a list of keywords ANDed together and matching properties'''
    ignore_case: bool = False

    def __init__(self):
        self.keywords = {}

    def add(self, kw):
        '''Adds given keyword to this filter'''
        self.keywords[kw] = None

    def pop(self):
        '''Removes most recently added keyword from this filter'''
        self.keywords.popitem()

class ViewConfig:
    '''Holds the configuration of a view'''
    # pylint: disable=too-many-instance-attributes
    line_numbers:  bool = False
    wrap:          bool = True
    bullets:       bool = False
    only_matching: bool = True
    show_spaces:   bool = False
    whole_line:    bool = False
    palette_index: int = 0

    def __init__(self):
        self.filters = []

    def has_filters(self):
        '''Returns whether or not there is any filter'''
        return len(self.filters) > 0

    def top_filter(self):
        '''Returns top level filter (most recently added)'''
        count = len(self.filters)
        assert count > 0
        return self.filters[count-1]

    def push_filter(self, f):
        '''Pushes the given filter'''
        self.filters.append(f)

    def get_color(self, fidx):
        '''Returns color associated with given filter index'''
        palette = PALETTES[self.palette_index]
        fidx = fidx % len(palette)
        return palette[fidx]

    def next_palette(self):
        '''Select the "next" palette'''
        self.palette_index = (self.palette_index + 1) % len(PALETTES)

class TextViewCommand(Enum):
    '''Simple commands accepted by TextView class, that do not take any argument.'''
    GO_UP                 = auto()
    GO_DOWN               = auto()
    GO_LEFT               = auto()
    GO_RIGHT              = auto()
    GO_HOME               = auto()
    GO_END                = auto()
    GO_NPAGE              = auto()
    GO_PPAGE              = auto()
    GO_SLEFT              = auto()
    GO_SRIGHT             = auto()
    POP_FILTER            = auto()
    POP_KEYWORD           = auto()
    VSCROLL_TO_NEXT_MATCH = auto()
    VSCROLL_TO_PREV_MATCH = auto()
    TOGGLE_ONLY_MATCHING  = auto()
    TOGGLE_LINE_NUMBERS   = auto()
    TOGGLE_WRAP           = auto()
    TOGGLE_BULLETS        = auto()
    TOGGLE_SHOW_SPACES    = auto()
    TOGGLE_WHOLE_LINE     = auto()
    TOGGLE_IGNORE_CASE    = auto()
    NEXT_PALETTE          = auto()

def bool_to_text(value):
    '''Converts a boolean value to text.'''
    return 'enabled' if value else 'disabled'

CASE_MODE_TEXT = ['ignored', 'sensitive']
CASE_MODE_LEN = len(max(CASE_MODE_TEXT, key=len))

class TextView:
    '''Display selected content of a file, using filters and keyword to
    highlight specific text.'''
    def __init__(self, scr, name, path):
        self._name = name
        self._path = path
        self._basename = os.path.basename(path)
        self._scr = scr
        self._config = ViewConfig()

        self._content_lines_count = 0
        self._h = 0
        self._w = 0
        self._win = None
        self._voffset = 0
        self._hoffset = 0
        self._voffset_desc = ''

        self._lines = [] # Content lines
        self._firstdlines = []
        self._data = []
        self._ddata = []
        self._hits = []
        self._w_text = 0

    def name(self):
        '''Gets the name of the view.'''
        return self._name

    def layout(self, h, w, y, x):
        '''Sets dimension of the view. Must be call before everything and
        only once (no dynamic layout supported)'''

        # _w and _h now store number of cols and lines available to draw content
        self._h = h
        self._w = w
        self._win = curses.newwin(h, w, y, x)

    def _get_prefix_info(self):
        '''Returns total length of prefix, the number of digits of the largest
line number and separator'''
        if self._config.line_numbers:
            number_length = math.floor(math.log10(len(self._lines))+1)
            sep = ' │ '
        elif self._config.wrap:
            number_length = 0
            sep = '◆ ' if self._config.bullets else '' # curses.ACS_DIAMOND
        else:
            number_length = 0
            sep = ''
        return number_length + len(sep), number_length, sep

    def _draw_bar(self, y):
        style = curses.color_pair(BAR_COLOR_ID)
        self._win.hline(y, 0, curses.ACS_HLINE, self._w, style)

        x = 1
        if not self._config.has_filters():
            text = ' No filter '
            self._win.addstr(y, x, text, style)
        else:
            text = ' Case '
            self._win.addstr(y, x, f'{text}', style)

            x = CASE_MODE_LEN + 1
            text = f'{sum(self._hits):>8} hits '
            self._win.addstr(y, x, text, style)

        # Print from right to left
        x = self._w
        text = f' {self._name} '
        x = x - len(text) - 1
        self._win.addstr(y, x, text, style)

        x = x - 5 - 1 # voffest_desc at most 5 char long
        if len(self._voffset_desc) > 0:
            text = f' {self._voffset_desc:>3} '
            self._win.addstr(y, x, text, style)

        text = f' {len(self._lines)} lines '
        x = x - len(text) - 1
        self._win.addstr(y, x, text, style)

        text = f' {self._basename} '
        x = x - len(text) - 1
        self._win.addstr(y, x, text, style | curses.A_BOLD)

        assert len(self._hits) == len(self._config.filters)
        for i, f in enumerate(self._config.filters):
            color = curses.color_pair(self._config.get_color(i))

            x = 0
            text = CASE_MODE_TEXT[0 if f.ignore_case else 1]
            self._win.addstr(y + 1 + i, x, text)

            x += CASE_MODE_LEN + 1
            text = ' AND '.join(f.keywords)
            self._win.addstr(y + 1 + i, x, f'{self._hits[i]:>8} {text}', color)

    def draw(self):
        '''Draws the view'''
        debug(f'{self._name} draw {self._voffset}')
        self._win.clear()

        prefix_info = self._get_prefix_info()

        # Only draw what we need: we are going to pull at most _h lines from the
        # data model, possibly less if some content needs multiple line (wrapping)
        iddata = self._voffset
        iddatamax = len(self._ddata)

        # screen offset of content (to the right of line number and sep, if any)
        for y in range(self._content_lines_count):
            if iddata >= iddatamax:
                break
            idata, offset = self._ddata[iddata]
            iddata += 1

            idx, fidx, text, s = self._data[idata]
            color = 0 if fidx < 0 else self._config.get_color(fidx)
            color = curses.color_pair(color)

            if offset == 0:
                self._draw_prefix((y, 0), prefix_info, idx, color)

            self._draw_content((y, prefix_info[0]),
                               text, s, self._hoffset + offset, color)

        try:
            self._draw_bar(self._content_lines_count)
        except curses.error:
            pass

        self._win.refresh()

    def _layout(self, redraw):
        # Breaks content lines into displayable lines (self._ddata)
        self._content_lines_count = max(0, self._h - 1 - len(self._config.filters))

        prefix_len, _, _ = self._get_prefix_info()
        w_text = self._w - prefix_len       # width for file content
        assert w_text > 0

        ddata = [] # Display data (one entry per line on display)
        firstdlines = [] # First display line of each model lines
        for idata, data in enumerate(self._data):
            firstdlines.append(len(ddata))
            if not self._config.wrap:
                ddata.append([idata, 0])
            else:
                _, _, text, _ = data
                offset = 0
                left = len(text)
                while left >= 0:
                    ddata.append([idata, offset])
                    offset += w_text
                    left -= w_text

        self._firstdlines = firstdlines
        self._ddata = ddata
        self._w_text = w_text
        # debug(f'layout: {len(ddata)} w:{self._config.wrap}')

        # Try preserve current voffset, but make sure we comply with constraints
        self.set_v_offset(self._voffset, False)

        assert self._voffset == 0 or self._voffset < len(ddata), f'{self._voffset}'

        if redraw:
            self.draw()

    def _sync_data(self, redraw):
        # Recompute the model data (self._data) based on the file content and
        # the selected filters. Layout and Draw() are done after model data has
        # been computed.

        # Returns a list of segments (ie pair of indices (start,end)) locating
        # keywords in the given text
        def find_matches(text, f):
            keywords = f.keywords
            flags = re.IGNORECASE if f.ignore_case else 0
            s = set() # Use a set() as multiple matches are possible
            for kw in keywords:
                matching = False
                for m in re.finditer(kw, text, flags):
                    matching = True
                    s.add((m.start(), m.end()))
                if not matching:
                    # Bail out early as soon as one keyword has no match
                    return False, set()

            # Sort all segments and then merge them as overlap can happen
            return True, segments.sort_and_merge_segments(s)

        data = []
        filters = self._config.filters
        only_matching = self._config.only_matching and len(filters) > 0
        hits = [0 for f in filters]

        for i, line in enumerate(self._lines):
            # Replace tabs with 4 spaces (not clean!!!)
            line = line.replace('\t', '    ')

            matching = False
            for fidx, f in enumerate(filters):
                matching, s = find_matches(line, f)
                if matching:
                    hits[fidx] += 1
                    data.append([i, fidx, line, s])
                    break
            if not matching and not only_matching:
                data.append([i, -1, line, set()])
        self._data = data
        self._hits = hits

        # Trigger layout and potentially draw
        self._voffset = 0 # vertical offset in content: index of first visible line in ddata
        self._voffset_desc = ''
        self._hoffset = 0 # horizontal offset in content: index of first visible column
        self._layout(redraw)

    def set_lines(self, lines):
        '''Sets the content of this view. Assumes view is offline, and does
        not trigger a redraw.'''
        self._lines = lines
        self._sync_data(False)

    def _pop_filter(self):
        if self._config.has_filters():
            self._config.filters.pop()
            self._sync_data(True)

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
            f = Filter()
            f.ignore_case = keyword.lower() == keyword
            self._config.push_filter(f)

        self._config.top_filter().add(keyword)
        self._sync_data(True)
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
            self._sync_data(True)

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
        self._sync_data(True)
        return f'Only matching lines {bool_to_text(self._config.only_matching)}'

    def _toggle_show_spaces(self):
        self._config.show_spaces = not self._config.show_spaces
        self.draw()
        return f'Show spaces {bool_to_text(self._config.show_spaces)}'

    def _toggle_whole_line(self):
        self._config.whole_line = not self._config.whole_line
        self.draw()
        return f'Whole line highliting {bool_to_text(self._config.whole_line)}'

    def _toggle_ignore_case(self):
        if not self._config.has_filters():
            return 'Cannot change case sentitivity (no keyword)'
        f = self._config.top_filter()
        f.ignore_case = not f.ignore_case
        self._sync_data(True)
        return f'Ignore case set to {f.ignore_case}'

    def _next_palette(self):
        self._config.next_palette()
        self.draw()
        return f'Using color palette #{self._config.palette_index}'

    def _draw_prefix(self, position, prefix_info, idx, color):
        _, w_index, sep = prefix_info
        y, x = position
        if w_index <= 0:
            self._win.addstr(y, x, f'{sep}', color | curses.A_BOLD)
        else:
            self._win.addstr(y, x, f'{idx:>{w_index}}{sep}', color | curses.A_BOLD)

    def _draw_content(self, position, text, s, offset, color):
        y, x = position
        vend = offset + self._w_text
        if self._config.show_spaces:
            text = text.replace(' ', '·') # Note: this is curses.ACS_BULLET
        if self._config.whole_line:
            text = text[offset:vend]
            text = f'{text:<{self._w_text}}'
            self._win.addnstr(y, x, text, self._w, color)
        else:
            for match, start, end in segments.iter_segments(offset, vend, s):
                assert start < end
                c = color if match else 0
                l = end - start
                self._win.addnstr(y, x, text[start:end], l, c)
                x += l

    def _set_h_offset(self, offset):
        offset = max(offset, 0)
        if self._hoffset != offset:
            self._hoffset = offset
            self.draw()

    def set_v_offset(self, offset, redraw):
        '''Sets the vertical offset of the view.'''
        assert self._content_lines_count >= 0
        ymax = max(0, len(self._ddata) - self._content_lines_count)
        if offset >= ymax:
            offset = ymax
            desc = 'BOT'
        elif offset <= 0:
            offset = 0
            desc = 'TOP'
        else:
            p = int(offset * 100 / ymax)
            desc = f'{p}%'
        if self._voffset != offset:
            self._voffset = offset
            self._voffset_desc = desc
            if redraw:
                self.draw()

    def _hscroll(self, delta):
        self._set_h_offset(self._hoffset + delta)

    def _vscroll(self, delta):
        self.set_v_offset(self._voffset + delta, True)

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
        elif line >= len(self._ddata):
            self.set_v_offset(sys.maxsize, True)
        else:
            voffset = 0
            for idata, _ in self._ddata:
                i, _, _, _ = self._data[idata]
                if i >= line:
                    self.set_v_offset(voffset, True)
                    break
                voffset += 1
        return f'Goto line {line}'

    def has_filters(self):
        '''Returns whether the view has any filter or not.'''
        return self._config.has_filters()

    def _vscroll_to_match(self, starting, direction):
        iddata = self._voffset
        idatamax = len(self._data)
        idata, _ = self._ddata[iddata]
        if not starting:
            idata += direction
        while 0 <= idata < idatamax:
            _, fidx, _, _ = self._data[idata]
            if fidx >= 0:
                iddata = self._firstdlines[idata]
                break
            idata += direction
        # Remember current offset to describe side-effect
        prev_offset = self._voffset
        self.set_v_offset(iddata, True)
        if prev_offset == self._voffset:
            return '(END)' if direction > 0 else '(BEGIN)'
        return 'Next match' if direction > 0 else 'Previous match'

    def search(self, kw):
        '''Searches for the given keyword. This function assumes the view
        currently has no filter.'''
        assert not self.has_filters()
        if len(kw) > 0:
            self._config.only_matching = False
            self.push_keyword(kw, True)
            self._vscroll_to_match(True, 1)

    def _vscroll_to_next_match(self):
        return self._vscroll_to_match(False, 1)

    def _vscroll_to_prev_match(self):
        return self._vscroll_to_match(False, -1)

    def _vpagescroll(self, delta):
        self._vscroll(delta * self._content_lines_count)

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
            TextViewCommand.TOGGLE_WHOLE_LINE:     self._toggle_whole_line,
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
    -          Remove last keyword from filter

  Display mode:
    m          Show/hide only matching lines
    l          Show/hide line numbers
    k          Enable/disables line wrapping
    *          Show/hide diamonds at line starts (when wrapping)
    .          Enable/disable space displaying as bullets
    c          Cycle/change color palette
    h          Cycle/change highlight mode
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

    def out(self, *argv):
        '''Outputs the given arg to the debug view.'''
        assert self._scr
        h, w = self._size
        self._lines.append(*argv)
        if len(self._lines) > h:
            self._lines.pop(0)

        i = 0
        for line in self._lines:
            try:
                self._win.addstr(i, 0, f'{line:<{w}}')
            except curses.error:
                pass
            i += 1

        self._win.refresh()

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
            padding = 3
            x += padding # just adds something to expose layout issues
            y += padding
            view_lines_count = 20
            maxw = maxw - 2 * padding
            dbg_size = (6, maxw)
            self.debug = DebugView(scr, dbg_size, (y, x))
            y += dbg_size[0]

        for v in self._content:
            v.layout(view_lines_count, maxw, y, x)

        y += view_lines_count
        self._y_get_text = y

    def _set_view(self, idx):
        assert 0 <= idx < len(self._content)
        if self._current != idx:
            self._current = idx
            self._content[idx].draw()
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
            kw = self._get_keyword()
            return v.push_keyword(kw, new_filter)

        def goto_line():
            line_as_text = self.get_text('Enter line: ')
            return v.goto_line(line_as_text)

        # Map keys to simple text view commands that don't take any argument
        simple = {
            ord('F'):          TextViewCommand.POP_FILTER,
            ord('-'):          TextViewCommand.POP_KEYWORD,
            ord('n'):          TextViewCommand.VSCROLL_TO_NEXT_MATCH,
            ord('p'):          TextViewCommand.VSCROLL_TO_PREV_MATCH,
            ord('m'):          TextViewCommand.TOGGLE_ONLY_MATCHING,
            ord('l'):          TextViewCommand.TOGGLE_LINE_NUMBERS,
            ord('k'):          TextViewCommand.TOGGLE_WRAP,
            ord('*'):          TextViewCommand.TOGGLE_BULLETS,
            ord('.'):          TextViewCommand.TOGGLE_SHOW_SPACES,
            ord('c'):          TextViewCommand.NEXT_PALETTE,
            ord('h'):          TextViewCommand.TOGGLE_WHOLE_LINE,
            ord('i'):          TextViewCommand.TOGGLE_IGNORE_CASE,
            curses.KEY_UP:     TextViewCommand.GO_UP,
            ord('w'):          TextViewCommand.GO_UP,
            curses.KEY_DOWN:   TextViewCommand.GO_DOWN,
            ord('s'):          TextViewCommand.GO_DOWN,
            curses.KEY_LEFT:   TextViewCommand.GO_LEFT,
            ord('a'):          TextViewCommand.GO_LEFT,
            curses.KEY_RIGHT:  TextViewCommand.GO_RIGHT,
            ord('d'):          TextViewCommand.GO_RIGHT,
            curses.KEY_HOME:   TextViewCommand.GO_HOME,
            ord('g'):          TextViewCommand.GO_HOME,
            ord('<'):          TextViewCommand.GO_HOME,
            curses.KEY_END:    TextViewCommand.GO_END,
            ord('G'):          TextViewCommand.GO_END,
            ord('>'):          TextViewCommand.GO_END,
            curses.KEY_NPAGE:  TextViewCommand.GO_NPAGE,
            ord(' '):          TextViewCommand.GO_NPAGE,
            curses.KEY_PPAGE:  TextViewCommand.GO_PPAGE,
            ord('b'):          TextViewCommand.GO_PPAGE,
            curses.KEY_SLEFT:  TextViewCommand.GO_SLEFT,
            ord('A'):          TextViewCommand.GO_SLEFT,
            curses.KEY_SRIGHT: TextViewCommand.GO_SRIGHT,
            ord('D'):          TextViewCommand.GO_SRIGHT,
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

def init_colors():
    '''Initializes color support.'''
    assert curses.has_colors()
    assert curses.COLORS == 256, 'Try setting TERM env var to screen-256color'

    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS-1):
        curses.init_pair(i + 1, i, -1)
    # HACK for color of bar with background
    curses.init_pair(BAR_COLOR_ID, 0, BAR_COLOR)

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
        debug(f'Key {key}')
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

    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    return parser

def main():
    '''Application entry point'''
    parser = init_env()
    args = parser.parse_args()
    curses.wrapper(main_loop, args.file)

if __name__ == '__main__':
    main()
