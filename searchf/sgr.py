'''Provides processor for Select Graphic Rendition (SGR)

https://en.wikipedia.org/wiki/ANSI_escape_code#SGR
'''
import curses
import re

from typing import Callable
from typing import Dict
from typing import List
from typing import Tuple

from . import colors
from . import enums
from . import segments


SGR_COLOR_TO_COLOR_ID: Dict[int, colors.ColorId] = {
    30: 0,
    31: 1,
    32: 2,
    33: 3,
    34: 4,
    35: 5,
    36: 6,
    37: 7,
    39: 0,
    90: 8,
    91: 9,
    92: 10,
    93: 11,
    94: 12,
    95: 13,
    96: 14,
    97: 15,
    40: 16,
    41: 17,
    42: 18,
    43: 19,
    44: 20,
    45: 21,
    46: 22,
    47: 23,
    100: 24,
    101: 25,
    102: 26,
    103: 27,
    104: 28,
    105: 29,
    106: 30,
    107: 31,
}

SGR_BG_COLOR_TO_COLOR_ID: Dict[int, colors.ColorId] = {
    40: 0,
    41: 1,
    42: 2,
    43: 3,
    44: 4,
    45: 5,
    46: 6,
    47: 7,
    100: 8,
    101: 9,
    102: 10,
    103: 11,
    104: 12,
    105: 13,
    106: 14,
    107: 15,
}

FG_BG_TO_COLOR_PAIR_FUNC: \
    Callable[[colors.ColorId, colors.ColorId], colors.Pair] = \
    colors.get_fg_bg_color_pair


class Processor:
    '''Holds original file coloring, built by parsing CSI.'''
    # https://en.wikipedia.org/wiki/ANSI_escape_code#CSI_(Control_Sequence_Introducer)_sequences
    # https://en.wikipedia.org/wiki/ANSI_escape_code#SGR_(Select_Graphic_Rendition)_parameters

    def __init__(self) -> None:
        self._a: int = 0
        self._s: int = -1
        self._fg: int = -1
        self._bg: int = -1

    def filter(self,
               line,
               mode: enums.SgrMode,
               ) -> Tuple[List[segments.Segment], str]:
        '''Process the SGR from the given line and returns the resulting raw
        string and the segments to render the requested attributes.

        '''
        background: List[segments.Segment] = []
        if mode == enums.SgrMode.NONE:
            return background, line
        new_line = re.sub(r'\x1b\[[0-?]*[!-/]*[@-~]', '', line)
        if mode == enums.SgrMode.REMOVE:
            return background, new_line

        assert mode == enums.SgrMode.PROCESS
        eaten = 0

        def seg_end(end):
            start, attr = self._s, self._a
            if 0 <= start < end:
                assert start < end, f'{start} {end}'
                assert attr != 0
                background.append(segments.Segment(start, end, attr))
            self._s = -1

        def set_attr(a):
            if not a:
                return
            a = int(a)
            if a == 0:
                self._a = 0
                self._fg = -1
                self._bg = -1
            elif a == 1:
                self._a = self._a | curses.A_BOLD
            elif a == 2:
                self._a = self._a | curses.A_DIM
            elif a == 4:
                self._a = self._a | curses.A_UNDERLINE
            elif a in SGR_COLOR_TO_COLOR_ID:
                if a in SGR_BG_COLOR_TO_COLOR_ID:
                    self._bg = SGR_BG_COLOR_TO_COLOR_ID[a]
                else:
                    self._fg = SGR_COLOR_TO_COLOR_ID[a]
                pair = FG_BG_TO_COLOR_PAIR_FUNC(self._fg, self._bg)
                self._a = (~curses.A_COLOR & self._a) | pair

        # If we have attribute from previous line, start a pending segment
        if self._a:
            self._s = 0

        for match in re.finditer(r'\x1b\[([0-9]+)(;([0-9]+))?m', line):
            s, e = match.start(), match.end()
            assert s < e
            a_1, a_2 = match.group(1), match.group(3)
            start = s - eaten
            eaten += e - s
            # Finish any pending segment
            seg_end(start)
            # Mark start a new pending
            set_attr(a_1)
            set_attr(a_2)
            if self._a:
                self._s = start

        # Finish any pending segment
        seg_end(len(new_line))
        return background, new_line
