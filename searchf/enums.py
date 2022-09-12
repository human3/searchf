'''Provides enum helper and enums for application.'''

from enum import auto
from enum import Enum


class AutoEnum(Enum):
    '''Base class for auto enum that can get iterated over with
    wrapping.'''
    def __new__(cls, description):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        obj._description = description
        return obj

    def __str__(self):
        return f'{self._description}' # f'{self._value_} {self._description}'

    @classmethod
    def from_int(cls, i):
        '''Returns the enum member associated with the given integer.'''
        for member in cls:
            if member.value == i:
                return member
        raise ValueError('Unsupported enum value')

    @classmethod
    def get(cls, i):
        '''Returns enumeration matching given int value'''
        i = i % len(cls.__members__)
        return cls.from_int(i)

    def get_next(self):
        '''Returns the next enumeration.'''
        return self.__class__.get(self.value + 1)

    def get_prev(self):
        '''Returns the previous enumeraion.'''
        return self.__class__.get(self.value - 1)


class LineVisibility(AutoEnum):
    '''Line visibility modes.'''
    ONLY_MATCHING = ('Showing only matching lines')
    CONTEXT_1 = ('Reveal 1 line above/below matching')
    CONTEXT_2 = ('Reveal 2 lines above/below matching')
    CONTEXT_5 = ('Reveal 5 lines above/below matching')
    ALL = ('Showing all lines')


class ColorizeMode(AutoEnum):
    '''Keyword colorize modes.'''
    KEYWORD_HIGHLIGHT = ('Keyword highlight')
    KEYWORD = ('Keyword')
    LINE = ('Line')


class TextViewCommand(Enum):
    '''Simple commands accepted by TextView class, that do not take any argument.'''
    GO_UP = auto()
    GO_DOWN = auto()
    GO_LEFT = auto()
    GO_RIGHT = auto()
    GO_HOME = auto()
    GO_END = auto()
    GO_NPAGE = auto()
    GO_PPAGE = auto()
    GO_SLEFT = auto()
    GO_SRIGHT = auto()
    POP_FILTER = auto()
    POP_KEYWORD = auto()
    VSCROLL_TO_NEXT_MATCH = auto()
    VSCROLL_TO_PREV_MATCH = auto()
    TOGGLE_LINE_NUMBERS = auto()
    TOGGLE_WRAP = auto()
    TOGGLE_BULLETS = auto()
    TOGGLE_SHOW_SPACES = auto()
    NEXT_COLORIZE_MODE = auto()
    PREV_COLORIZE_MODE = auto()
    NEXT_LINE_VISIBILITY = auto()
    PREV_LINE_VISIBILITY = auto()
    TOGGLE_IGNORE_CASE = auto()
    TOGGLE_HIDING = auto()
    NEXT_PALETTE = auto()
    PREV_PALETTE = auto()
    SWAP_FILTERS = auto()
