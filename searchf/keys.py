'''Module abstracting key input.'''

from typing import List

import datetime
import curses
import curses.ascii

# Special key that will make _my_get_ch return -1 and result in app being polled
POLL = 'POLL'

# Number of seconds to wait before canceling key escape sequence
ESCAPE_TIMEOUT = 0.2

class Processor:
    '''Class that returns key pressed by end-user, handling any required
    decoding of escape sequences.'''
    def __init__(self, scr) -> None:
        self.scr_ = scr
        self.test_keys_: List[str] = []
        self.escaping_ = False
        self.seq_ = ''
        self.start_: datetime.datetime = datetime.datetime.min
        self.map_ = {
            '[1;2A': curses.KEY_PPAGE,
            '[1;2B': curses.KEY_NPAGE,
            '[1;2D': curses.KEY_SLEFT,
            '[1;2C': curses.KEY_SRIGHT,
            'OH': curses.KEY_HOME,
            'OF': curses.KEY_END,
        }

    def inject_test_keys(self, test_keys: List[str]) -> None:
        '''Inject the given list of keys for testing purposes'''
        self.test_keys_ = test_keys

    def process_(self, key) -> int:
        '''Process given key'''
        if key < 0:
            self.escaping_ = False
            return key
        if self.escaping_:
            self.seq_ += chr(key)
            delta = datetime.datetime.now() - self.start_
            # debug.out(f'{key} {chr(key)} {str(key)} {delta.total_seconds()}')
            if self.seq_ in self.map_:
                self.escaping_ = False
                return self.map_[self.seq_]
            if delta.total_seconds() <= ESCAPE_TIMEOUT:
                return -1
            # Stop escaping regardless of sequence after 200ms
            self.escaping_ = False
            # Note: we might start escaping again right now...
        if key == curses.ascii.ESC:
            self.start_ = datetime.datetime.now()
            self.escaping_ = True
            self.seq_ = ''
            return -1
        assert not self.escaping_
        return key

    def get(self):
        '''Returns key typed by user or -1 if none'''
        if len(self.test_keys_) > 0:
            key = self.test_keys_.pop()
            return -1 if key == POLL else ord(key)

        return self.process_(self.scr_.getch())
