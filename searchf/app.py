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
from . import keys
from . import types
from . import views

# Changes layout to show a debug window in which debug() function will output
USE_DEBUG = False

STATUS_UNCHANGED = 'unchanged'


def load_lines(path: str) -> List[str]:
    '''Load all the lines of the given file.'''
    with open(path, encoding='utf-8') as f:
        # splitlines() ensures that any newline char is removed
        return f.read().splitlines()


def get_max_yx(scr) -> types.Size:
    '''This function is a test artifact that wraps getmaxyx() from curses so
    that we can overwrite it and test specific dimensions.
    '''
    return scr.getmaxyx()


def getmtime(path):
    '''Wraps os.getmtime() for testing.'''
    return os.path.getmtime(path)


class EscapeException(Exception):
    '''Signals that Escape key has been pressed.'''


def validate(k: int) -> int:
    '''Validates key.'''
    if k == curses.ascii.DEL:
        k = curses.KEY_BACKSPACE
    elif k == curses.ascii.ESC:
        raise EscapeException()
    return k


def get_text(*, scr, y: int, x: int, text_prompt: str, handler, text: str) -> str:
    '''Gets text interactively from end user.'''
    _, maxw = get_max_yx(scr)
    scr.addstr(y, x, text_prompt)
    x += len(text_prompt)
    width = max(0, maxw - x)
    editwin = curses.newwin(1, width, y, x)
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
    return get_text(scr=scr, y=y, x=x,
                    text_prompt=text_prompt, handler=handle, text=text)


def clear(scr, y: int, x: int, length: int):
    '''Prints "length" spaces at the given position.'''
    _, maxw = get_max_yx(scr)
    blank = f'{" ":>{length}}'
    scr.addstr(y, x, blank[:maxw-(x+1)])
    scr.move(y, x)


