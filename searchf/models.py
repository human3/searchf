'''Provides various model classes for searchf application.'''

import math

from typing import Dict
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple

from . import enums
from . import segments
from . import types


class DisplayLine(NamedTuple):
    '''Holds data associated with a single displayable line on the screen. Each
    line in the original file might not entirely fit on screen, and can be
    split into several DisplayLine (when line wrapping is on). In other words,
    several DisplayLine might refer to same selected line and have the same
    line_index.

    Attributes:
        line_index  Index of line in array of SelectedLines
        offset      Offset in the original line of the first char of this
                    displayable line.
    '''
    line_index: int
    offset: int


class DisplayContent:
    '''Displayable content. Highest level class not dependent on curses.

    Attributes:
        firstdlines  First display line of each selected lines.
        dlines       List of display lines.
    '''
    def __init__(self) -> None:
        self.firstdlines: List[int] = []
        self.dlines: List[DisplayLine] = []

    def lines_count(self) -> int:
        '''Gets the number of lines required to display the whole content
        without clipping any of it.'''
        return len(self.dlines)


class Filter:
    '''Filters are used to select lines and highlight keywords in these
    matching lines. In practice, each filter holds properties defining
    how matching is done and a list of keywords. Keywords can be added
    or removed by end-user.

    Attributes:
        ignore_case  Whether or not matching is done ignoring case.
        hiding       Defines the visibility of lines matching this filter.
        keywords     List of keywords.
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


def digits_count(number: int) -> int:
    '''Returns the number of digits required to display given number'''
    return math.floor(math.log10(max(1, number))+1)


RULER_INDEX = -1


class SelectedLine(NamedTuple):
    '''Data associated with a selected line. A line can be selected either
    because it directly matches a filter, or because it is in proximity of
    another matching line and user has speficy a LineVisibility to reveal
    context.

    Attributes:
        line_index    The index of the line in the original content, or -1
                      if this line does not represent original content (like
                      an horizontal ruler).
        filter_index  The index of the matching filter if any, or -1 otherwise
        text          The actual raw text of the line.
        segments      The segments that will be highlighted.
    '''
    line_index: int
    filter_index: int
    text: str
    segments: List[segments.Segment]


VISIBILITY_TO_SIZE = {
    enums.LineVisibility.ONLY_MATCHING: 0,
    enums.LineVisibility.CONTEXT_1: 1,
    enums.LineVisibility.CONTEXT_2: 2,
    enums.LineVisibility.CONTEXT_5: 5,
    enums.LineVisibility.ALL: -1,
}


class SelectedLineQueue:
    '''Class use to filter out SelectedLine according to a given line
    visibility mode. SelectedLines are added sequentially, one by one,
    and are then yielded back to caller (or not) so as to reveal the
    desired amount of non-matching lines above and below matching
    lines.
    '''
    def __init__(self, mode: enums.LineVisibility):
        self._queue: List[SelectedLine] = []
        assert mode in VISIBILITY_TO_SIZE
        self._size = VISIBILITY_TO_SIZE[mode]
        self._left = 0
        self._last_line_visible = 0

    def _add(self, model: SelectedLine) -> bool:
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

    def _flush(self) -> List[SelectedLine]:
        models = self._queue
        self._queue = []
        return models

    def _update_last_line_visible(self, model: SelectedLine):
        line, _, _, _ = model
        self._last_line_visible = line + 1

    def add_matching(self, model: SelectedLine) -> List[SelectedLine]:
        '''Adds a line model that matches a filter. Returns
        the list of line models that are visible, if any.'''

        models = []
        queued = self._flush()
        if len(queued) > 0:
            # Check if we need to add horizontal rule (index -1)
            line, _, _, _ = queued[0]
            if line > self._last_line_visible:
                models.append(SelectedLine(RULER_INDEX, -1, '', []))
            models = models + queued

        models.append(model)
        self._update_last_line_visible(model)

        # Make sure we are going to bufferize the appropriate amount
        # of subsequent non-matching lines, if we encounter any.
        self._left = self._size

        return models

    def add_non_matching(self, model: SelectedLine) -> List[SelectedLine]:
        '''Adds a line model that does not match any filter. Returns
        the list of line models that are visible, if any.'''
        if not self._add(model):
            return []
        queued = self._flush()
        assert len(queued) == 1
        self._update_last_line_visible(model)
        return queued


class SelectedContent:
    '''Holds filtered content of a file, and generates DisplayContent
    instances according a desired screen layout.

    Attributes:
        lines        List of SelectedLine that each contains information on
                     what segments of the original line matches which filter.
        hits         Keeps how many times each filter was matched.
    '''
    def __init__(self) -> None:
        self.lines: List[SelectedLine] = []
        self.hits: List[int] = []

    def visible_line_count(self) -> int:
        '''Gets the total number of lines that would be visible if not
        limited by screen height'''
        return len(self.lines)

    def hits_count(self) -> int:
        '''Gets the current hits count'''
        return sum(self.hits)

    def layout(self,
               height: int,
               width: int,
               wrapping: bool
               ) -> DisplayContent:
        '''Generate displayable content, breaking the given selected lines
        into displayable lines taking into account the available space
        on the screen.'''

        assert height > 0
        assert width > 0

        dlines: List[DisplayLine] = []
        firstdlines: List[int] = []
        if not wrapping:
            for idata, mdata in enumerate(self.lines):
                firstdlines.append(len(dlines))
                dlines.append(DisplayLine(idata, 0))
        else:
            for idata, mdata in enumerate(self.lines):
                firstdlines.append(len(dlines))
                line_idx, _, text, _ = mdata
                offset = 0
                if line_idx == RULER_INDEX:
                    dlines.append(DisplayLine(idata, offset))
                    continue
                left = len(text)
                while left >= 0:
                    dlines.append(DisplayLine(idata, offset))
                    offset += width
                    left -= width

        assert len(firstdlines) == len(self.lines)
        dc = DisplayContent()
        dc.dlines = dlines
        dc.firstdlines = firstdlines
        return dc


class RawContent:
    '''Holds raw content of a file and generates instances of
    SelectedContent from filters.

    Attributes:
        _lines       Lines of the original file.
    '''
    def __init__(self) -> None:
        self._lines: List[str] = []

    def line_count(self) -> int:
        '''Gets the number of lines in the original file'''
        return len(self._lines)

    def line_number_length(self) -> int:
        '''Number of digit required to display bigest line number'''
        return digits_count(len(self._lines))

    def set_lines(self, lines: List[str]) -> None:
        '''Sets and stores the file content lines.'''
        self._lines = lines

    def filter(self,
               filters: List[Filter],
               mode: enums.LineVisibility
               ) -> SelectedContent:
        '''Filters the raw content using the given filters and line visibility
        mode, and returns an instance of SelectedContent.
        '''
        lines: List[SelectedLine] = []
        hits = [0 for f in filters]
        mode = mode if sum(not f.hiding for f in filters) > 0 \
            else enums.LineVisibility.ALL
        line_queue = SelectedLineQueue(mode)
        for i, line in enumerate(self._lines):
            # Replace tabs with 4 spaces (not clean!!!)
            line = line.replace('\t', '    ')
            assert len(line) <= 0 or ord(line[0]) != 0, \
                f'Line {i} has embedded null character'
            matching = False
            for fidx, f in enumerate(filters):
                matching, matching_segments = \
                    segments.find_matching(line, f.keywords, f.ignore_case)
                if matching:
                    hits[fidx] += 1
                    if not f.hiding:
                        new_lines = line_queue.add_matching(
                            SelectedLine(i, fidx, line, matching_segments))
                        lines = lines + new_lines
                    break
            if not matching:
                new_lines = line_queue.add_non_matching(
                    SelectedLine(i, -1, line, []))
                lines = lines + new_lines

        assert len(filters) == len(hits)
        sc = SelectedContent()
        sc.lines = lines
        sc.hits = hits
        return sc


class ViewConfig:
    '''This class holds the configuration of a view, like filters to use or the
    display modes, typically changed by end users to match their need. Does not
    contain any data related to actual file content, and can get serialized for
    persistence (see storage.py). This class is not a view class per-se in the
    sense that it does NOT depend on curses or anything UI related.
    '''

    # pylint: disable=too-many-instance-attributes

    line_numbers: bool = True
    wrap: bool = True
    bullets: bool = False
    reverse_matching: bool = False
    line_visibility: enums.LineVisibility = enums.LineVisibility.ONLY_MATCHING
    show_all_lines: bool = True
    show_spaces: bool = False
    colorize_mode: enums.ColorizeMode = enums.ColorizeMode.KEYWORD_HIGHLIGHT
    palette_id: types.PaletteId = 0
    dirty: bool = False

    def __init__(self) -> None:
        self.filters: List[Filter] = []

    def get_filters_count(self) -> int:
        '''Returns the number of filters currently defined'''
        return len(self.filters)

    def has_filters(self) -> bool:
        '''Returns whether or not there is any filter'''
        return len(self.filters) > 0

    def top_filter(self) -> Filter:
        '''Returns top level filter (most recently added)'''
        count = len(self.filters)
        assert count > 0
        return self.filters[count-1]

    def push_filter(self, f: Filter) -> None:
        '''Pushes the given filter'''
        self.dirty = True
        self.filters.append(f)

    def swap_filters(self, i, j) -> None:
        '''Swaps the given filters'''
        self.dirty = True
        count = len(self.filters)
        assert 0 <= i < count
        assert 0 <= j < count
        self.filters[i], self.filters[j] = self.filters[j], self.filters[i]

    def rotate_filters(self, go_up: bool) -> None:
        '''Rotates filters'''
        self.dirty = True
        count = len(self.filters)
        assert count >= 2
        if go_up:
            self.filters = self.filters[1:] + self.filters[:1]
        else:
            self.filters = self.filters[-1:] + self.filters[:-1]

    def set_palette(self, pid: types.PaletteId) -> None:
        '''Select the next palette in the given direction'''
        self.dirty = True
        self.palette_id = pid


class Offsets:
    '''Class managing horizontal and vertical offsets in displayable
    content.

    Attributes:
        hoffset      Horizontal offset in content (index of first visible
                     column).
        voffset      Vertical offset in content (index of first visible
                     line).
    '''
    def __init__(self) -> None:
        self.hoffset: int = 0
        self.voffset: int = 0
        self.voffset_desc: str = ''
        self._ymax: int = 0

    def layout(self, available_height: int, content_lines_count: int) -> None:
        '''Layout function defining the space available for the
        displayable content.'''
        assert available_height >= 0
        assert content_lines_count >= 0
        self._ymax = max(0, content_lines_count - available_height)

    def set_h_offset(self, offset: int) -> bool:
        '''Sets the horizontal offset.
        Returns True if changed, False otherwise.'''
        offset = max(offset, 0)
        if self.hoffset == offset:
            return False
        self.hoffset = offset
        return True

    def set_v_offset(self, offset: int) -> bool:
        '''Sets the vertical offfset.
        Returns True if changed, False otherwise.'''
        if offset >= self._ymax:
            offset = self._ymax
            desc = 'BOT'
        elif offset <= 0:
            offset = 0
            desc = 'TOP'
        else:
            percent = int(offset * 100 / self._ymax)
            desc = f'{percent}%'
        if self.voffset == offset:
            return False
        self.voffset = offset
        self.voffset_desc = desc
        return True
