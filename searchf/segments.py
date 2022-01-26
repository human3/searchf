'''This module contains helper functions to define and manipulate segments.
'''

import re

from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Iterable
from typing import Set
from typing import Tuple

# We want one letter variable name in simple functions.
# pylint: disable=invalid-name


class Segment(NamedTuple):
    '''A segment is a pair of indices (start, end) that identifies a
    portion of text displayed with a given style. Please note that
    start is inclusive, while end is exclusive.
    '''
    start: int
    end: int


def _sort_and_merge(segments: Set[Segment]) -> List[Segment]:
    '''Merges overlapping segments, sorts them, and returns a clean sorted
    list of non overlapping segments. For instance, in "abcde" the 2
    keywords "abc" and "cde" are repectively matching segments (0,3)
    and (2,5) which are overlapping. This function would merge them as
    one segment (0,5).
    '''
    merged: Set[Segment] = set()
    pending: Optional[Segment] = None
    for s in sorted(segments):
        assert s.start < s.end
        if not pending:
            pending = s
        elif pending.end >= s.start:
            pending = Segment(pending.start, max(pending.end, s.end))
        else:
            merged.add(pending)
            pending = s
    if pending:
        merged.add(pending)
    return sorted(merged)


def find_matching(text: str, keywords, ignore_case: bool) -> Tuple[bool, List[Segment]]:
    '''Returns True and the segments matching any of the given keywords if
    each keyword is found at least once in the given text, False and
    an empty list otherwise.
    '''
    assert len(keywords) > 0
    flags = re.IGNORECASE if ignore_case else 0
    s: Set[Segment] = set()  # Use a set() as multiple matches are possible
    for k in keywords:
        matching = False
        for m in re.finditer(k, text, flags):
            if m.start() >= m.end():
                continue
            matching = True
            s.add(Segment(m.start(), m.end()))
        if not matching:
            # Bail out early as soon as one keyword has no match
            return False, []

    # Sort all segments and then merge them as overlap can happen
    return True, _sort_and_merge(s)


def iterate(start: int,
            end: int,
            matching_segments: List[Segment]
            ) -> Iterable[Tuple[bool, int, int]]:
    '''This function is used to build the list of text draw commands to
    display a line containing highlighted keywords. Text draws
    commands are yielded for left to right drawing, alternating
    highlighted segments (prefixed by True) with normal ones (prefixed
    by False).

    The arguments start and end define the boundaries of the text we
    care about, and constrain all the returned draw commands. The
    given 'matching_segments' define the segments that must be
    highlighted.
    '''
    assert start < end
    for s in matching_segments:
        assert s.start < s.end  # Paranoid overkill assert

        if start >= end:
            # start has moved past the area of interest: could
            # break out but we are done for good so return!
            return

        # Consume "s", the current matching segment, by inspecting
        # its relative position with (start, end) segment.

        if start >= s.end:
            # The current matching segment is of no interest, but we
            # need to keep iterating to find next matching segment of
            # interest to the right (if any)
            continue
        if end < s.start:
            # Current matching segment and all remaining ones (on the
            # right) are of no interest. (start, end) defines a non
            # matching segment that we yield after breaking out of the
            # for loop
            break
        if start < s.start:
            # There is a non-matching segment before s that we must
            # yield now
            yield (False, start, s.start)
            start = s.start
        # Take care of matching segment within s (if any)
        matching_end = min(s.end, end)
        if start < matching_end:
            yield (True, start, matching_end)
        # s has been entirely consumed
        start = s.end

    # We walked through all matching_segments (if any), we now need to
    # address any non-matching segment that has been left out
    if start < end:
        yield (False, start, end)
