'''Module holding general utilities'''

import sys


def wrapper(force, func, /, *args):
    '''Helper function that wraps given function (eg curses.wrapper) so
    that print() statements gets bufferized and dumped to stdout in
    case func raises any exception. This allows seeing the output of
    debug print() statements which are otherwize lost as curses traps
    stdout for its own use.'''

    class StdBuffer:
        '''Helper class to bufferize stdout and stderr'''
        def __init__(self):
            self._lines = []

        def write(self, line):
            '''Write current line'''
            self._lines.append(line)

        def get(self):
            '''Get all the lines that were bufferized'''
            return ''.join(self._lines)

    buf = StdBuffer()
    sys.stdout = buf
    sys.stderr = buf

    error = None
    # pylint: disable=broad-except
    try:
        func(*args)
    except Exception as ex:
        error = ex

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    if force or error:
        print('== Start of bufferized stdout and stderr ==')
        print(buf.get())
        print('== End of bufferized stdout and stderr ==')

    if error:
        print('== Exception ==')
        raise error
