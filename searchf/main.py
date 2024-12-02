'''https://github.com/human3/searchf'''

import os
import argparse
import curses

from . import __version__
from . import __url__
from . import app
from . import colors
from . import enums
from . import keys
from . import storage
from . import types
from . import utils


def _load_help_lines():
    lines = [f'  ~ Searchf {__version__} Help ~', '']
    help_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'help.txt')
    lines += app.load_lines(help_file)
    lines += ['More info']
    lines += [f'  {__url__}']
    lines += [f'  {__url__}/releases/tag/{__version__}']
    return lines


HELP_LINES = _load_help_lines()

APP = app.App(HELP_LINES)


class StatusView:
    '''View class for a single status line at the bottom of the screen.'''
    def __init__(self, scr):
        self.pos = (0, 0)
        self._scr = scr
        self._width = 0

    def layout(self) -> None:
        '''Layout the view.'''
        max_y, max_x = app.get_max_yx(self._scr)
        # We use padding to workaround addstr() throwing exception
        # when printing outside of the screen boundaries with
        # some utf-8 encoded char
        padding = 5
        self._width = max(0, max_x - 1 - 2 * padding)
        y = max_y - 1
        x = min(padding, max_x - 1)
        self.pos = (y, x)

    def draw(self, status) -> None:
        '''Draw the status.'''
        pos = self.pos
        self._scr.addstr(pos[0], pos[1], f'{status:^{self._width}}')
        self._scr.refresh()


def main_loop(scr,
              path: str,
              use_debug: bool,
              show_events: bool,
              keys_processor: keys.Processor
              ) -> None:
    '''Main loop consuming keys and events.'''
    app.USE_DEBUG = use_debug
    colors.init()
    scr.refresh()  # Must be call once on empty screen?
    curses.mousemask(-1)
    store = storage.Store('.searchf')
    margins = types.Margins()
    margins.bottom += 1
    APP.create(store=store, scr=scr, margins=margins,
               show_events=show_events, path=path)
    v = StatusView(scr)
    v.layout()

    scr.timeout(200)
    status = ''
    while True:
        scr.move(v.pos[0], 0)
        try:
            ev = keys_processor.get()
        except KeyboardInterrupt:
            break
        handled, new_status = APP.handle_event(ev)
        if not handled and ev.cmd == enums.Command.QUIT:
            break
        if new_status == app.STATUS_UNCHANGED:
            continue
        if ev.cmd == enums.Command.RESIZE:
            v.layout()
        app.clear(scr, v.pos[0], v.pos[1], len(status))
        status = new_status
        v.draw(status)


def main_curses(scr, args) -> None:
    '''Main entry point requiring curse environment.'''
    main_loop(scr,
              args.file,
              args.debug,
              args.show_events,
              keys.Processor(scr, curses))


def init_env() -> argparse.ArgumentParser:
    '''Initialize environment and return argument parser.'''
    # https://stackoverflow.com/questions/27372068/why-does-the-escape-key-have-a-delay-in-python-curses
    os.environ.setdefault('ESCDELAY', '25')
    os.environ['TERM'] = 'screen-256color'
    parser = argparse.ArgumentParser(
        description='Console application to search into text files and \
highlight keywords.',
        epilog='Press ? in the application for more information, or go to \
https://github.com/human3/searchf')
    parser.add_argument('file')
    parser.add_argument('--debug',
                        help='Use debug layout',
                        action='store_true')
    parser.add_argument('--show-events',
                        help='Show events like key presses',
                        action='store_true')
    return parser


def main() -> None:
    '''Application entry point.'''
    parser = init_env()
    args = parser.parse_args()
    utils.wrapper(False, curses.wrapper, main_curses, args)


if __name__ == '__main__':  # pragma: no cover
    main()
