'''Provides model classes for searchf application.'''

# pylint: disable=invalid-name

import math
from searchf import segments

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
        self.keywords.popitem()

def _digits_count(max_number):
    return math.floor(math.log10(max(1, max_number))+1)

class Model:
    '''Holds data associated with a file.'''
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

    def sync(self, filters, only_matching):
        '''Recomputes the data model by applying the given filters to the
        current file content. Each line is associated with:
        - the index of the line in the original content (required
          because we don't always show all lines of the original file)
        - the index of the matching filter if any, or -1 otherwise
        - the text of the line
        - the segments matching keywords in the filter that will be
          highlighted/colorized
        '''

        show_all_lines = not only_matching or len(filters) <= 0
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
                    data.append([i, fidx, line, matching_segments])
                    break
            if not matching and show_all_lines:
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
