'''Unit tests for keys'''

import time

from .. import keys
from .. import enums


def test_processor():
    '''Test keys.Processor'''
    proc = keys.Processor(keys.Provider([ord('a')]))
    assert proc
    assert ord('a') == proc.get().key


def test_process():
    '''Test keys.Process'''
    proc = keys.Processor(keys.Provider([]))
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

    # Make sure we timeout while escaping
    keys.ESCAPE_TIMEOUT = 0.01
    key = proc.process(27)
    assert proc.escaping_
    assert key.key == -1
    time.sleep(0.05)
    key = proc.process(ord('A'))
    assert key.key == ord('A')
