'''This module contains helper functions to define and manipulate segments.
'''

import re

from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Iterable
from typing import Set
from typing import Tuple


class Segment(NamedTuple):
    '''A segment is a pair of indices (start, end) that identifies a
    portion of text displayed with a given style. Please note that
    start is inclusive, while end is exclusive.
    '''
    start: int
    end: int


def sort_and_merge(segments: Set[Segment]) -> List[Segment]:
    '''Merges overlapping segments, sorts them, and returns a clean sorted
    list of non overlapping segments. For instance, in "abcde" the 2
    keywords "abc" and "cde" are repectively matching segments (0,3)
    and (2,5) which are overlapping. This function would merge them as
    one segment (0,5).
    '''
    merged: Set[Segment] = set()
    pending: Optional[Segment] = None
    for cur in sorted(segments):
        assert cur.start < cur.end
        if not pending:
            pending = cur
        elif pending.end >= cur.start:
            pending = Segment(pending.start, max(pending.end, cur.end))
        else:
            merged.add(pending)
            pending = cur
    if pending:
        merged.add(pending)
    return sorted(merged)


def find_matching(
        text: str,
        keywords,
        ignore_case: bool
        ) -> Tuple[bool, List[Segment]]:
    '''Returns True and the segments matching any of the given keywords if
    each keyword is found at least once in the given text, False and
    an empty list otherwise.
    '''
    assert len(keywords) > 0
    flags = re.IGNORECASE if ignore_case else 0
    matching: Set[Segment] = set()
    # matching is a set() as multiple matches are possible
    for k in keywords:
        is_matching = False
        for match in re.finditer(k, text, flags):
            if match.start() >= match.end():
                continue
            is_matching = True
            matching.add(Segment(match.start(), match.end()))
        if not is_matching:
            # Bail out early as soon as one keyword has no match
            return False, []

    # Sort all segments and then merge them as overlap can happen
    return True, sort_and_merge(matching)


def iterate(
        start: int,
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
    for cur in matching_segments:
        assert cur.start < cur.end  # Paranoid overkill assert

        if start >= end:
            # start has moved past the area of interest: could
            # break out but we are done for good so return!
            return

        # Consume "s", the current matching segment, by inspecting
        # its relative position with (start, end) segment.

        if start >= cur.end:
            # The current matching segment is of no interest, but we
            # need to keep iterating to find next matching segment of
            # interest to the right (if any)
            continue
        if end < cur.start:
            # Current matching segment and all remaining ones (on the
            # right) are of no interest. (start, end) defines a non
            # matching segment that we yield after breaking out of the
            # for loop
            break
        if start < cur.start:
            # There is a non-matching segment before s that we must
            # yield now
            yield (False, start, cur.start)
            start = cur.start
        # Take care of matching segment within s (if any)
        matching_end = min(cur.end, end)
        if start < matching_end:
            yield (True, start, matching_end)
        # s has been entirely consumed
        start = cur.end

    # We walked through all matching_segments (if any), we now need to
    # address any non-matching segment that has been left out
    if start < end:
        yield (False, start, end)
