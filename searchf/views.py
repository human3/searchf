'''Module implementing views for searchf application.'''

import curses
import curses.ascii
import os
import re
import sys

from typing import Any
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple

from . import colors
from . import enums
from . import keys
from . import models
from . import segments
from . import types

# Do not use curses.A_BOLD on Windows as it just renders horribly when
# highlighting
USE_BOLD = 0 if sys.platform == 'win32' else curses.A_BOLD

STATUS_EMPTY = ''


def bool_to_text(value: bool) -> str:
    '''Converts a boolean value to text.'''
    return 'enabled' if value else 'disabled'


CASE_COL_TEXTS = ['Case', 'ignored', 'sensitive']
CASE_COL_LEN = len(max(CASE_COL_TEXTS, key=len))

SHOWN_COL_TEXTS = ['Shown', 'no', 'yes']
SHOWN_COL_LEN = len(max(SHOWN_COL_TEXTS, key=len))


class PrefixInfo(NamedTuple):
    '''Line prefix infos.

    Attributes:
        length       Total length of prefix.
        digit_count  Number of digits of the largest line number.
        separator    Separator between things on left (line number,
                     bullet), and things on right (line).
    '''
    length: int
    digit_count: int
    separator: str


class TextView:
    '''Display selected content of a file, using filters and keyword to
    highlight specific text.'''

    # pylint: disable=too-many-instance-attributes

    def __init__(self, store, scr, name: str, path: str) -> None:
        self._raw: models.RawContent = \
            models.RawContent()
        self._selected: models.SelectedContent = \
            models.SelectedContent()
        self._display: models.DisplayContent = \
            models.DisplayContent()
        self._offsets: models.Offsets = models.Offsets()
        self._config: models.ViewConfig = models.ViewConfig()
        self._store = store
        self._scr = scr
        self._name: str = name
        self._basename: str = os.path.basename(path)
        # self._win: Optional[curses._CursesWindow]
        self._win: Any = None
        self._size: types.Size = (0, 0)
        self._content_available_size: types.Size = (0, 0)
        self._ruler: str = ''

    def get_config(self) -> models.ViewConfig:
        '''Gets the config.'''
        return self._config

    def _slot_save(self) -> types.Status:
        '''Save the config.'''
        if not self._config.has_filters():
            return 'No filters to save'
        if not self._config.dirty:
            return 'No change to save'
        idx = self._store.save(self._config)
        self._config.dirty = False
        return f'Filters saved in slot {idx}'

    def _slot_delete(self) -> types.Status:
        idx = self._store.delete()
        if idx is not None:
            assert idx >= 0
            self._config.dirty = True  # Allows saving again
            return f'Slot {idx} deleted'
        return 'No slot loaded. Cannot delete current slot.'

    def _slot_load(self, goto_next: bool) -> types.Status:
        if not self._store.can_load():
            return 'Nothing to load. All slots are empty.'
        self._config, idx = self._store.load(goto_next)
        self._sync(True)
        self._config.dirty = False
        return f'Slot {idx} loaded'

    def name(self) -> str:
        '''Gets the name of the view.'''
        return self._name

    def layout(self, h: int, w: int, y: int, x: int) -> None:
        '''Sets dimension of the view and recompute underlying view model
        without redrawing anything.'''

        # _size stores number of lines and columns available to draw content
        self._size = (h, w)

        if not self._win:
            self._win = curses.newwin(h, w, y, x)
        else:
            self._win.resize(h, w)
            self._layout(False)

    def _get_prefix_info(self) -> PrefixInfo:
        if self._config.line_numbers:
            number_length = self._raw.line_number_length()
            sep = ' │ '
        elif self._config.wrap:
            number_length = 0
            sep = '◆ ' if self._config.bullets else ''  # curses.ACS_DIAMOND
        else:
            number_length = 0
            sep = ''
        return PrefixInfo(number_length + len(sep), number_length, sep)

    def _get_color_pair(self, i: int) -> colors.Pair:
        return colors.get_color_pair(self._config.palette_id, i)

    def _draw_bar(self, y: int) -> None:
        '''Draws the status bar and the filter stack underneath.'''

        _, w = self._size
        style = curses.color_pair(colors.BAR_COLOR_PAIR_ID)
        self._win.hline(y, 0, curses.ACS_HLINE, w, style)

        if not self._config.has_filters():
            self._win.addstr(' No filter ', style)
        else:
            self._win.addstr(f'{self._selected.hits_count():>8}', style)
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

        # voffest_desc is not always shown, but at most 5 char long
        text = ''.ljust(5)
        x = move_left_for(x, text)
        if len(self._offsets.voffset_desc) > 0:
            text = f' {self._offsets.voffset_desc:>3} '
            self._win.addstr(y, x, text, style)

        text = f' {self._raw.line_count()} lines '
        x = move_left_for(x, text)
        self._win.addstr(y, x, text, style)

        text = f' {self._basename} '
        x = move_left_for(x, text)
        self._win.addstr(y, x, text, style | USE_BOLD)

        assert len(self._selected.hits) == \
            self._config.get_filters_count()
        for i, f in enumerate(self._config.filters):
            x = 0
            y += 1
            self._win.addstr(y, 0, f'{self._selected.hits[i]:>8}')
            text = CASE_COL_TEXTS[1 if f.ignore_case else 2]
            self._win.addstr(f' | {text:^{CASE_COL_LEN}}')
            text = SHOWN_COL_TEXTS[1 if f.hiding else 2]
            self._win.addstr(f' | {text:^{SHOWN_COL_LEN}} | ')
            text = ' AND '.join(f.keywords)
            color = 0 if f.hiding else self._get_color_pair(i)
            self._win.addstr(text, color)

    def _draw_prefix(
            self,
            *,
            y: int,
            prefix_info: PrefixInfo,
            line_idx: int,
            color: int,
            is_first_line: bool,
    ) -> None:
        _, w_index, sep = prefix_info
        if is_first_line and w_index > 0:
            assert line_idx >= 0
            self._win.addstr(y, 0, f'{line_idx:>{w_index}}', color | USE_BOLD)
        else:
            fill = ' '
            self._win.addstr(y, 0, f'{fill:>{w_index}}', color | USE_BOLD)
        self._win.addstr(y, w_index, f'{sep}')

    def _draw_content(
            self,
            *,
            pos: types.Position,
            text: str,
            segs: List[segments.Segment],
            offset: int,
            ffidx: int,
            ffcolor: int,
    ) -> None:
        _, width = self._content_available_size
        vend = offset + width
        if self._config.show_spaces:
            text = text.replace(' ', '·')  # Note: this is curses.ACS_BULLET

        x = pos.x
        for match, start, end, attr in segments.iterate(
                offset, vend, segs):
            assert match or attr == -1
            assert start < end
            length = end - start
            if ffidx != -1 and \
               self._config.colorize_mode == enums.ColorizeMode.LINE:
                attr = ffcolor
            elif attr == -1 or (attr & curses.A_ATTRIBUTES) == 0:
                # Assume attr is a filter index
                attr = self._get_color_pair(attr)
            # otherwise use attributes from segment as is
            self._win.addnstr(pos.y, x, text[start:end], length, attr)
            # Some characters like emojs and chinese characters actually
            # take 2 spot on the screen, so we just use current cursor
            # position after last write
            _, x = self._win.getyx()

    def draw(self) -> None:
        '''Draws the view.'''
        # debug.out(f'{self._name} draw {self._offsets.voffset}')
        self._win.clear()

        prefix_info = self._get_prefix_info()
        ymax, _ = self._content_available_size

        # Only draw what we need: we are going to pull at most
        # _content_available_size[1] lines from DisplayContent, possibly
        # less if some content needs multiple lines (wrapping)

        # We iterate over all the display lines using idline
        idline = self._offsets.voffset
        idlinemax = self._display.lines_count()

        for y in range(ymax):
            if idline >= idlinemax:
                break
            iline, offset = self._display.dlines[idline]
            idline += 1

            # iline is the index of the selected line associated with the
            # current display line. offset is the horizontal offset in
            # original content line where this display line starts.  If offset
            # is not 0, this means the original content line is effectively
            # being wrapped on to multiple lines on the screen.

            line_idx, filter_idx, text, segs = \
                self._selected.lines[iline]
            if line_idx == models.RULER_INDEX:
                self._win.addstr(y, 0, self._ruler)
                continue

            # filter_idx is the index of the first filter that is matching
            # current line
            ffcolor = self._get_color_pair(filter_idx)
            self._draw_prefix(y=y, prefix_info=prefix_info,
                              line_idx=line_idx, color=ffcolor,
                              is_first_line=offset == 0)
            offset += self._offsets.hoffset
            self._draw_content(
                pos=types.Position(prefix_info.length, y),
                text=text,
                segs=segs,
                offset=offset,
                ffidx=filter_idx,
                ffcolor=ffcolor)

        self._draw_bar(self._content_available_size[0])
        self._win.refresh()

    def _layout(self, redraw: bool) -> None:
        '''Propagate layout changes: evaluates the available space and
        recompute displayable content from the selected lines.
        '''

        self._ruler = '-' * self._size[1]

        # Compute space available for file content
        h, w = self._size
        prefix_len, _, _ = self._get_prefix_info()
        h = max(0, h - 1 - self._config.get_filters_count())
        w = max(0, w - prefix_len)
        self._content_available_size = (h, w)

        self._display = self._selected.layout(h, w, self._config.wrap)
        self._offsets.layout(h, self._display.lines_count())

        # Try preserve current voffset, but make sure we comply with
        # constraints which might just have changed.
        self.set_v_offset(self._offsets.voffset, False)

        assert self._offsets.voffset == 0 or \
            self._offsets.voffset < self._display.lines_count()

        if redraw:
            self.draw()

    def _sync(self, redraw: bool) -> None:
        self._selected = self._raw.filter(
            self._config.filters,
            self._config.line_visibility,
            self._config.sgr_mode)
        self._layout(redraw)

    def set_config(self, config: models.ViewConfig) -> None:
        '''Sets the configuration.'''
        self._config = config
        self._sync(False)

    def set_lines(self, lines: List[str]) -> None:
        '''Sets the content of this view. Assumes the view is offscreen and
        does not trigger a redraw.
        '''
        self._raw.set_lines(lines)
        self._sync(False)

    def _pop_filter(self) -> types.Status:
        if self._config.has_filters():
            self._config.filters.pop()
            self._sync(True)
            return 'Filter removed'
        return 'No filter to remove'

    def push_keyword(self, keyword: str, new_filter: bool) -> types.Status:
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

    def _pop_keyword(self) -> types.Status:
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
        and the keyword that was last entered by user.
        '''
        if not self._config.has_filters():
            return 0, ''
        f = self._config.top_filter()
        return f.get_count_and_last_keyword()

    def _toggle_line_numbers(self) -> types.Status:
        self._config.line_numbers = not self._config.line_numbers
        self._layout(True)
        return f'Line numbers {bool_to_text(self._config.line_numbers)}'

    def _toggle_wrap(self) -> types.Status:
        self._config.wrap = not self._config.wrap
        self._layout(True)
        return f'Line wrapping {bool_to_text(self._config.wrap)}'

    def _toggle_bullets(self) -> types.Status:
        self._config.bullets = not self._config.bullets
        self._layout(True)
        return f'Bullets {bool_to_text(self._config.bullets)}'

    def _toggle_show_spaces(self) -> types.Status:
        self._config.show_spaces = not self._config.show_spaces
        self.draw()
        return f'Show spaces {bool_to_text(self._config.show_spaces)}'

    def _cycle_colorize_mode(self, forward: bool) -> types.Status:
        f = enums.ColorizeMode.get_next if forward \
            else enums.ColorizeMode.get_prev
        self._config.colorize_mode = f(self._config.colorize_mode)
        self.show()
        return f'Colorize mode: {self._config.colorize_mode}'

    def _cycle_line_visibility(self, forward: bool) -> types.Status:
        f = enums.LineVisibility.get_next if forward \
            else enums.LineVisibility.get_prev
        self._config.line_visibility = f(self._config.line_visibility)
        self._sync(True)
        return f'{self._config.line_visibility}'

    def _cycle_sgr_mode(self, forward: bool) -> types.Status:
        f = enums.SgrMode.get_next if forward \
            else enums.SgrMode.get_prev
        self._config.sgr_mode = f(self._config.sgr_mode)
        self._sync(True)
        return f'{self._config.sgr_mode}'

    def _toggle_ignore_case(self) -> types.Status:
        if not self._config.has_filters():
            return 'Cannot change case sentitivity (no keyword)'
        f = self._config.top_filter()
        f.ignore_case = not f.ignore_case
        self._sync(True)
        return f'Ignore case set to {f.ignore_case}'

    def _toggle_hiding(self) -> types.Status:
        if not self._config.has_filters():
            return 'Cannot change filter property (no filter)'
        f = self._config.top_filter()
        f.hiding = not f.hiding
        self._sync(True)
        action = 'hidden' if f.hiding else 'shown'
        return f'Lines matching filter are now {action}'

    def _apply_palette_and_draw(self) -> None:
        colors.apply_palette(
            self._config.palette_id,
            self._config.colorize_mode == enums.ColorizeMode.KEYWORD_HIGHLIGHT)
        self.draw()

    def show(self) -> None:
        '''Shows the view, after it was hidden by another one'''
        self._apply_palette_and_draw()

    def _cycle_palette(self, forward: bool) -> types.Status:
        '''Select the next palette in the given direction'''
        pid = colors.cycle_palette(self._config.palette_id, forward)
        self._config.set_palette(pid)
        self._apply_palette_and_draw()
        return f'Using color palette #{pid}'

    def _set_h_offset(self, offset: int) -> types.Status:
        if self._offsets.set_h_offset(offset):
            self.draw()
        return STATUS_EMPTY

    def set_v_offset(self, offset: int, redraw: int) -> types.Status:
        '''Sets the vertical offset of the view.'''
        if self._offsets.set_v_offset(offset) and redraw:
            self.draw()
        return STATUS_EMPTY

    def _hscroll(self, delta: int) -> types.Status:
        self._set_h_offset(self._offsets.hoffset + delta)
        return STATUS_EMPTY

    def _vscroll(self, delta: int) -> types.Status:
        self.set_v_offset(self._offsets.voffset + delta, True)
        return STATUS_EMPTY

    def goto_line(self, line_text: str) -> types.Status:
        '''Makes sure the given line is visible, making it the first line on
        the screen unless that would make last line of the file not
        displayed at the bottom.'''
        try:
            line = int(line_text)
        except ValueError:
            return 'Not a number'
        if line <= 0:
            self.set_v_offset(0, True)
        elif line >= self._display.lines_count():
            self.set_v_offset(sys.maxsize, True)
        else:
            voffset = 0
            for iline, _ in self._display.dlines:
                i, _, _, _ = self._selected.lines[iline]
                if i >= line:
                    self.set_v_offset(voffset, True)
                    break
                voffset += 1
        return f'Goto line {line}'

    def has_filters(self) -> bool:
        '''Returns whether the view has any filter or not.'''
        return self._config.has_filters()

    def swap_filters(self) -> types.Status:
        '''Swaps the top 2 filters.'''
        count = self._config.get_filters_count()
        if self._config.get_filters_count() < 2:
            return 'Not enough filters'
        self._config.swap_filters(count - 1, count - 2)
        self._sync(True)
        return 'Filters swapped'

    def rotate_filters(self, go_up: bool) -> types.Status:
        '''Rotate the filters.'''
        if self._config.get_filters_count() < 2:
            return 'Not enough filters'
        self._config.rotate_filters(go_up)
        self._sync(True)
        return 'Filters rotated'

    def _vscroll_to_match(
            self,
            starting: bool,
            direction: int,
    ) -> types.Status:
        idline = self._offsets.voffset
        ilinemax = len(self._selected.lines)
        iline, _ = self._display.dlines[idline]
        if not starting:
            iline += direction
        while 0 <= iline < ilinemax:
            _, fidx, _, _ = self._selected.lines[iline]
            if fidx >= 0:
                idline = self._display.firstdlines[iline]
                break
            iline += direction
        # Remember current offset to be able to return a side-effect
        # description
        prev_offset = self._offsets.voffset
        self.set_v_offset(idline, True)
        if prev_offset == self._offsets.voffset:
            return '(END)' if direction > 0 else '(BEGIN)'
        return 'Next match' if direction > 0 else 'Previous match'

    def search(self, keyword: str) -> types.Status:
        '''Searches for the given keyword. This function assumes the view
        currently has no filter.'''
        assert not self.has_filters()
        if len(keyword) > 0:
            self._config.reverse_matching = False
            self._config.line_visibility = enums.LineVisibility.ALL
            self.push_keyword(keyword, True)
            self._vscroll_to_match(True, 1)
        return STATUS_EMPTY

    def _vpagescroll(self, delta: int) -> types.Status:
        self._vscroll(delta * self._content_available_size[0])
        return STATUS_EMPTY

    def execute(self, command: enums.Command) -> types.Status:
        '''Executes the given command.'''
        dispatch = {
            enums.Command.GO_UP:
                lambda: self._vscroll(-1),
            enums.Command.GO_DOWN:
                lambda: self._vscroll(1),
            enums.Command.GO_LEFT:
                lambda: self._hscroll(-1),
            enums.Command.GO_RIGHT:
                lambda: self._hscroll(1),
            enums.Command.GO_HOME:
                lambda: self.set_v_offset(0, True),
            enums.Command.GO_END:
                lambda: self.set_v_offset(sys.maxsize, True),
            enums.Command.GO_NPAGE:
                lambda: self._vpagescroll(1),
            enums.Command.GO_PPAGE:
                lambda: self._vpagescroll(-1),
            enums.Command.GO_SLEFT:
                lambda: self._hscroll(-20),
            enums.Command.GO_SRIGHT:
                lambda: self._hscroll(20),
            enums.Command.VSCROLL_TO_NEXT_MATCH:
                lambda: self._vscroll_to_match(False, 1),
            enums.Command.VSCROLL_TO_PREV_MATCH:
                lambda: self._vscroll_to_match(False, -1),
            enums.Command.NEXT_COLORIZE_MODE:
                lambda: self._cycle_colorize_mode(True),
            enums.Command.PREV_COLORIZE_MODE:
                lambda: self._cycle_colorize_mode(False),
            enums.Command.NEXT_PALETTE:
                lambda: self._cycle_palette(True),
            enums.Command.PREV_PALETTE:
                lambda: self._cycle_palette(False),
            enums.Command.NEXT_LINE_VISIBILITY:
                lambda: self._cycle_line_visibility(True),
            enums.Command.PREV_LINE_VISIBILITY:
                lambda: self._cycle_line_visibility(False),
            enums.Command.NEXT_SGR_MODE:
                lambda: self._cycle_sgr_mode(True),
            enums.Command.PREV_SGR_MODE:
                lambda: self._cycle_sgr_mode(False),
            enums.Command.POP_FILTER:
                self._pop_filter,
            enums.Command.POP_KEYWORD:
                self._pop_keyword,
            enums.Command.TOGGLE_LINE_NUMBERS:
                self._toggle_line_numbers,
            enums.Command.TOGGLE_WRAP:
                self._toggle_wrap,
            enums.Command.TOGGLE_BULLETS:
                self._toggle_bullets,
            enums.Command.TOGGLE_SHOW_SPACES:
                self._toggle_show_spaces,
            enums.Command.TOGGLE_IGNORE_CASE:
                self._toggle_ignore_case,
            enums.Command.TOGGLE_HIDING:
                self._toggle_hiding,
            enums.Command.SWAP_FILTERS:
                self.swap_filters,
            enums.Command.ROTATE_FILTERS_UP:
                lambda: self.rotate_filters(True),
            enums.Command.ROTATE_FILTERS_DOWN:
                lambda: self.rotate_filters(False),
            enums.Command.SLOT_SAVE:
                self._slot_save,
            enums.Command.SLOT_DELETE:
                self._slot_delete,
            enums.Command.SLOT_LOAD_NEXT:
                lambda: self._slot_load(True),
            enums.Command.SLOT_LOAD_PREV:
                lambda: self._slot_load(False),
        }
        assert command in dispatch, f'command {command}'
        return dispatch[command]()


class DebugView:
    '''Displays few debug lines, convenient to debug layout while curses
    running.'''
    def __init__(self, scr) -> None:
        self._scr = scr
        self._lines: List[str] = []
        self._size: types.Size = (0, 0)
        self._position = (0, 0)
        self._win = curses.newwin(0, 0, 0, 0)
        # self._f = open('.searchf/debug.txt', 'w+')

    def layout(self, size: types.Size, position: Tuple[int, int]) -> None:
        '''Layout the debug view'''
        self._size = size
        self._position = position
        self._win.resize(size[0], size[1])
        self._win.mvwin(position[0], position[1])

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
        # self._f.write(*argv)
        # self._f.write('\n')
        # self._f.flush()
        if len(self._lines) > h:
            self._lines.pop(0)
        self.draw()


class KeyEventView:
    '''Display KeyEvent pressed by end-user.'''
    def __init__(self, scr):
        self._scr = scr
        self._x = 0
        self._y = 0
        self._w = 0

    def layout(self, y: int, x: int, _: int, w: int) -> None:
        '''Layout view.'''
        self._x = x
        self._y = y
        self._w = w

    def show(self, ev: keys.KeyEvent) -> None:
        '''Show key pressed'''
        if not ev.is_poll():
            text = f'    KEY {ev.text:15} {ev.cmd}'
            self._scr.addstr(self._y,
                             self._x,
                             f'{text:<{self._w}}',
                             curses.A_BOLD)
