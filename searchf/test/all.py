'''Application end-to-end tests.
'''
import curses
import os
import sys
import time

import searchf
import searchf.app
import searchf.test.test_segments

TEST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample.txt')
if len(sys.argv) > 1:
    TEST_FILE = sys.argv[1]

INPUTS = []
INPUT_IDX = 0

def reset_inputs(inputs):
    global INPUTS, INPUT_IDX
    INPUTS = inputs
    INPUT_IDX = 0

def my_get_text(_1, _2, _3, _4, _5):
    global INPUTS, INPUT_IDX
    assert INPUT_IDX < len(INPUTS), f'{INPUT_IDX} {INPUTS}'
    text = INPUTS[INPUT_IDX]
    INPUT_IDX += 1
    return text

def run_test(stdscr, description, keys, inputs):
    print(description)
    stdscr.clear()
    reset_inputs(inputs)
    searchf.app.init_colors()
    searchf.app.views.create(stdscr, TEST_FILE)
    original_get_text = searchf.app._get_text
    searchf.app._get_text = my_get_text
    for key in keys:
        stdscr.refresh()
        # Add sleep just to see something, test can run without it
        time.sleep(0.1)
        handled = searchf.app.views.handle_key(ord(key))
        assert handled or key == 'q'
    searchf.app._get_text = original_get_text

KEYS = [' ', '>', '<']
KEY_IDX = 0

def my_get_ch(_):
    global KEYS, KEY_IDX
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
def run_app_tests(stdscr):

    # Log param, that might be useful to repro any issue
    print(f'TEST_FILE = {TEST_FILE}')
    print(f'stdscr.getmaxyx() = {stdscr.getmaxyx()}')
    print()

    run_test(stdscr, 'Test keywords that are invalid regex',
             ['f', 'q'], ['?'])
    run_test(stdscr, 'Test that help can get displayed',
             ['?', 'd', 'a', 's', 'w', 'q'], [])
    run_test(stdscr, 'Test view switching',
             ['r', 't', '1', '2', '3'], [])
    run_test(stdscr, 'Test scrolling around',
             ['>', '<', 'd', 'a', 's', 'w', 'D', 'A', ' ', 'b', 'q'], [])
    run_test(stdscr, 'Test goto lines',
             ['\t', '\t', '\t', '\t'], ['5', '99999', 'bad', '0'])
    run_test(stdscr, 'Test various display modes',
             ['l', 'l', 'k', 'k', '.', '.', '*', '*', 'q'], [])
    run_test(stdscr, 'Test entering keywords',
             ['+', '+', 'f', 'f', 'm', 'h', 'h', 'm', 'c', 'c', 'F', '-', '-', '-', '+'],
             ['filter', 'keyword', 'for', 'python', ''])
    run_test(stdscr, 'Test entering empty keywords, poping non existent keywords',
             ['+', 'f', '-', 'F'],
             ['', ''])
    run_test(stdscr, 'Test keyword search',
             ['/', 'n', 'n', 'n', 'p', 'p', 'p', 'p'],
             ['filter'])
    run_test(stdscr, 'Test case sensitive search',
             ['i', '/', 'i', 'i'],
             ['Show'])

    searchf.app.USE_DEBUG = True
    run_test(stdscr, 'Test special debug mode',
             ['/', 'n', 'n', 'n', 'p', 'p'], ['filter'])
    searchf.app.USE_DEBUG = False

    def get_max_yx(_):
        return 20, 20

    original_get_max_yx = searchf.app.get_max_yx
    searchf.app.get_max_yx = get_max_yx
    run_test(stdscr, 'Test with specific layout (scenario #1)',
             ['?', ' ', 'b', 's', 'w'], [])
    run_test(stdscr, 'Test with specific layout (scenario #2)',
             ['>', '<', 'd', 'a', 's', 'w', 'D', 'A', ' ', 'b', 'q'], [])
    searchf.app.get_max_yx = original_get_max_yx

    print('Test searchf.app.get_text()')
    def my_handler(_):
        pass
    reset_inputs(['dummy'])
    searchf.app._get_text(stdscr, 0, 0, "Testing prompt", my_handler)

    print('Test searchf.app._box_edit()')
    class MyBox:
        def edit(self, validate):
            assert validate('a') == 'a'
            assert curses.KEY_BACKSPACE == validate(curses.ascii.DEL)
            validate(curses.ascii.ESC)
    searchf.app._box_edit(MyBox())

    print('Test searchf.app.main_loop()')
    searchf.app.get_ch = my_get_ch
    searchf.app.main_loop(stdscr, TEST_FILE)
    searchf.app.get_ch = stdscr.getch

    print('Test searchf.app.init_env()')
    parser = searchf.app.init_env()
    assert parser

def run_unit_tests():
    print('Test segments')
    searchf.test.test_segments.test_iter_segments()
    searchf.test.test_segments.test_sort_and_merge_segments()

class StdoutWrapper:
    '''Helper class to store stdout while curses is running and testing the app'''
    def __init__(self):
        self._lines = []

    def write(self, line):
        self._lines.append(line)

    def get(self):
        return ''.join(self._lines)

def main():
    '''Test entry point'''

    print('== test starting ==')

    test_stdout = StdoutWrapper()
    sys.stdout = test_stdout
    sys.stderr = test_stdout

    error = None
    try:
        curses.wrapper(run_app_tests)
    except Exception as ex:
        error = ex

    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    print(test_stdout.get())

    if error:
        print('== test failed ==')
        raise error

    run_unit_tests()
    print('== test passed ==')

if __name__ == '__main__':
    main()
