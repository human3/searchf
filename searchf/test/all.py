'''Application end-to-end tests.
'''

import argparse
import curses
import os
import time

from typing import List
from typing import NamedTuple
from contextlib import contextmanager

from .. import main
from .. import app
from .. import colors
from .. import debug
from .. import keys
from .. import storage
from .. import utils

from . import test_enums
from . import test_keys
from . import test_models
from . import test_segments
from . import test_storage

TEST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'sample.txt')


class KeywordsInjector:
    '''Class that emulates end-user entering keywords. Provides a
    get_text() function that can replace the one in the main module.
    '''
    def __init__(self, keywords: List[str]):
        self._keywords = keywords

    def get_next(self) -> str:
        '''Returns the next keyword'''
        return self._keywords.pop(0)

    def get_text(self, scr, y, x, text_prompt: str, handler, text: str) -> str:
        '''Function to replace main.get_next'''
        # pylint: disable=unused-argument
        return self.get_next()


class MtimeInjector:
    '''Class that emulates end-user externally changing file. Provides
    a getmtime() function that can replace the one in the main module,
    and that makes sure the file always changes.'''

    def __init__(self):
        self._time = 0.0

    def getmtime(self, path: str) -> float:
        '''Returns the file last modification time'''
        # pylint: disable=unused-argument
        self._time += 1
        return self._time


# Screen size used for tests, terminal must be bigger for
# tests to run
TEST_SIZE = (30, 60)


@contextmanager
def main_modifier(stdscr,
                  keywords_injector: KeywordsInjector,
                  mtime_injector: MtimeInjector):
    '''Context manager that replaces key and text input methods of the main
    module, and makes sure tests are run always with same screen
    resolution.
    '''

    size = app.get_max_yx(stdscr)
    assert size[0] >= TEST_SIZE[0], f'{size} < {TEST_SIZE}'
    assert size[1] >= TEST_SIZE[1], f'{size} < {TEST_SIZE}'

    def _injected_get_max_yx(_):
        return TEST_SIZE

    get_text = app.get_text
    getmtime = app.getmtime
    get_max_yx = app.get_max_yx
    app.get_text = keywords_injector.get_text
    app.getmtime = mtime_injector.getmtime
    app.get_max_yx = _injected_get_max_yx
    try:
        yield
    finally:
        app.get_text = get_text
        app.getmtime = getmtime
        app.get_max_yx = get_max_yx


class AppTest(NamedTuple):
    '''Model data associated with a test:
    - the description of the test
    - the list of keys that will be sequentially automatically pressed
      by test runner
    - the list of text input that will be automatically fed to the
      application
    '''
    description: str
    keys: List[str]
    inputs: List[str]


HANDLE_KEY_DELAY = 0.01


def _run(stdscr, t: AppTest):
    '''Helper function to run the given AppTest'''
    print(t.description)
    stdscr.clear()
    colors.init()
    store = storage.Store('.searchf.test')
    with main_modifier(stdscr,
                       KeywordsInjector(t.inputs),
                       MtimeInjector()):
        main.APP.create(store, stdscr, TEST_FILE)
        for key in t.keys:
            stdscr.refresh()
            # Add sleep just to see something, test can run without it
            time.sleep(HANDLE_KEY_DELAY)
            i = key if isinstance(key, int) else ord(key)
            main.APP.handle_key(keys.map_key_to_command(i))
    store.destroy()


def _test_main_init_env():
    print('Test main.init_env()')
    parser = main.init_env()
    assert parser


def _test_main_get_text(stdscr):
    print('Test main.get_text()')

    def my_handler(_):
        pass

    def my_handler_throwing(_):
        raise app.EscapeException

    app.get_text(stdscr, 0, 0,
                 "Testing prompt", my_handler, 'Editable content')
    app.get_text(stdscr, 0, 0,
                 "Testing prompt", my_handler_throwing, '')


def _test_app_validate():
    print('Test app.validate()')
    assert app.validate('a') == 'a'
    assert app.validate(curses.ascii.DEL) == curses.KEY_BACKSPACE
    actual = None
    try:
        app.validate(curses.ascii.ESC)
    except app.EscapeException as ex:
        actual = ex
    assert actual


def _test_main_main_loop(stdscr):
    print('Test main.main_loop()')
    keys_processor = keys.Processor(keys.Provider(
        [' ', '>', 'l', keys.POLL, 'q']))
    main.main_loop(stdscr, TEST_FILE, False, keys_processor)


def _test_main_resize(stdscr):
    print('Test main.resize')
    keys_processor = keys.Processor(keys.Provider([curses.KEY_RESIZE, 'q']))
    main.main_loop(stdscr, TEST_FILE, False, keys_processor)


def _test_main_debug_view(stdscr):
    # Test debug mode in a very hacky way by hijacking handle_key function
    # and spitting out a few dummy debug lines per key press
    app.USE_DEBUG = True
    original_handle_key = main.APP.handle_key

    def my_handle_key(key):
        for i in range(20):
            debug.out(f'Test {i} dbg {key}')
        return original_handle_key(key)

    main.APP.handle_key = my_handle_key
    _run(stdscr, AppTest(
        'Test special debug mode',
        ['/', 'n', 'n', 'n', 'p', 'p'], ['filter']))
    main.APP.handle_key = original_handle_key
    app.USE_DEBUG = False


