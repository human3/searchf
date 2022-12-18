'''Application module'''

import copy
import curses
import curses.ascii
import os
import sys

from curses.textpad import Textbox
from typing import Any
from typing import List
from typing import Tuple

from . import debug
from . import enums
from . import types
from . import views

# Changes layout to show a debug window in which debug() function will output
USE_DEBUG = False

STATUS_UNCHANGED = 'unchanged'


def get_max_yx(scr) -> types.Size:
    '''This function is a test artifact that wraps getmaxyx() from curses so
    that we can overwrite it and test specific dimensions.
    '''
    return scr.getmaxyx()


def getmtime(path):
    '''Wraps os.getmtime() for testing'''
    return os.path.getmtime(path)


class EscapeException(Exception):
    '''Signals that Escape key has been pressed'''


def validate(k: int) -> int:
    '''Validates key'''
    if k == curses.ascii.DEL:
        k = curses.KEY_BACKSPACE
    elif k == curses.ascii.ESC:
        raise EscapeException()
    return k


def get_text(scr, y, x, text_prompt: str, handler, text: str) -> str:
    '''Gets text interactively from end user'''
    scr.addstr(y, x, text_prompt)
    x += len(text_prompt)
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
    clear(scr, y, 0, len(text_prompt))
    return text if text else ''


def prompt(scr, y: int, x: int, text_prompt: str, text: str) -> str:
    '''Prompts user to enter some text.'''
    def handle(box):
        box.edit(validate=validate)
    return get_text(scr, y, x, text_prompt, handle, text)


def clear(scr, y, x, length):
    '''Prints "length" spaces at the given position'''
    _, maxw = get_max_yx(scr)
    blank = f'{" ":>{length}}'
    scr.addstr(y, x, blank[:maxw-(x+1)])
    scr.move(y, x)


