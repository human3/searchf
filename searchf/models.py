'''Provides model classes for application.'''

# pylint: disable=invalid-name

import math
from enum import Enum
from . import segments

class Filter:
    '''Represents a list of keywords ANDed together and matching properties'''
    ignore_case: bool = False

    def __init__(self):
        self.keywords = {}

    def add(self, keyword):
        '''Adds given keyword to this filter'''
        self.keywords[keyword] = None

    def pop(self):
        '''Removes most recently added keyword from this filter'''
        return self.keywords.popitem()

    def get_last(self):
        '''Returns last entered keyword'''
        keyword, _ = self.pop()
        self.add(keyword)
        return keyword

def _digits_count(max_number):
    return math.floor(math.log10(max(1, max_number))+1)

class AutoEnum(Enum):
    '''Base class for auto enum that can get iterated over.'''
    def __new__(cls, description):
        value = len(cls.__members__)
        obj = object.__new__(cls)
        obj._value_ = value
        obj._description = description
        return obj

    def __str__(self):
        return f'{self._description}'

    @classmethod
    def _from_int(cls, i):
        for e in cls:
            if e.value == i:
                return e
        raise ValueError('Unsupported enum value')

    @classmethod
    def get(cls, i):
        '''Returns enumeration matching given int value'''
        i = (i ) % len(cls.__members__)
        return cls._from_int(i)

    def get_next(self):
        '''Returns the next enumeration.'''
        return self.__class__.get(self.value + 1)

    def get_prev(self):
        '''Returns the previous enumeraion.'''
        return self.__class__.get(self.value - 1)

class MatchingMode(AutoEnum):
    '''Matching modes.'''
    ALL_LINES = ('all lines')
    ONLY_MATCHING_LINES = ('only matching lines')
    ONLY_NOT_MATCHING = ('only not matching lines')

class Model:
    '''Holds data associated with the content of a file. and all the
    segments that matches filters.
    '''
    def __init__(self):
        self._lines = []
        self.data = []
        self.hits = []

    def line_count(self):
        '''Gets the number of lines in the original file'''
        return len(self._lines)

    def line_number_length(self):
        '''Number of digit required to display bigest line number'''
        return _digits_count(len(self._lines))

    def set_lines(self, lines):
        '''Sets and stores the file content lines into the data model'''
        self._lines = lines
        self.data = []
        self.hits = []

    def hits_count(self):
        '''Gets the current hits count'''
        return sum(self.hits)

    def sync(self, filters, mode):
        '''Recomputes the data model by applying the given filters to the
        current file content. Each line is associated with:
        - the index of the line in the original content (required
          because we don't always show all lines of the original file)
        - the index of the matching filter if any, or -1 otherwise
        - the text of the line
        - the segments matching keywords in the filter that will be
          highlighted/colorized
        '''

        show_matching = mode in (
            MatchingMode.ALL_LINES,
            MatchingMode.ONLY_MATCHING_LINES)
        show_not_matching = len(filters) <= 0 or mode in (
            MatchingMode.ALL_LINES,
            MatchingMode.ONLY_NOT_MATCHING)

        data = []
        hits = [0 for f in filters]

        for i, line in enumerate(self._lines):
            # Replace tabs with 4 spaces (not clean!!!)
            line = line.replace('\t', '    ')
            matching = False
            for fidx, f in enumerate(filters):
                matching, matching_segments = \
                    segments.find_matching(line, f.keywords, f.ignore_case)
                if matching:
                    hits[fidx] += 1
                    if show_matching:
                        data.append([i, fidx, line, matching_segments])
                    break
            if not matching and show_not_matching:
                data.append([i, -1, line, set()])

        self.data = data
        self.hits = hits

class ViewModel:
    '''ViewModel data.'''
    def __init__(self):
        self.hoffset = 0 # horizontal offset in content: index of first visible column
        self.voffset = 0 # vertical offset in content: index of first visible line in data
        self.voffset_desc = ''
        self.firstdlines = [] # First display line of each model lines
        self.data = [] # Display line data (index in model and horizontal offset)
        self.size = (0, 0) # Number of lines and columns available to display file content

    def reset_offsets(self):
        '''Reset all the content offsets.'''
        self.hoffset = 0
        self.voffset = 0
        self.voffset_desc = ''

    def lines_count(self):
        '''Gets the number of lines required to display the whole content
without clipping any of it.'''
        return len(self.data)

    def set_h_offset(self, offset):
        '''Sets the horizontal offset. Returns True if changed, False otherwise.'''
        offset = max(offset, 0)
        if self.hoffset == offset:
            return False
        self.hoffset = offset
        return True

    def set_v_offset(self, offset):
        '''Sets the vertical offfset. Returns True if changed, False otherwise.'''
        assert self.size[0] >= 0
        ymax = max(0, self.lines_count() - self.size[0])
        if offset >= ymax:
            offset = ymax
            desc = 'BOT'
        elif offset <= 0:
            offset = 0
            desc = 'TOP'
        else:
            percent = int(offset * 100 / ymax)
            desc = f'{percent}%'
        if self.voffset == offset:
            return False
        self.voffset = offset
        self.voffset_desc = desc
        return True

    def layout(self, height, width, model_data, wrapping):
        '''Computes the view model data, breaking the lines from the
        data model into displayable lines taking into account the
        available space on the screen.'''

        assert height > 0
        assert width > 0

        self.size = (height, width)

        data = []
        firstdlines = []
        if not wrapping:
            for idata, mdata in enumerate(model_data):
                firstdlines.append(len(data))
                data.append([idata, 0])
        else:
            for idata, mdata in enumerate(model_data):
                firstdlines.append(len(data))
                _, _, text, _ = mdata
                offset = 0
                left = len(text)
                while left >= 0:
                    data.append([idata, offset])
                    offset += width
                    left -= width
        self.data = data
        self.firstdlines = firstdlines
