'''Module abstracting key input.'''

from typing import Any
from typing import List
from typing import Optional

import datetime
import curses
import curses.ascii
import sys

from . import enums

# Special key that will result in app being polled
POLL = -1
UNMAP = -2

# Number of seconds to wait before canceling key escape sequence
ESCAPE_TIMEOUT = 0.1


# Map keys to simple text view commands
KEYS_TO_COMMAND = {
    ord('F'):              enums.Command.POP_FILTER,
    curses.KEY_BACKSPACE:  enums.Command.POP_FILTER,
    curses.ascii.DEL:      enums.Command.POP_FILTER,
    ord('-'):              enums.Command.POP_KEYWORD,
    ord('_'):              enums.Command.POP_KEYWORD,
    ord('n'):              enums.Command.VSCROLL_TO_NEXT_MATCH,
    ord('p'):              enums.Command.VSCROLL_TO_PREV_MATCH,
    ord('l'):              enums.Command.TOGGLE_LINE_NUMBERS,
    ord('k'):              enums.Command.TOGGLE_WRAP,
    ord('*'):              enums.Command.TOGGLE_BULLETS,
    ord('.'):              enums.Command.TOGGLE_SHOW_SPACES,
    ord('`'):              enums.Command.NEXT_SGR_MODE,
    ord('~'):              enums.Command.PREV_SGR_MODE,
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
    ord('q'):              enums.Command.QUIT,
    ord('Q'):              enums.Command.QUIT,
    curses.KEY_RESIZE:     enums.Command.RESIZE,
}

MOUSE_STATE_TO_CMD = {}

MOUSE_STATE_TO_CMD[curses.BUTTON4_PRESSED] = enums.Command.GO_UP
if getattr(curses, 'BUTTON5_PRESSED', None):
    MOUSE_STATE_TO_CMD[curses.BUTTON5_PRESSED] = enums.Command.GO_DOWN
    # If BUTTON5_PRESSED is not defined, we need to workaround it see:
    # https://github.com/peterbrittain/asciimatics/issues/345
    # https://github.com/python/cpython/issues/91132
elif sys.platform == 'darwin':
    # mac use old curses (see https://github.com/python/cpython/issues/91132)
    MOUSE_STATE_TO_CMD[0x8000000] = enums.Command.GO_DOWN
else:
    # we assume PDCurses
    # https://github.com/mattn/pdcurses/blob/master/curses.h#L194
    MOUSE_STATE_TO_CMD[0x200000] = enums.Command.GO_DOWN


KEYS_TO_TEXT = {
    POLL:                 'POLL',
    UNMAP:                'UNMAP',
    curses.ascii.ESC:     'ESC',
    curses.ascii.DEL:     'DELETE',
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
    curses.KEY_MOUSE:     'MOUSE',
    curses.KEY_RESIZE:    'RESIZE',
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
        if not text or len(text) <= 0:
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


# Some OS are eating up lots of dead key + arrow combinations
ESCAPED_TO_COMMAND = {
    chr(curses.KEY_UP):    enums.Command.ROTATE_FILTERS_UP,
    CTRL + UP:             enums.Command.ROTATE_FILTERS_UP,
    CTRL_SHIFT + UP:       enums.Command.ROTATE_FILTERS_UP,
    ALT + UP:              enums.Command.ROTATE_FILTERS_UP,
    chr(curses.KEY_DOWN):  enums.Command.ROTATE_FILTERS_DOWN,
    CTRL + DOWN:           enums.Command.ROTATE_FILTERS_DOWN,
    ALT + DOWN:            enums.Command.ROTATE_FILTERS_DOWN,
    CTRL_SHIFT + DOWN:     enums.Command.ROTATE_FILTERS_DOWN,
    chr(curses.KEY_LEFT):  enums.Command.SWAP_FILTERS,
    CTRL + LEFT:           enums.Command.SWAP_FILTERS,
    CTRL_SHIFT + LEFT:     enums.Command.SWAP_FILTERS,
    ALT + LEFT:            enums.Command.SWAP_FILTERS,
    chr(curses.KEY_RIGHT): enums.Command.SWAP_FILTERS,
    CTRL + RIGHT:          enums.Command.SWAP_FILTERS,
    CTRL_SHIFT + RIGHT:    enums.Command.SWAP_FILTERS,
    ALT + RIGHT:           enums.Command.SWAP_FILTERS,
    SHIFT + UP:            enums.Command.GO_PPAGE,
    SHIFT + DOWN:          enums.Command.GO_NPAGE,
    SHIFT + LEFT:          enums.Command.GO_SLEFT,
    SHIFT + RIGHT:         enums.Command.GO_SRIGHT,
    'OH':                  enums.Command.GO_HOME,
    'OF':                  enums.Command.GO_END,
}


class Processor:
    '''Class that returns key pressed by end-user, handling any required
    decoding of escape sequences.
    '''
    def __init__(self, getch_provider, getmouse_provider) -> None:
        getch_attr = getattr(getch_provider, 'getch', None)
        assert getch_attr
        assert callable(getch_attr)
        self._getch_provider = getch_provider
        getmouse_attr = getattr(getmouse_provider, 'getmouse', None)
        assert getmouse_attr
        assert callable(getmouse_attr)
        self._getmouse_provider = getmouse_provider
        self._escaping = False
        self._seq = ''
        self.start_: datetime.datetime = datetime.datetime.min

    def _start_esc(self) -> None:
        self.start_ = datetime.datetime.now()
        self._escaping = True
        self._seq = ''

    def _stop_esc(self) -> str:
        seq = self._seq
        self._escaping = False
        self._seq = ''
        return seq

    def process(self, key: int) -> KeyEvent:
        '''Process given key'''
        # pylint: disable=too-many-return-statements

        if not self._escaping:
            if key == curses.KEY_MOUSE:
                state = self._getmouse_provider.getmouse()[4]
                if state in MOUSE_STATE_TO_CMD:
                    return KeyEvent(key, '', MOUSE_STATE_TO_CMD[state])
                key = POLL
            elif key == curses.ascii.ESC:
                self._start_esc()
                key = POLL
            return KeyEvent(key)

        assert self._escaping
        if key == curses.ascii.ESC:
            # Trash unrecognized sequence, and start again
            self._start_esc()
            return KeyEvent(POLL)
        if key < 0:
            # Assume sequence timed out
            seq = self._stop_esc()
            if len(seq) <= 0:
                # Emtpy escaped sequence, we remit the ESC key we swallowed
                key = curses.ascii.ESC
            else:
                # The sequence we captured is unrecognised
                key = UNMAP
            return KeyEvent(key, seq, None)
        delta = datetime.datetime.now() - self.start_
        if delta.total_seconds() > ESCAPE_TIMEOUT:
            # Stop escaping regardless of sequence after 200ms
            seq = self._stop_esc()
            return KeyEvent(key)

        # Ok to store key in sequence
        self._seq += chr(key)
        # debug.out(f'{key} {chr(key)} {str(key)} {delta.total_seconds()}')
        if self._seq not in ESCAPED_TO_COMMAND:
            return KeyEvent(POLL)
        seq = self._stop_esc()
        cmd = ESCAPED_TO_COMMAND[seq]
        return KeyEvent(key, seq, cmd)

    def get(self) -> KeyEvent:
        '''Wait on next key event typed by user or -1 if none'''
        return self.process(self._getch_provider.getch())
