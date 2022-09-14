'''Provides model classes for application.'''

# pylint: disable=invalid-name

import math
from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple
from . import segments
from . import enums


class Filter:
    '''Filters are used to select lines and highlight keywords in these
    matching lines. In practice, each filter holds properties defining
    how matching is done and a list of keywords. Keywords can be added
    or removed by end-user.
    '''
    ignore_case: bool = False
    hiding: bool = False

    def __init__(self) -> None:
        # We use a Dict to make sure that keywords are never added
        # twice (ie like a set) and that insertion order is preserved
        # (ie like a stack).
        self.keywords: Dict[str, None] = {}

    def add(self, keyword: str) -> None:
        '''Adds given keyword to this filter'''
        self.keywords[keyword] = None

    def pop(self) -> Tuple[str, None]:
        '''Removes most recently added keyword from this filter'''
        return self.keywords.popitem()

    def get_count_and_last_keyword(self) -> Tuple[int, Optional[str]]:
        '''Returns the number of keywords and the last keyword.'''
        count = len(self.keywords)
        if count <= 0:
            return 0, None
        # No peek API, so we need to pop and add back...
        keyword, _ = self.pop()
        self.add(keyword)
        return count, keyword


def _digits_count(max_number) -> int:
    return math.floor(math.log10(max(1, max_number))+1)

RULER_INDEX = -1

class LineModel(NamedTuple):
    '''Model data associated with each line:
    - the index of the line in the original content (required because
      we don't always show all lines of the original file), or
      -1 if this line does not represent original content (like
      an horizontal ruler).
    - the index of the matching filter if any, or -1 otherwise
    - the text of the line
    - the segments that will be highlighted (and that are matching
      keywords in the filter).
    '''
    line_index: int
    filter_index: int
    text: str
    segments: List[segments.Segment]


class LineModelFilter:
    '''Class use to filter out LineModel according to a given line visibility
    mode. Models are added sequentially, one by one, and are then yielded back
    to caller (or not) so as to reveal the desired amount of non-matching lines
    above and below matching lines.
    '''
    def __init__(self, mode: enums.LineVisibility):
        self._queue: List[LineModel] = []
        if mode == enums.LineVisibility.ONLY_MATCHING:
            self._size = 0
        elif mode == enums.LineVisibility.CONTEXT_1:
            self._size = 1
        elif mode == enums.LineVisibility.CONTEXT_2:
            self._size = 2
        elif mode == enums.LineVisibility.CONTEXT_5:
            self._size = 5
        else:
            assert mode == enums.LineVisibility.ALL, f'BAD enum {mode}'
            self._size = -1
        self._left = 0
        self._last_line_visible = 0

    def _add(self, model: LineModel) -> bool:
        '''Adds model and returns whether or not caller should flush queue.'''
        if self._size == 0:
            return False
        self._queue.append(model)
        if self._size < 0:
            # Infinite capacity, never queueing anything...
            return True
        if self._left > 0:
            # Want caller to call flush
            self._left -= 1
            return True
        # We are now queueing these lines, as we are unsure they will be shown
        if len(self._queue) > self._size:
            self._queue.pop(0)
        return False

    def _flush(self) -> List[LineModel]:
        models = self._queue
        self._queue = []
        return models

    def _updateLastYielded(self, model: LineModel):
        line, _, _, _ = model
        self._last_line_visible = line + 1

    def addMatching(self, model: LineModel) -> List[LineModel]:
        '''Adds a line model that matches a filter. Returns
        the list of line models that are visible, if any.'''

        models = []
        queued = self._flush()
        if len(queued) > 0:
            # Check if we need to add horizontal rule (index -1)
            line, _, _, _ = queued[0]
            if line > self._last_line_visible:
                models.append(LineModel(RULER_INDEX, -1, '', []))
            models = models + queued

        models.append(model)
        self._updateLastYielded(model)

        # Make sure we are going to bufferize the appropriate amount
        # of subsequent non-matching lines, if we encounter any.
        self._left = self._size

        return models

    def addNonMatching(self, model: LineModel) -> List[LineModel]:
        '''Adds a line model that does not match any filter. Returns
        the list of line models that are visible, if any.'''
        if not self._add(model):
            return []
        queued = self._flush()
        assert len(queued) == 1
        self._updateLastYielded(model)
        return queued


