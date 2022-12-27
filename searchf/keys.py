'''Module abstracting key input.'''

from typing import Any
from typing import List
from typing import Optional

import datetime
import curses
import curses.ascii

from . import enums

# Special key that will result in app being polled
POLL = -1

# Number of seconds to wait before canceling key escape sequence
ESCAPE_TIMEOUT = 0.2


# Map keys to simple text view commands
KEYS_TO_COMMAND = {
    ord('F'):              enums.Command.POP_FILTER,
    curses.KEY_BACKSPACE:  enums.Command.POP_FILTER,
    ord('-'):              enums.Command.POP_KEYWORD,
    ord('_'):              enums.Command.POP_KEYWORD,
    ord('n'):              enums.Command.VSCROLL_TO_NEXT_MATCH,
    ord('p'):              enums.Command.VSCROLL_TO_PREV_MATCH,
    ord('l'):              enums.Command.TOGGLE_LINE_NUMBERS,
    ord('k'):              enums.Command.TOGGLE_WRAP,
    ord('*'):              enums.Command.TOGGLE_BULLETS,
    ord('.'):              enums.Command.TOGGLE_SHOW_SPACES,
    ord('c'):              enums.Command.NEXT_PALETTE,
    ord('C'):              enums.Command.PREV_PALETTE,
    ord('h'):              enums.Command.NEXT_COLORIZE_MODE,
    ord('H'):              enums.Command.PREV_COLORIZE_MODE,
    ord('m'):              enums.Command.NEXT_LINE_VISIBILITY,
    ord('M'):              enums.Command.PREV_LINE_VISIBILITY,
    ord('i'):              enums.Command.TOGGLE_IGNORE_CASE,
    ord('x'):              enums.Command.TOGGLE_HIDING,
    curses.KEY_UP:         enums.Command.GO_UP,
    curses.KEY_DOWN:       enums.Command.GO_DOWN,
    curses.KEY_LEFT:       enums.Command.GO_LEFT,
    curses.KEY_RIGHT:      enums.Command.GO_RIGHT,
    curses.KEY_HOME:       enums.Command.GO_HOME,
    ord('g'):              enums.Command.GO_HOME,
    ord('<'):              enums.Command.GO_HOME,
    curses.KEY_END:        enums.Command.GO_END,
    ord('G'):              enums.Command.GO_END,
    ord('>'):              enums.Command.GO_END,
    curses.KEY_NPAGE:      enums.Command.GO_NPAGE,
    ord(' '):              enums.Command.GO_NPAGE,
    curses.KEY_PPAGE:      enums.Command.GO_PPAGE,
    ord('b'):              enums.Command.GO_PPAGE,
    curses.KEY_SLEFT:      enums.Command.GO_SLEFT,
    curses.KEY_SRIGHT:     enums.Command.GO_SRIGHT,
    ord('d'):              enums.Command.SWAP_FILTERS,
    ord('w'):              enums.Command.ROTATE_FILTERS_UP,
    ord('s'):              enums.Command.ROTATE_FILTERS_DOWN,
    ord('\\'):             enums.Command.SLOT_SAVE,
    ord('|'):              enums.Command.SLOT_DELETE,
    ord(']'):              enums.Command.SLOT_LOAD_NEXT,
    ord('['):              enums.Command.SLOT_LOAD_PREV,
    ord('1'):              enums.Command.SHOW_VIEW_1,
    ord('2'):              enums.Command.SHOW_VIEW_2,
    ord('3'):              enums.Command.SHOW_VIEW_3,
    ord('!'):              enums.Command.SHOW_VIEW_1_WITH_FILTER,
    ord('@'):              enums.Command.SHOW_VIEW_2_WITH_FILTER,
    ord('#'):              enums.Command.SHOW_VIEW_3_WITH_FILTER,
    ord('?'):              enums.Command.SHOW_HELP,
    ord('e'):              enums.Command.EDIT_KEYWORD,
    ord('+'):              enums.Command.PUSH_KEYWORD,
    ord('='):              enums.Command.PUSH_KEYWORD,
    ord('f'):              enums.Command.PUSH_FILTER_AND_KEYWORD,
    ord('\n'):             enums.Command.PUSH_FILTER_AND_KEYWORD,
    ord('r'):              enums.Command.RELOAD_HEAD,
    ord('R'):              enums.Command.RELOAD_HEAD_AUTO,
    ord('t'):              enums.Command.RELOAD_TAIL,
    ord('T'):              enums.Command.RELOAD_TAIL_AUTO,
    ord('/'):              enums.Command.TRY_SEARCH,
    curses.ascii.TAB:      enums.Command.GOTO_LINE,
    curses.ascii.BEL:      enums.Command.GOTO_LINE,
}

