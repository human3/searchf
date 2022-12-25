'''https://github.com/human3/searchf'''

import os
import argparse
import curses

from . import __version__
from . import app
from . import colors
from . import keys
from . import storage
from . import utils


def _load_help_lines():
    lines = [f'  ~ Searchf {__version__} Help ~', '']
    help_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'help.txt')
    with open(help_file, encoding='utf-8') as f:
        lines += f.readlines()
    return lines


HELP_LINES = _load_help_lines()

APP = app.App(HELP_LINES)


class StatusView:
    '''View class for a single status line at the bottom of the screen.'''
    def __init__(self, scr):
        self.pos = (0, 0)
        self._scr = scr
        self._max_x = 0

    def layout(self) -> None:
        '''Layout the view.'''
        max_y, max_x = app.get_max_yx(self._scr)
        y = max_y - 1
        x = max(0, min(10, max_x - 50))  # allow for 50 char of status
        self.pos = (y, x)
        self._max_x = max_x

    def draw(self, status) -> None:
        '''Draw the status.'''
        pos = self.pos
        self._scr.addstr(pos[0], pos[1], status[:self._max_x-1])
        self._scr.refresh()


def main_loop(scr, path: str, keys_processor: keys.Processor) -> None:
    '''Main loop consuming keys and events.'''
    colors.init()
    scr.refresh()  # Must be call once on empty screen?
    store = storage.Store('.searchf')
    APP.create(store, scr, path)
    v = StatusView(scr)
    v.layout()

    scr.timeout(1000)
    status = ''
    while True:
        scr.move(v.pos[0], 0)
        try:
            key = keys_processor.get()
        except KeyboardInterrupt:
            break
        handled, new_status = APP.handle_key(key)
        if not handled and key in (ord('q'), ord('Q')):
            break
        if new_status == app.STATUS_UNCHANGED:
            continue
        if key == curses.KEY_RESIZE:
            v.layout()
        app.clear(scr, v.pos[0], v.pos[1], len(status))
        status = new_status
        v.draw(status)


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