# This is poor man's testing, as we don't validate much other than
# just making sure things don't blow up when executing common commands
# (cf all assert in code). By maintaining code coverage above 95%,
# these tests are still very useful to catch regression when
# refactoring.
def _run_app_tests(stdscr):

    # Log param, that might be useful to repro any issue
    print(f'TEST_FILE = {TEST_FILE}')
    print(f'stdscr.getmaxyx() = {stdscr.getmaxyx()}')
    print()

    app_tests = [
        AppTest('Test keywords that are invalid regex',
                ['f'], ['?']),
        AppTest('Test that help can get displayed',
                ['?', 'q'], []),
        AppTest('Test view switching',
                ['r', 't', '1', '2', '3', '!', '@', '#'], []),
        AppTest('Test reloading',
                ['r', 't', keys.POLL, 'R', keys.POLL, 'R', 'T', 'T'], []),
        AppTest('Test scrolling around',
                ['>', '<', ' ', 'b'], []),
        AppTest('Test scrolling horizontally',
                [curses.KEY_RIGHT, curses.KEY_LEFT], []),
        AppTest('Test goto lines',
                ['\t', '\t', '\t', '\t'], ['5', '99999', 'bad', '0']),
        AppTest('Test various display modes',
                ['l', 'k', 'k', '.', '.', '*', '*', 'm', 'M', 'm'], []),
        AppTest('Test entering one letter keywords',
                ['+', '+', 'f', 'f', 'v', 'h', 'h', 'v', 'v', 'V', 'c', 'c',
                 'F', '-', '-', '-', '+'],
                ['a', 'b', 'c', 'd', '']),
        AppTest('Test entering keywords',
                ['+', '+', 'f', 'f', 'm', 'h', 'h', 'H', 'm', 'c', 'C', 'F',
                 '-', '-', '-', '+'],
                ['filter', 'keyword', 'for', 'python', '']),
        AppTest('Test entering empty keywords, poping non existent keywords',
                ['+', 'f', '-', 'F'],
                ['', '']),
        AppTest('Test editing keywords',
                ['e', '+', 'e', 'e'],
                ['something', 'good', '']),
        AppTest('Test keyword search',
                ['/', 'n', 'n', 'n', 'p', 'p', 'p', 'p', '/'],
                ['filter']),
        AppTest('Test case sensitive search',
                ['i', '/', 'i', 'i'],
                ['Show']),
        AppTest('Test toggling hiden/shown filter',
                ['x', 'f', 'x', 'x'],
                ['Show']),
        AppTest('Test swapping filters',
                ['d', 'f', 'f', 'd'],
                ['key', 'python']),
        AppTest('Test rotating filters',
                ['w', 'f', 'f', 'w', 's'],
                ['key', 'python']),
        AppTest('Test save/load/delete slots',
                ['[', '\\', '|', 'f', 'f', '\\', '\\', '[', ']', '|'],
                ['key', 'python']),
    ]

    for test in app_tests:
        _run(stdscr, test)

    _test_main_init_env()
    _test_main_get_text(stdscr)
    _test_app_validate()
    _test_main_main_loop(stdscr)
    _test_main_resize(stdscr)
    _test_main_debug_view(stdscr)


def _run_unit_tests():
    print('Test enums.test_get_next_prev()')
    test_enums.test_get_next_prev()
    print('Test enums.test_from_int()')
    test_enums.test_from_int()
    print('Test enums.test_repr()')
    test_enums.test_repr()
    print('Test segments.iterate()')
    test_segments.test_iterate()
    print('Test segments._sort_and_merge()')
    test_segments.test_sort_and_merge()
    print('Test segments.find_matching()')
    test_segments.test_find_matching()
    print('Test models.test_filter()')
    test_models.test_filter()
    print('Test models.test_digit_count()')
    test_models.test_digit_count()
    print('Test models.test_model()')
    test_models.test_model()
    print('Test models.test_display_content()')
    test_models.test_display_content()
    print('Test models.test_offsets()')
    test_models.test_offsets()
    print('Test models.test_view_config()')
    test_models.test_view_config()
    print('Test keys.test_processor()')
    test_keys.test_process()
    print('Test keys.test_process()')
    test_keys.test_processor()
    print('Test storage.test_strore()')
    test_storage.test_store()


def _test_main_main():
    print('Test main.main()')

    # We use a context manager that replaces main.init_env and
    # keys.Processor in order to be able to load main.main as if it was
    # invoked by end-user

    def _init_env():
        parser = argparse.ArgumentParser(description='Dummy parser')
        parser.add_argument('-file', default=TEST_FILE)
        parser.add_argument('-debug', default=False)
        print('test_env')
        return parser

    class _KeysProcessor:
        def __init__(self, _):
            self._keys = [-1, ord('<')]

        def get(self):
            '''Get next key'''
            if len(self._keys) <= 0:
                raise KeyboardInterrupt
            return self._keys.pop(0)

    @contextmanager
    def _main_modifier():
        keys_processor = keys.Processor
        init_env = main.init_env
        keys.Processor = _KeysProcessor
        main.init_env = _init_env
        try:
            yield
        finally:
            keys.Processor = keys_processor
            main.init_env = init_env

    with _main_modifier():
        main.main()


def test_main():
    '''Test entry point'''
    print('== Tests started ==')
    _run_unit_tests()
    utils.wrapper(True, curses.wrapper, _run_app_tests)
    _test_main_main()
    print('== Tests passed ==')


if __name__ == '__main__':
    test_main()
