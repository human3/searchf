'''https://github.com/human3/searchf'''

import os
import argparse
import curses

from . import colors
from . import keys
from . import storage
from . import utils
from . import views

VIEWS = views.Views()


def main_loop(scr, path: str, keys_processor: keys.Processor) -> None:
    '''Main loop consuming keys and events.'''
    colors.init()
    scr.refresh()  # Must be call once on empty screen?
    store = storage.Store('.searchf')
    VIEWS.create(store, scr, path)

    max_y, max_x = views.get_max_yx(scr)

    status = ''
    status_x = max(0, min(10, max_x - 50))  # allow for 50 char of status
    status_y = max_y - 1

    scr.timeout(1000)
    while True:
        try:
            key = keys_processor.get()
        except KeyboardInterrupt:
            break
        if key == curses.KEY_RESIZE:
            raise views.ResizeException('Sorry, resizing is not supported')
        handled, new_status = VIEWS.handle_key(key)
        if not handled and key in (ord('q'), ord('Q')):
            break
        if new_status == views.STATUS_UNCHANGED:
            continue
        views.clear(scr, status_y, status_x, len(status))
        status = new_status
        scr.addstr(status_y, status_x, status[:max_x-1])
        scr.refresh()
        scr.move(status_y, 0)


def main_curses(scr, path: str) -> None:
    '''Main entry point requiring curse environment.'''
    main_loop(scr, path, keys.Processor(scr))


def init_env() -> argparse.ArgumentParser:
    '''Initialize environment and return argument parser'''
    # https://stackoverflow.com/questions/27372068/why-does-the-escape-key-have-a-delay-in-python-curses
    os.environ.setdefault('ESCDELAY', '25')
    os.environ['TERM'] = 'screen-256color'
    parser = argparse.ArgumentParser(
        description='Console application to search into text files and \
highlight keywords.',
        epilog='Press ? in the application for more information, or go to \
https://github.com/human3/searchf')
    parser.add_argument('file')
    return parser


def main() -> None:
    '''Application entry point'''
    parser = init_env()
    args = parser.parse_args()
    utils.wrapper(False, curses.wrapper, main_curses, args.file)


if __name__ == '__main__':  # pragma: no cover
    main()