KEYS_TO_TEXT = {
    ord(' '):             'SPACE',
    ord('\n'):            'ENTER',
    ord('\t'):            'TAB',
    curses.KEY_BACKSPACE: 'BACKSPACE',
    curses.KEY_UP:        'UP',
    curses.KEY_DOWN:      'DOWN',
    curses.KEY_LEFT:      'LEFT',
    curses.KEY_RIGHT:     'RIGHT',
    curses.KEY_HOME:      'HOME',
    curses.KEY_END:       'END',
    curses.KEY_PPAGE:     'PGUP',
    curses.KEY_NPAGE:     'PGDOWN',
}


def _key_to_text(key: int) -> str:
    if key in KEYS_TO_TEXT:
        return KEYS_TO_TEXT[key]
    return f'{chr(key)}'


class KeyEvent():
    '''Class representing KeyEvent '''
    key: int
    text: str
    cmd: Optional[enums.Command]

    def is_poll(self) -> bool:
        '''Returns whether or not this is the poll key/command'''
        return self.key == POLL

    def __init__(self,
                 key: int = POLL,
                 text: str = '',
                 cmd: Optional[enums.Command] = None):
        self.key = key
        self.text = text
        self.cmd = cmd
        if not cmd and key in KEYS_TO_COMMAND:
            self.cmd = KEYS_TO_COMMAND[key]
        if key == POLL:
            self.text = 'POLL'
        elif not text or len(text) <= 0:
            self.text = _key_to_text(key)


class Provider:
    '''Key press provider, that replaces curses getch()
    implementation when testing.'''
    def __init__(self, keys: List[Any]) -> None:
        self._keys: List[Any] = keys

    def getch(self) -> int:
        '''Gets the next key'''
        key = self._keys.pop(0)
        return key if isinstance(key, int) else ord(key)


# Define strings used for representing key combination
SHIFT = '[1;2'
ALT = '[1;3'
ALT_SHIFT = '[1;4'
CTRL = '[1;5'
CTRL_SHIFT = '[1;6'

UP = 'A'
DOWN = 'B'
RIGHT = 'C'
LEFT = 'D'

ESCAPED_TO_COMMAND = {
    CTRL + UP:     enums.Command.ROTATE_FILTERS_UP,
    ALT + UP:      enums.Command.ROTATE_FILTERS_UP,
    CTRL + DOWN:   enums.Command.ROTATE_FILTERS_DOWN,
    ALT + DOWN:    enums.Command.ROTATE_FILTERS_DOWN,
    CTRL + LEFT:   enums.Command.SWAP_FILTERS,
    ALT + LEFT:    enums.Command.SWAP_FILTERS,
    CTRL + RIGHT:  enums.Command.SWAP_FILTERS,
    ALT + RIGHT:   enums.Command.SWAP_FILTERS,
    SHIFT + UP:    enums.Command.GO_PPAGE,
    SHIFT + DOWN:  enums.Command.GO_NPAGE,
    SHIFT + LEFT:  enums.Command.GO_SLEFT,
    SHIFT + RIGHT: enums.Command.GO_SRIGHT,
    'OH':          enums.Command.GO_HOME,
    'OF':          enums.Command.GO_END,
}


class Processor:
    '''Class that returns key pressed by end-user, handling any required
    decoding of escape sequences.
    '''
    def __init__(self, getch_provider) -> None:
        getch_attr = getattr(getch_provider, 'getch', None)
        assert getch_attr
        assert callable(getch_attr)
        self._getch_provider = getch_provider
        self.escaping_ = False
        self.seq_ = ''
        self.start_: datetime.datetime = datetime.datetime.min

    def process(self, key: int) -> KeyEvent:
        '''Process given key'''
        if key < 0:
            self.escaping_ = False
            return KeyEvent(key)
        if self.escaping_:
            self.seq_ += chr(key)
            delta = datetime.datetime.now() - self.start_
            # debug.out(f'{key} {chr(key)} {str(key)} {delta.total_seconds()}')
            if self.seq_ in ESCAPED_TO_COMMAND:
                self.escaping_ = False
                return KeyEvent(key,
                                self.seq_,
                                ESCAPED_TO_COMMAND[self.seq_])
            if delta.total_seconds() <= ESCAPE_TIMEOUT:
                return KeyEvent()
            # Stop escaping regardless of sequence after 200ms
            self.escaping_ = False
            # Note: we might start escaping again right now...
        if key == curses.ascii.ESC:
            self.start_ = datetime.datetime.now()
            self.escaping_ = True
            self.seq_ = ''
            return KeyEvent()
        assert not self.escaping_
        return KeyEvent(key)

    def get(self) -> KeyEvent:
        '''Wait on next key event typed by user or -1 if none'''
        return self.process(self._getch_provider.getch())
