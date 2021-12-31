'''This module contains helper functions to manipulate segments.

A segment is just a pair of indices (start, end) that identifies a
portion of text displayed with a given style. Please note that start
is inclusive, while end is exclusive (meaning end is not part of the
segment).

'''

import re

# We want one letter variable name in simple functions.
# pylint: disable=invalid-name

def _sort_and_merge(segments):
    '''Takes a list of segments, merges overlapping ones and returns the
resulting list cleared off any overlapping segments. This function
only looks at indices. For instance, in "abcde" the 2 keywords "abc"
and "cde" are repectively matching segments (0,3) and (2,5), which
contain overlapping indices. This function merges them as one segment
(0,5).

    '''
    merged = set()
    pending = ()
    for s in sorted(segments):
        assert s[0] < s[1]
        if not pending:
            pending = s
        elif pending[1] >= s[0]:
            pending = (pending[0], max(pending[1], s[1]))
        else:
            merged.add(pending)
            pending = s
    if pending:
        merged.add(pending)
    return sorted(merged)

def find_matching(text, keywords, ignore_case):
    '''Returns True and the segments matching any of the given keywords if
each keyword is found at least once in the given text, False and an
empty set otherwise.

    '''
    assert len(keywords) > 0
    flags = re.IGNORECASE if ignore_case else 0
    s = set() # Use a set() as multiple matches are possible
    for k in keywords:
        matching = False
        for m in re.finditer(k, text, flags):
            matching = True
            s.add((m.start(), m.end()))
        if not matching:
            # Bail out early as soon as one keyword has no match
            return False, set()

    # Sort all segments and then merge them as overlap can happen
    return True, _sort_and_merge(s)

def iterate(start, end, matching_segments):
    '''This function is used to build the list of text draw commands
required to display a line containing highlighted keywords.

The given 'matching_segments' is a list of pair of indices defining
the segments of a string that must be highlighted. iterate() returns
these highlighted segments with True to indicate they should be
highlighted but interleaves them with the non-matching complementary
segments returned with False, indicating they should not be
highlighted. Finally, start and end are indices defining the
boundaries we actually care about.

    '''
    assert start < end
    for s in matching_segments:
        assert s[0] < s[1] # Paranoid overkill assert

        if start >= end:
            # start has moved past the area of interest: could
            # break out but we are done for good so return!
            return

        # Consume "s", the current matching segment, by inspecting
        # its relative position with (start, end) segment.

        if start >= s[1]:
            # The current matching segment is of no interest, but we
            # need to keep iterating to find next matching segment of
            # interest to the right (if any)
            continue
        if end < s[0]:
            # Current matching segment and all remaining ones (on the
            # right) are of no interest. (start, end) defines a non
            # matching segment that we yield after breaking out of the
            # for loop
            break
        if start < s[0]:
            # There is a non-matching segment before s that we must
            # yield now
            yield (False, start, s[0])
            start = s[0]
        # Take care of matching segment within s (if any)
        matching_end = min(s[1], end)
        if start < matching_end:
            yield (True, start, matching_end)
        # s has been entirely consumed
        start = s[1]

    # We walked through all matching_segments (if any), we now need to
    # address any non-matching segment that has been left out
    if start < end:
        yield (False, start, end)