class App:
    '''Aggregates all views, controlling which ones are visible, handling
    key presses and command dispatching.'''

    # pylint: disable=too-many-instance-attributes

    def __init__(self, help_lines: List[str]) -> None:
        self._help_lines: List[str] = help_lines
        self._debug_view: views.DebugView
        self._event_view: views.KeyEventView
        self._scr: Any = None
        self._margins: types.Margins = types.Margins()
        self._show_events: bool = False
        self._path: str = ''
        self._views: List[views.TextView] = []
        self._help_view_index: int = -1
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
        maxh -= (self._margins.top + self._margins.bottom)
        maxw -= (self._margins.left + self._margins.right)
        x = self._margins.left
        y = self._margins.top

        if self._show_events:
            self._event_view.layout(y, x, 2, maxw)
            y += 2
            maxh -= 2

        view_lines_count = maxh

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

        for v in self._views:
            v.layout(view_lines_count, maxw, y, x)

        y += view_lines_count
        self._y_get_text = y
        return maxh, maxw

    def _set_view(self, idx: int, propagate_config: bool) -> types.Status:
        assert 0 <= idx < len(self._views)
        if self._current == idx:
            return f'Current view is already {self._views[idx].name()}'
        self._hidden_view = \
            self._current if idx == self._help_view_index else -1
        config = self._views[self._current].get_config()
        self._current = idx
        if propagate_config:
            self._views[idx].set_config(copy.deepcopy(config))
        self._views[idx].show()
        return f'Switched to {self._views[idx].name()}'

    def _help_view_push(self) -> types.Status:
        return self._set_view(self._help_view_index, False)

    def _help_view_pop(self) -> types.Status:
        assert self._hidden_view >= 0
        return self._set_view(self._hidden_view, False)

    def _reload(self, scroll_to: int) -> types.Status:
        lines = load_lines(self._path)
        for i, v in enumerate(self._views):
            if i == self._help_view_index:
                v.set_lines(self._help_lines)
            else:
                v.set_lines(lines)
                v.set_v_offset(scroll_to, False)
        self._views[self._current].draw()
        self._mtime = getmtime(self._path)
        return 'File reloaded'

    def create(
            self,
            *,
            store,
            scr,
            margins: types.Margins,
            show_events: bool,
            path: str,
    ) -> None:
        '''Creates all views in the given screen, and loads the content from
        the given file.'''
        self._scr = scr
        self._margins = margins
        self._show_events = show_events
        self._path = path
        self._views.clear()
        self._views.append(views.TextView(store, scr, 'View 1', path))
        self._views.append(views.TextView(store, scr, 'View 2', path))
        self._views.append(views.TextView(store, scr, 'View 3', path))
        self._views.append(views.TextView(store, scr, 'Help', 'Help'))
        self._help_view_index = len(self._views) - 1
        self._views[self._help_view_index].get_config().line_numbers = False
        if USE_DEBUG:
            self._debug_view = views.DebugView(scr)
            debug.OUT_FUNC = self._debug_view.out
        self._event_view = views.KeyEventView(scr)
        self.layout()
        self._reload(0)
        self._set_view(0, False)

    def prompt(self, text_prompt: str, text: str) -> str:
        '''Prompts user to enter or edit some text.'''
        return prompt(self._scr,
                      self._y_get_text,
                      self._margins.left,
                      text_prompt,
                      text)

    def _get_keyword(self) -> str:
        return self.prompt('Keyword: ', '')

    def try_start_search(self) -> types.Status:
        '''Tries to initiate a less like search.'''
        v = self._views[self._current]
        if v.has_filters():
            return 'Cannot start search when filters already defined'
        t = self._get_keyword()
        return v.search(t)

    def _toggle_auto_reload(self, anchor: int) -> types.Status:
        self._auto_reload = not self._auto_reload
        self._auto_reload_anchor = anchor
        return f'Auto reload {self._auto_reload}'

    def _poll(self) -> Tuple[bool, types.Status]:
        if self._auto_reload:
            mtime = getmtime(self._path)
            if mtime != self._mtime:
                return True, self._reload(self._auto_reload_anchor)
        return False, STATUS_UNCHANGED

    def handle_event(
            self,
            ev: keys.KeyEvent,
    ) -> Tuple[bool, types.Status]:
        '''Handles the given key, propagating it to the proper view.'''

        if self._show_events:
            self._event_view.show(ev)

        if ev.is_poll():
            return self._poll()

        # Local functions redirecting to current view v
        v = self._views[self._current]

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
            v.execute(enums.Command.POP_KEYWORD)
            v.push_keyword(keyword, count == 1)
            return 'Keyword updated'

        def resize() -> types.Status:
            self._scr.clear()
            self._scr.refresh()
            size = self.layout()
            v.draw()
            return f'Resized to {size[1]}x{size[0]}'

        # Map the commands requiring custom functions and that
        # cannot be directly sent over the current view.
        cmd_to_func = {
            enums.Command.SHOW_VIEW_1:
                lambda: self._set_view(0, False),
            enums.Command.SHOW_VIEW_2:
                lambda: self._set_view(1, False),
            enums.Command.SHOW_VIEW_3:
                lambda: self._set_view(2, False),
            enums.Command.SHOW_VIEW_1_WITH_FILTER:
                lambda: self._set_view(0, True),
            enums.Command.SHOW_VIEW_2_WITH_FILTER:
                lambda: self._set_view(1, True),
            enums.Command.SHOW_VIEW_3_WITH_FILTER:
                lambda: self._set_view(2, True),
            enums.Command.SHOW_HELP:
                self._help_view_push,
            enums.Command.EDIT_KEYWORD:
                edit_keyword,
            enums.Command.PUSH_KEYWORD:
                lambda: new_keyword(False),
            enums.Command.PUSH_FILTER_AND_KEYWORD:
                lambda: new_keyword(True),
            enums.Command.RELOAD_HEAD:
                lambda: self._reload(0),
            enums.Command.RELOAD_HEAD_AUTO:
                lambda: self._toggle_auto_reload(0),
            enums.Command.RELOAD_TAIL:
                lambda: self._reload(sys.maxsize),
            enums.Command.RELOAD_TAIL_AUTO:
                lambda: self._toggle_auto_reload(sys.maxsize),
            enums.Command.TRY_SEARCH:
                self.try_start_search,
            enums.Command.GOTO_LINE:
                goto_line,
            enums.Command.RESIZE:
                resize,
        }

        handled: bool = True  # Assumed until otherwise
        status: types.Status = ''
        if ev.cmd == enums.Command.QUIT or ev.key == curses.ascii.ESC:
            if self._hidden_view < 0:
                handled = False
            else:
                status = self._help_view_pop()
        elif ev.cmd in cmd_to_func:
            status = cmd_to_func[ev.cmd]()
        elif ev.cmd:
            status = v.execute(ev.cmd)
        else:
            handled = False
            status = f'Unknown key {ev.text} (? for help, q to quit)'

        return handled, status
