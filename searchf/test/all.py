import os, sys
import searchf
import searchf.app
import curses
import time

INPUTS = []
INPUT_IDX = 0

def reset_inputs(inputs):
    global INPUTS, INPUT_IDX
    INPUTS = inputs
    INPUT_IDX = 0

def my_get_text(self):
    global INPUTS, INPUT_IDX
    assert INPUT_IDX < len(INPUTS)
    input = INPUTS[INPUT_IDX]
    INPUT_IDX += 1
    return input

def run_test(stdscr, path, keys, inputs):
    stdscr.clear()
    reset_inputs(inputs)
    searchf.app.init_colors()
    searchf.app.views.create(stdscr, path)
    searchf.app.views.get_text = my_get_text
    for key in keys:
        stdscr.refresh()
        # Add sleep just to see something, test can run without it
        time.sleep(0.1)
        handled = searchf.app.views.handle_key(ord(key))
        assert handled or key == 'q'

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
def run_all(stdscr):

    dummy_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sample.txt')

    # Test keywords that are invalid regex
    run_test(stdscr, dummy_file,
             ['f', 'q'], ['?'])

    # Test help can get displayed
    run_test(stdscr, dummy_file,
             ['?', 'd', 'a', 's', 'w', 'q'], [])
    # View testsing
    run_test(stdscr, dummy_file,
             ['r', 't', '1', '2', '3'], [])
    # Scrolling around
    run_test(stdscr, dummy_file,
             ['>', '<', 'd', 'a', 's', 'w', 'D', 'A', ' ', 'b', 'q'], [])
    # Goto lines
    run_test(stdscr, dummy_file, ['\t', '\t', '\t', '\t'], ['5', '99999', 'bad', '0'])
    # Testing display modes
    run_test(stdscr, dummy_file,
             ['l', 'l', 'k', 'k', '.', '.', '*', '*', 'q'], [])
    # Entering keywords
    run_test(stdscr, dummy_file,
             ['+', '+', 'f', 'f', 'm', 'h', 'h', 'm', 'c', 'c', 'F', '-', '-', '-', '+'],
             ['filter', 'keyword', 'for', 'python', ''])
    # Entering empty keywords, poping non existent keywords
    run_test(stdscr, dummy_file,
             ['+', 'f', '-', 'F'],
             ['', ''])
    # Search keywords
    run_test(stdscr, dummy_file,
             ['/', 'n', 'n', 'n', 'p', 'p'],
             ['filter'])
    # Case sensitive search
    run_test(stdscr, dummy_file,
             ['i', '/', 'i', 'i'],
             ['Show'])

    # Testing special modes
    searchf.USE_DEBUG = True
    run_test(stdscr, dummy_file, ['/', 'n', 'n', 'n', 'p', 'p'], ['filter'])
    searchf.USE_DEBUG = False

    def get_max_yx(stdscr):
        return 20, 20

    original_get_max_yx = searchf.app.get_max_yx
    searchf.app.get_max_yx = get_max_yx
    run_test(stdscr, dummy_file, ['?', ' ', 'b', 's', 'w'], [])
    run_test(stdscr, dummy_file, ['>', '<', 'd', 'a', 's', 'w', 'D', 'A', ' ', 'b', 'q'], [])
    searchf.app.get_max_yx = original_get_max_yx

    # Testing searchf.app.get_text
    def my_handler(box):
        pass

    searchf.app._get_text(stdscr, 0, 0, "Testing prompt", my_handler)

    class MyBox:
        def edit(self, validate):
            assert 'a' == validate('a')
            assert curses.KEY_BACKSPACE == validate(curses.ascii.DEL)
            validate(curses.ascii.ESC)

    searchf.app._box_edit(MyBox())

    # Testing searchf.main wrapper
    searchf.app.get_ch = my_get_ch
    searchf.app.main_loop(stdscr, dummy_file)
    searchf.app.get_ch = stdscr.getch

def main():
    curses.wrapper(run_all)
    
if __name__ == '__main__':
    print('Running unit tests')
    # test_unit.test_iter_segments()
    # test_unit.test_sort_and_merge_segments()

    main()

    print('To generate coverage data:')
    print('  coverage run all.py')
    print('  coverage html')
