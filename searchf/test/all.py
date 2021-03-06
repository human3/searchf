'''Application end-to-end tests.
'''

# pylint: disable=global-statement
# pylint: disable=protected-access
# pylint: disable=invalid-name

import curses
import os
import sys
import time

from .. import app
from .. import colors
from .. import utils
from . import test_segments
from . import test_models

TEST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample.txt')
if len(sys.argv) > 1:
    TEST_FILE = sys.argv[1]

INPUTS = []
INPUT_IDX = 0


def _reset_inputs(inputs):
    global INPUTS, INPUT_IDX
    INPUTS = inputs
    INPUT_IDX = 0


def _my_get_text(_1, _2, _3, _4, _5, _6):
    global INPUT_IDX
    assert INPUT_IDX < len(INPUTS), f'{INPUT_IDX} {INPUTS}'
    text = INPUTS[INPUT_IDX]
    INPUT_IDX += 1
    return text


def _run_test(stdscr, description, keys, inputs):
    print(description)
    stdscr.clear()
    _reset_inputs(inputs)
    colors.init()
    app.views.create(stdscr, TEST_FILE)
    original_get_text = app._get_text
    app._get_text = _my_get_text
    for key in keys:
        stdscr.refresh()
        # Add sleep just to see something, test can run without it
        time.sleep(0.01)
        handled = app.views.handle_key(ord(key))
        assert handled or key == 'q'
    app._get_text = original_get_text


KEYS = [' ', '>', '<']
KEY_IDX = 0


def _my_get_ch(_):
    global KEY_IDX
    if KEY_IDX >= len(KEYS):
        return ord('q')
    key = ord(KEYS[KEY_IDX])
    KEY_IDX += 1
    return key


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

    _run_test(stdscr, 'Test keywords that are invalid regex',
              ['f', 'q'], ['?'])
    _run_test(stdscr, 'Test that help can get displayed',
              ['?', 'd', 'a', 'a', 's', 'w', 'q'], [])
    _run_test(stdscr, 'Test view switching',
              ['r', 't', '1', '2', '3', '!', '@', '#'], [])
    _run_test(stdscr, 'Test scrolling around',
              ['>', '<', 'd', 'a', 's', 'w', 'D', 'A', ' ', 'b', 'q'], [])
    _run_test(stdscr, 'Test goto lines',
              ['\t', '\t', '\t', '\t'], ['5', '99999', 'bad', '0'])
    _run_test(stdscr, 'Test various display modes',
              ['l', 'k', 'k', '.', '.', '*', '*', 'm', 'M', 'm', 'q'], [])
    _run_test(stdscr, 'Test entering one letter keywords',
              ['+', '+', 'f', 'f', 'v', 'h', 'h', 'v', 'v', 'V', 'c', 'c', 'F', '-', '-', '-', '+'],
              ['a', 'b', 'c', 'd', ''])
    _run_test(stdscr, 'Test entering keywords',
              ['+', '+', 'f', 'f', 'm', 'h', 'h', 'H', 'm', 'c', 'C', 'F', '-', '-', '-', '+'],
              ['filter', 'keyword', 'for', 'python', ''])
    _run_test(stdscr, 'Test entering empty keywords, poping non existent keywords',
              ['+', 'f', '-', 'F'],
              ['', ''])
    _run_test(stdscr, 'Test editing keywords',
              ['e', '+', 'e', 'e'],
              ['something', 'good', ''])
    _run_test(stdscr, 'Test keyword search',
              ['/', 'n', 'n', 'n', 'p', 'p', 'p', 'p'],
              ['filter'])
    _run_test(stdscr, 'Test case sensitive search',
              ['i', '/', 'i', 'i'],
              ['Show'])

    # Test debug mode in a very hacky way by hijacking handle_key function
    # and spitting out a few dummy debug lines per key press
    app.USE_DEBUG = True
    original_handle_key = app.views.handle_key

    def my_handle_key(key):
        for i in range(20):
            app.debug(f'Test {i} dbg {key}')
        return original_handle_key(key)

    app.views.handle_key = my_handle_key
    _run_test(stdscr, 'Test special debug mode',
              ['/', 'n', 'n', 'n', 'p', 'p'], ['filter'])
    app.views.handle_key = original_handle_key
    app.USE_DEBUG = False

    def get_max_yx(_):
        return 20, 20

    original_get_max_yx = app.get_max_yx
    app.get_max_yx = get_max_yx
    _run_test(stdscr, 'Test with specific layout (scenario #1)',
              ['?', ' ', 'b', 's', 'w'], [])
    _run_test(stdscr, 'Test with specific layout (scenario #2)',
              ['>', '<', 'd', 'a', 's', 'w', 'D', 'A', ' ', 'b', 'q'], [])
    app.get_max_yx = original_get_max_yx

    print('Test app.get_text()')

    def my_handler(_):
        pass

    _reset_inputs(['dummy'])
    app._get_text(stdscr, 0, 0, "Testing prompt", my_handler, '')

    def my_handler_throwing(_):
        raise app.EscapeException

    app._get_text(stdscr, 0, 0, "Testing prompt", my_handler_throwing, '')

    print('Test app._validate()')
    assert app._validate('a') == 'a'
    assert app._validate(curses.ascii.DEL) == curses.KEY_BACKSPACE
    actual = None
    try:
        app._validate(curses.ascii.ESC)
    except app.EscapeException as e:
        actual = e
    assert actual

    print('Test app.main_loop()')
    app.get_ch = _my_get_ch
    app.main_loop(stdscr, TEST_FILE)
    app.get_ch = stdscr.getch

    print('Test app.init_env()')
    parser = app.init_env()
    assert parser


def _run_unit_tests():
    print('Test segments.iterate()')
    test_segments.test_iterate()
    print('Test segments._sort_and_merge()')
    test_segments.test_sort_and_merge()
    print('Test segments.find_matching()')
    test_segments.test_find_matching()
    print('Test models.test_visibility_mode()')
    test_models.test_visibility_mode()
    print('Test models.test_filter()')
    test_models.test_filter()
    print('Test models.test_digit_count()')
    test_models.test_digit_count()
    print('Test models.test_model()')
    test_models.test_model()
    print('Test models.test_view_model()')
    test_models.test_view_model()


def main():
    '''Test entry point'''
    print('== Tests started ==')
    utils.wrapper(True, curses.wrapper, _run_app_tests)
    _run_unit_tests()
    print('== Tests passed ==')


if __name__ == '__main__':
    main()
