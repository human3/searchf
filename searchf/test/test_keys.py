'''Unit tests for keys'''

import time
import curses

from .. import keys
from .. import enums


class MouseProvider:
    '''Class providing a getmouse() function similar to curses.getmouse().'''
    def getmouse(self):
        '''Mocks curses.getmouse().'''
        assert False  # pragma: no cover


def test_processor():
    '''Test keys.Processor'''
    proc = keys.Processor(keys.Provider([ord('a')]), MouseProvider())
    assert proc
    assert ord('a') == proc.get().key


def test_process():
    '''Test keys.Process'''
    proc = keys.Processor(keys.Provider([]), MouseProvider())
    assert proc

    key = proc.process(-1)
    assert key.key == -1

    key = proc.process(ord('a'))
    assert key.key == ord('a')
    key = proc.process(ord('A'))
    assert key.key == ord('A')

    for k in '\x1b[1;2C':
        key = proc.process(ord(k))
        assert key.key == -1 or key.cmd == enums.Command.GO_SRIGHT

    key = proc.process(ord('A'))
    assert key.key == ord('A')

    for k in '\x1b[1;2C':
        key = proc.process(ord(k))
        assert key.key == -1 or key.cmd == enums.Command.GO_SRIGHT

    for k in '\x1bZ\x1b':
        key = proc.process(ord(k))
        assert key.key == -1

    # Make sure we spit out ESC if polling right after escaping
    key = proc.process(27)
    assert key.key == keys.POLL
    key = proc.process(-1)
    assert key.key == curses.ascii.ESC

    # Make sure we spit out UNMAP if polling in middle of unrecognize seq
    key = proc.process(27)
    assert key.key == keys.POLL
    key = proc.process(ord('['))
    assert key.key == keys.POLL
    key = proc.process(-1)
    assert key.key == keys.UNMAP

    # Make sure we timeout while escaping
    keys.ESCAPE_TIMEOUT = 0.01
    key = proc.process(27)
    assert key.key == -1
    time.sleep(0.05)
    key = proc.process(ord('A'))
    assert key.key == ord('A')