class App:
    '''Aggregates all views, controlling which ones are visible, handling
    key presses and command dispatching.'''

    # pylint: disable=too-many-instance-attributes

    def __init__(self, help_lines) -> None:
        self._help_lines = help_lines
        self._debug_view: views.DebugView
        self._scr: Any = None
        self._path: str = ''
        self._content: List[views.TextView] = []
        self._current: int = -1
        self._hidden_view: int = -1
        self._y_get_text: int = 0
        self._mtime: float = 0.0
        self._auto_reload: bool = False
        self._auto_reload_anchor: int = 0

    def layout(self) -> types.Size:
        '''Recompute layout'''
        assert self._scr
        scr = self._scr
        maxh, maxw = get_max_yx(scr)
        view_lines_count = maxh - 1
        x = 0
        y = 0

        if USE_DEBUG:
            dbg_size = (10, maxw)
            self._debug_view.layout(dbg_size, (y, x))
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
        return maxh, maxw

    def _set_view(self, idx: int, propagate_config: bool) -> types.Status:
        assert 0 <= idx < len(self._content)
        if self._current != idx:
            config = self._content[self._current].get_config()
            self._current = idx
            if propagate_config:
                self._content[idx].set_config(copy.deepcopy(config))
            self._content[idx].show()
        return f'Switched to {self._content[idx].name()}'

    def _help_view_push(self) -> types.Status:
        self._hidden_view = self._current
        return self._set_view(3, False)

    def _help_view_pop(self) -> types.Status:
        idx = self._hidden_view
        self._hidden_view = -1
        return self._set_view(idx, False)

    def _reload(self, scroll_to: int) -> types.Status:
        with open(self._path, encoding='utf-8') as f:
            lines = f.readlines()
            for i, v in enumerate(self._content):
                if i == len(self._content) - 1:
                    v.set_lines(self._help_lines)
                else:
                    v.set_lines(lines)
                    v.set_v_offset(scroll_to, False)
        self._content[self._current].draw()
        self._mtime = getmtime(self._path)
        return 'File reloaded'

    def create(self, store, scr, path: str) -> None:
        '''Creates all views in the given screen, and loads the content from
        the given file.'''
        self._scr = scr
        self._path = path
        self._content.clear()
        self._content.append(views.TextView(store, scr, 'View 1', path))
        self._content.append(views.TextView(store, scr, 'View 2', path))
        self._content.append(views.TextView(store, scr, 'View 3', path))
        self._content.append(views.TextView(store, scr, 'Help', 'Help'))
        if USE_DEBUG:
            self._debug_view = views.DebugView(scr)
            debug.OUT_FUNC = self._debug_view.out
        self.layout()
        self._reload(0)
        self._set_view(0, False)

    def prompt(self, text_prompt: str, text: str) -> str:
        '''Prompts user to enter or edit some text.'''
        return prompt(self._scr, self._y_get_text, 0, text_prompt, text)

    def _get_keyword(self) -> str:
        return self.prompt('Keyword: ', '')

    def try_start_search(self) -> types.Status:
        '''Tries to initiate a less like search.'''
        v = self._content[self._current]
        if v.has_filters():
            return 'Cannot start search when filters already defined'
        t = self._get_keyword()
        return v.search(t)

    def _toggle_auto_reload(self, anchor: int):
        self._auto_reload = not self._auto_reload
        self._auto_reload_anchor = anchor
        return f'Auto reload {self._auto_reload}'

    def _poll(self) -> Tuple[bool, types.Status]:
        if self._auto_reload:
            mtime = getmtime(self._path)
            if mtime != self._mtime:
                return True, self._reload(self._auto_reload_anchor)
        return False, STATUS_UNCHANGED

    def handle_key(self, key) -> Tuple[bool, types.Status]:
        '''Handles the given key, propagating it to the proper view.'''

        if key == -1:
            # No key, means we are polling view for any self triggered action
            return self._poll()

        # Local functions redirecting to current view v
        v = self._content[self._current]

        if key == curses.KEY_RESIZE:
            self._scr.clear()
            self._scr.refresh()
            size = self.layout()
            v.draw()
            return True, f'Resized to {size[1]}x{size[0]}'

        def new_keyword(new_filter) -> types.Status:
            keyword = self._get_keyword()
            return v.push_keyword(keyword, new_filter)

        def goto_line() -> types.Status:
            line_as_text = self.prompt('Enter line: ', '')
            return v.goto_line(line_as_text)

        def edit_keyword() -> types.Status:
            count, keyword = v.get_last_keyword()
            if count <= 0:
                return 'No keyword to edit'
            keyword = self.prompt('Edit: ', keyword if keyword else '')
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
            curses.KEY_DOWN:       enums.TextViewCommand.GO_DOWN,
            curses.KEY_LEFT:       enums.TextViewCommand.GO_LEFT,
            curses.KEY_RIGHT:      enums.TextViewCommand.GO_RIGHT,
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
            curses.KEY_SRIGHT:     enums.TextViewCommand.GO_SRIGHT,
            ord('d'):              enums.TextViewCommand.SWAP_FILTERS,
            ord('w'):              enums.TextViewCommand.ROTATE_FILTERS_UP,
            ord('s'):              enums.TextViewCommand.ROTATE_FILTERS_DOWN,
            ord('\\'):             enums.TextViewCommand.SLOT_SAVE,
            ord('|'):              enums.TextViewCommand.SLOT_DELETE,
            ord(']'):              enums.TextViewCommand.SLOT_LOAD_NEXT,
            ord('['):              enums.TextViewCommand.SLOT_LOAD_PREV,
        }

        # Map keys to custom functions used to handle more complex commands
        # like ones taking arguments

        # noqa: E272 is "multiple spaces before keyword"
        keys_to_func = {
            ord('1'):
                lambda: self._set_view(0, False),
            ord('2'):
                lambda: self._set_view(1, False),
            ord('3'):
                lambda: self._set_view(2, False),
            ord('!'):
                lambda: self._set_view(0, True),
            ord('@'):
                lambda: self._set_view(1, True),
            ord('#'):
                lambda: self._set_view(2, True),
            ord('?'):
                self._help_view_push,
            ord('e'):
                edit_keyword,
            ord('f'):
                lambda: new_keyword(True),
            ord('\n'):
                lambda: new_keyword(True),
            ord('r'):
                lambda: self._reload(0),
            ord('R'):
                lambda: self._toggle_auto_reload(0),
            ord('t'):
                lambda: self._reload(sys.maxsize),
            ord('T'):
                lambda: self._toggle_auto_reload(sys.maxsize),
            ord('+'):
                lambda: new_keyword(False),
            ord('='):
                lambda: new_keyword(False),
            ord('/'):
                self.try_start_search,
            curses.ascii.TAB:
                goto_line,
            7:
                goto_line,
        }

        inter = keys_to_command.keys() & keys_to_func.keys()
        assert len(inter) == 0, f'Keys with multiple mapping {inter}'
        status: types.Status = ''

        # If help is shown, we hijack keys closing the view but
        # forward all other keys as if it is a regular view (which
        # makes help searchable like a file...)
        if self._hidden_view >= 0 and key in (
                ord('q'), ord('Q'), curses.ascii.ESC):
            self._help_view_pop()
        elif key in keys_to_command:
            status = v.execute(keys_to_command[key])
        elif key in keys_to_func:
            status = types.Status(keys_to_func[key]())
        else:
            return False, f'Unknown key {key} (? for help, q to quit)'

        return True, status
