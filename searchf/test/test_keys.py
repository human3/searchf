'''Unit tests for keys'''

import time
import curses

from .. import keys


def test_processor():
    '''Test keys.Processor'''
    proc = keys.Processor(None)
    assert proc

    key = proc.process_(-1)
    assert key == -1

    key = proc.process_(ord('a'))
    assert key == ord('a')
    key = proc.process_(ord('A'))
    assert key == ord('A')

    for k in '\x1b[1;2C':
        key = proc.process_(ord(k))
        assert key in (-1, curses.KEY_SRIGHT)

    key = proc.process_(ord('A'))
    assert key == ord('A')

    for k in '\x1b[1;2C':
        key = proc.process_(ord(k))
        assert key in (-1, curses.KEY_SRIGHT)

    keys.ESCAPE_TIMEOUT = 0.01
    key = proc.process_(27)
    assert proc.escaping_
    assert key == -1
    time.sleep(0.05)
    key = proc.process_(ord('A'))
    assert key == ord('A')
