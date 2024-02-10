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
    attr: int  # Filter index if < 256, or raw curses attributes


def merge(bottom: List[Segment], top: List[Segment]) -> List[Segment]:
    '''Merge 2 layers of segment into one single layer. All segments of the
    top layer remain on top and visible, while segments of the bottom layer
    can be partially or completely obstructed by overlapping segments from
    the top layer.

    '''
    merged: List[Segment] = []

    # The logic here is to primarily iterate over each bottom segment and then
    # consume all the top segments (if any) that are overlapping the current
    # bottom segment.
    i_b = 0
    i_t = 0
    while i_b < len(bottom):
        assert bottom[i_b].start < bottom[i_b].end
        if i_t >= len(top):
            # we consumed all tops, so just add all the bottoms
            merged.append(bottom[i_b])
            i_b += 1
            continue
        assert top[i_t].start < top[i_t].end
        if top[i_t].end <= bottom[i_b].start:
            # top is clear ahead
            merged.append(top[i_t])
            i_t += 1
            continue
        if top[i_t].start >= bottom[i_b].end:
            # bottom is clear ahead
            merged.append(bottom[i_b])
            i_b += 1
            continue
        # we have some overlap
        bot = bottom[i_b]
        i_bnext = bot.start
        while i_bnext < bot.end:
            if i_t >= len(top):
                # we consumed all tops, so just add last segment of bottom
                if i_bnext < bot.end:
                    merged.append(Segment(i_bnext, bot.end, bot.attr))
                break
            assert top[i_t].start < top[i_t].end
            if top[i_t].start <= i_bnext:
                merged.append(top[i_t])
                i_bnext = top[i_t].end
                i_t += 1
                continue
            end = min(top[i_t].start, bot.end)
            merged.append(Segment(i_bnext, end, bot.attr))
            i_bnext = end
        i_b += 1

    assert i_b >= len(bottom)

    while i_t < len(top):
        merged.append(top[i_t])
        i_t += 1

    return merged


def flatten(layers: List[List[Segment]]) -> List[Segment]:
    '''Flatten the array of layers into one single layers.'''
    assert len(layers) > 0
    merged = layers[0]
    for i in range(1, len(layers)):
        merged = merge(merged, layers[i])
    return merged


def sort_and_merge(segments: Set[Segment]) -> List[Segment]:
    '''Merges overlapping segments belonging to the same filter, sort them, and
    returns a clean sorted list of non overlapping segments. For instance, in
    "abcde" the 2 keywords "abc" and "cde" are repectively matching segments
    (0,3) and (2,5) which are overlapping. This function would merge them as
    one segment (0,5).
    '''
    merged: Set[Segment] = set()
    pending: Optional[Segment] = None
    for cur in sorted(segments):
        assert cur.start < cur.end
        if not pending:
            pending = cur
        elif pending.end >= cur.start:
            assert pending.attr == cur.attr
            pending = Segment(
                pending.start, max(pending.end, cur.end), cur.attr)
        else:
            merged.add(pending)
            pending = cur
    if pending:
        merged.add(pending)
    return sorted(merged)


def find_matching(
        text: str,
        keywords,
        ignore_case: bool,
        attr: int,
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
            matching.add(Segment(match.start(), match.end(), attr))
        if not is_matching:
            # Bail out early as soon as one keyword has no match
            return False, []

    # Sort all segments and then merge them as overlap can happen
    return True, sort_and_merge(matching)


def iterate(
        start: int,
        end: int,
        matching_segments: List[Segment]
        ) -> Iterable[Tuple[bool, int, int, int]]:
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
            yield (False, start, cur.start, -1)
            start = cur.start
        # Take care of matching segment within s (if any)
        matching_end = min(cur.end, end)
        if start < matching_end:
            yield (True, start, matching_end, cur.attr)
        # s has been entirely consumed
        start = cur.end

    # We walked through all matching_segments (if any), we now need to
    # address any non-matching segment that has been left out
    if start < end:
        yield (False, start, end, -1)
