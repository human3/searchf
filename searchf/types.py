'''Module exporting basic types'''

from dataclasses import dataclass
from typing import Tuple
from typing import NamedTuple


@dataclass
class Margins():
    '''Defining margins for window.'''
    top: int
    bottom: int
    left: int
    right: int

    def __init__(self):
        self.top = 0
        self.bottom = 0
        self.left = 0
        self.right = 0


class Position(NamedTuple):
    '''Defining text cursor position'''
    x: int
    y: int


Size = Tuple[int, int]
Status = str
PaletteId = int
