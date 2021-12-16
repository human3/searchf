# A word on segments as used by this program to identify portion of text in a string:
# a segment is a pair of indices (start, end) that identify a portion of text

def sort_and_merge_segments(segments):
    '''Takes a list of segments, merges overlapping ones and returns the resulting
list cleared off any overlapping segments. This function only looks at
indices. For instance, in "abcde" the 2 keywords "abc" and "cde" are repectively
matching segments (0,3) and (2,5), which contain overlapping indices. This
function would merge them as one segment (0,5).'''
    merged = set()
    pending = ()
    for c in sorted(segments):
        assert c[0] < c[1]
        if not pending:
            pending = c
        elif pending[1] >= c[0]:
            pending = (pending[0], max(pending[1], c[1]))
        else:
            merged.add(pending)
            pending = c
    if pending:
        merged.add(pending)
    return sorted(merged)

def iter_segments(start, end, segments):
    '''This function is used to build the list of text draw commands required to
display a line containing highlighted keywords.

The given 'segments' is a list of pair of indices defining the segments of a
string that must be highlighted. iter_segments() returns these highlighted
segments with True to indicate they should be highlighted but interleaves them
with the non-matching complementary segments returned with False, indicating
they should not be highlighted. Finally, start and end are indices defining the
boundaries we actually care about.'''
    assert start < end
    for c in segments:
        if start >= c[1]:
            continue
        if end < c[0]:
            if start < end:
                yield (False, start, end)
            return
        if start < c[0]:
            yield (False, start, c[0])
            if end < c[1]:
                if c[0] < end:
                    yield (True, c[0], end)
                return
            yield (True, c[0], c[1])
        elif start < c[1]:
            assert start < min(c[1], end)
            yield (True, start, min(c[1], end))
            if end < c[1]:
                return
        start = c[1]
    if start < end:
        yield (False, start, end)