class Model:
    '''Holds data associated with the content of a file and all the
    segments that matches filters.
    '''
    def __init__(self) -> None:
        self._lines: List[str] = []
        self.data: List[LineModel] = []
        self.hits: List[int] = []

    def line_count(self) -> int:
        '''Gets the number of lines in the original file'''
        return len(self._lines)

    def line_number_length(self) -> int:
        '''Number of digit required to display bigest line number'''
        return _digits_count(len(self._lines))

    def set_lines(self, lines: List[str]) -> None:
        '''Sets and stores the file content lines into the data model'''
        self._lines = lines
        self.data = []
        self.hits = []

    def hits_count(self) -> int:
        '''Gets the current hits count'''
        return sum(self.hits)

    def sync(self, filters: List[Filter], mode: enums.LineVisibility) -> None:
        '''Recomputes the data model by applying the given filters to the
        current file content.
        '''
        data: List[LineModel] = []
        hits = [0 for f in filters]
        mode = mode if sum(not f.hiding for f in filters) > 0 else enums.LineVisibility.ALL
        q = LineModelFilter(mode)
        for i, line in enumerate(self._lines):
            # Replace tabs with 4 spaces (not clean!!!)
            line = line.replace('\t', '    ')
            assert len(line) <= 0 or ord(line[0]) != 0, f'Line {i} has embedded null character'
            matching = False
            for fidx, f in enumerate(filters):
                matching, matching_segments = \
                    segments.find_matching(line, f.keywords, f.ignore_case)
                if matching:
                    hits[fidx] += 1
                    if not f.hiding:
                        lines = q.addMatching(LineModel(i, fidx, line, matching_segments))
                        data = data + lines
                    break
            if not matching:
                lines = q.addNonMatching(LineModel(i, -1, line, []))
                data = data + lines

        self.data = data
        self.hits = hits

class LineViewModel(NamedTuple):
    '''View model data associated with each line'''
    line_index: int
    offset: int


class ViewModel:
    '''ViewModel data.'''
    def __init__(self) -> None:
        self.hoffset: int = 0  # horizontal offset in content: index of first visible column
        self.voffset: int = 0  # vertical offset in content: index of first visible line in data
        self.voffset_desc: str = ''
        self.firstdlines: List[int] = []  # First display line of each model lines
        self.data: List[LineViewModel] = []  # Display line data
        self.size = (0, 0)  # Number of lines and columns available to display file content

    def lines_count(self) -> int:
        '''Gets the number of lines required to display the whole content
        without clipping any of it.'''
        return len(self.data)

    def set_h_offset(self, offset: int) -> bool:
        '''Sets the horizontal offset. Returns True if changed, False otherwise.'''
        offset = max(offset, 0)
        if self.hoffset == offset:
            return False
        self.hoffset = offset
        return True

    def set_v_offset(self, offset: int) -> bool:
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

    def layout(self,
               height: int,
               width: int,
               model_data: List[LineModel],
               wrapping: bool
               ) -> None:
        '''Computes the view model data, breaking the lines from the
        data model into displayable lines taking into account the
        available space on the screen.'''

        assert height > 0
        assert width > 0

        self.size = (height, width)

        data: List[LineViewModel] = []
        firstdlines: List[int] = []
        if not wrapping:
            for idata, mdata in enumerate(model_data):
                firstdlines.append(len(data))
                data.append(LineViewModel(idata, 0))
        else:
            for idata, mdata in enumerate(model_data):
                firstdlines.append(len(data))
                line_idx, _, text, _ = mdata
                offset = 0
                if line_idx == RULER_INDEX:
                    data.append(LineViewModel(idata, offset))
                    continue
                left = len(text)
                while left >= 0:
                    data.append(LineViewModel(idata, offset))
                    offset += width
                    left -= width
        self.data = data
        self.firstdlines = firstdlines
