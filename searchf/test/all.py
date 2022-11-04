'''Application end-to-end tests.
'''

import argparse
import curses
import os
import time

from typing import List
from typing import NamedTuple
from contextlib import contextmanager

from .. import app
from .. import colors
from .. import debug
from .. import keys
from .. import storage
from .. import utils
from .. import views

from . import test_enums
from . import test_keys
from . import test_models
from . import test_segments
from . import test_storage

TEST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'sample.txt')


class KeywordsInjector:
    '''Class that emulates end-user entering keywords. Provides a
    get_text() function that can replace the one in the app module.
    '''
    def __init__(self, keywords: List[str]):
        self._keywords = keywords

    def get_next(self) -> str:
        '''Returns the next keyword'''
        return self._keywords.pop(0)

    def get_text(self, scr, y, x, text_prompt: str, handler, text: str) -> str:
        '''Function to replace app.get_next'''
        # pylint: disable=unused-argument
        return self.get_next()


class MtimeInjector:
    '''Class that emulates end-user externally changing file. Provides
    a getmtime() function that can replace the one in the app module,
    and that makes sure the file always changes.'''

    def __init__(self):
        self._time = 0.0

    def getmtime(self, path: str) -> float:
        '''Returns the file last modification time'''
        # pylint: disable=unused-argument
        self._time += 1
        return self._time


@contextmanager
def app_modifier(keywords_injector: KeywordsInjector,
                 mtime_injector: MtimeInjector):
    '''Context manager that replaces key and text input methods of the app
    module, and makes sure tests are run always with same screen
    resolution
    '''

    def _injected_get_max_yx(_):
        return 30, 80

    get_text = views.get_text
    getmtime = views.getmtime
    get_max_yx = views.get_max_yx
    views.get_text = keywords_injector.get_text
    views.getmtime = mtime_injector.getmtime
    views.get_max_yx = _injected_get_max_yx
    try:
        yield
    finally:
        views.get_text = get_text
        views.getmtime = getmtime
        views.get_max_yx = get_max_yx


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


def _run(stdscr, t: AppTest):
    '''Helper function to run the given AppTest'''
    print(t.description)
    stdscr.clear()
    colors.init()
    store = storage.Store('.searchf.test')
    with app_modifier(KeywordsInjector(t.inputs), MtimeInjector()):
        app.VIEWS.create(store, stdscr, TEST_FILE)
        for key in t.keys:
            stdscr.refresh()
            # Add sleep just to see something, test can run without it
            time.sleep(0.01)
            app.VIEWS.handle_key(key if isinstance(key, int) else ord(key))
    store.destroy()


def _test_app_init_env():
    print('Test app.init_env()')
    parser = app.init_env()
    assert parser


def _test_app_get_text(stdscr):
    print('Test app.get_text()')

    def my_handler(_):
        pass

    def my_handler_throwing(_):
        raise views.EscapeException

    views.get_text(stdscr, 0, 0,
                   "Testing prompt", my_handler, 'Editable content')
    views.get_text(stdscr, 0, 0,
                   "Testing prompt", my_handler_throwing, '')


def _test_app_validate():
    print('Test views.validate()')
    assert views.validate('a') == 'a'
    assert views.validate(curses.ascii.DEL) == curses.KEY_BACKSPACE
    actual = None
    try:
        views.validate(curses.ascii.ESC)
    except views.EscapeException as ex:
        actual = ex
    assert actual


def _test_app_main_loop(stdscr):
    print('Test app.main_loop()')
    keys_processor = keys.Processor(keys.Provider(
        [' ', '>', 'l', keys.POLL, 'q']))
    app.main_loop(stdscr, TEST_FILE, keys_processor)


def _test_app_resize(stdscr):
    print('Test app.resize')
    keys_processor = keys.Processor(keys.Provider([curses.KEY_RESIZE, 'q']))
    app.main_loop(stdscr, TEST_FILE, keys_processor)


def _test_app_debug_view(stdscr):
    # Test debug mode in a very hacky way by hijacking handle_key function
    # and spitting out a few dummy debug lines per key press
    views.USE_DEBUG = True
    original_handle_key = app.VIEWS.handle_key

    def my_handle_key(key):
        for i in range(20):
            debug.out(f'Test {i} dbg {key}')
        return original_handle_key(key)

    app.VIEWS.handle_key = my_handle_key
    _run(stdscr, AppTest(
        'Test special debug mode',
        ['/', 'n', 'n', 'n', 'p', 'p'], ['filter']))
    app.VIEWS.handle_key = original_handle_key
    views.USE_DEBUG = False


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

    _test_app_init_env()
    _test_app_get_text(stdscr)
    _test_app_validate()
    _test_app_main_loop(stdscr)
    _test_app_resize(stdscr)
    _test_app_debug_view(stdscr)


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
    print('Test models.test_view_model()')
    test_models.test_view_model()
    print('Test models.test_view_config()')
    test_models.test_view_config()
    print('Test keys.test_processor()')
    test_keys.test_process()
    print('Test keys.test_process()')
    test_keys.test_processor()
    print('Test storage.test_strore()')
    test_storage.test_store()


def _test_app_main():
    print('Test app.main()')

    # We use a context manager that replaces app.init_env and
    # keys.Processor in order to be able to load app.main as if it was
    # invoked by end-user

    def _init_env():
        parser = argparse.ArgumentParser(description='Dummy parser')
        parser.add_argument('-file', default=TEST_FILE)
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
    def _app_modifier():
        keys_processor = keys.Processor
        init_env = app.init_env
        keys.Processor = _KeysProcessor
        app.init_env = _init_env
        try:
            yield
        finally:
            keys.Processor = keys_processor
            app.init_env = init_env

    with _app_modifier():
        app.main()


def main():
    '''Test entry point'''
    print('== Tests started ==')
    _run_unit_tests()
    utils.wrapper(True, curses.wrapper, _run_app_tests)
    _test_app_main()
    print('== Tests passed ==')


if __name__ == '__main__':
    main()
