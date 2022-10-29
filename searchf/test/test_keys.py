'''Unit tests for keys'''

import time
import curses

from .. import keys

def test_processor():
    '''Test keys.Processor'''
    proc = keys.Processor(keys.Provider([]))
    assert proc

    key = proc.process(-1)
    assert key == -1

    key = proc.process(ord('a'))
    assert key == ord('a')
    key = proc.process(ord('A'))
    assert key == ord('A')

    for k in '\x1b[1;2C':
        key = proc.process(ord(k))
        assert key in (-1, curses.KEY_SRIGHT)

    key = proc.process(ord('A'))
    assert key == ord('A')

    for k in '\x1b[1;2C':
        key = proc.process(ord(k))
        assert key in (-1, curses.KEY_SRIGHT)

    # Make sure we timeout while escaping
    keys.ESCAPE_TIMEOUT = 0.01
    key = proc.process(27)
    assert proc.escaping_
    assert key == -1
    time.sleep(0.05)
    key = proc.process(ord('A'))
    assert key == ord('A')
