'''Unit tests for segments'''

from .. import segments


def _iterate(start, end, test_segments, expected_segments):
    actual_segments = list(segments.iterate(start, end, test_segments))
    assert len(actual_segments) == len(expected_segments)
    for actual, expected in zip(actual_segments, expected_segments):
        _, start, end = actual
        assert start < end, f'{start} {end} not a segment!'
        assert actual == expected, f'{actual} != {expected}'


def test_iterate():
    '''Test segments.iterate()'''
    seg = {segments.Segment(5, 15), segments.Segment(25, 35)}
    _iterate(0, 20, {segments.Segment(11, 12), segments.Segment(20, 21)},
             [(False, 0, 11), (True, 11, 12), (False, 12, 20)])
    _iterate(0, 50, seg,
             [(False, 0, 5), (True, 5, 15), (False, 15, 25), (True, 25, 35), (False, 35, 50)])
    _iterate(10, 20, seg,
             [(True, 10, 15), (False, 15, 20)])
    _iterate(0, 4, seg,
             [(False, 0, 4)])
    _iterate(7, 12, seg,
             [(True, 7, 12)])
    _iterate(17, 20, seg,
             [(False, 17, 20)])
    _iterate(10, 50, seg,
             [(True, 10, 15), (False, 15, 25), (True, 25, 35), (False, 35, 50)])
    _iterate(0, 10, {segments.Segment(5, 15)},
             [(False, 0, 5), (True, 5, 10)])


def _sort_and_merge(test_segments, expected_segments):
    count = 0
    # pylint: disable=protected-access
    for actual, expected in zip(segments._sort_and_merge(test_segments), expected_segments):
        assert actual[0] < actual[1]
        assert actual == expected, f'{actual} != {expected}'
        count += 1
    assert count == len(expected_segments)


def test_sort_and_merge():
    '''Test segments._sort_and_merge()'''
    seg = {segments.Segment(0, 1), segments.Segment(2, 3)}
    _sort_and_merge(seg, seg)
    _sort_and_merge({segments.Segment(2, 3), segments.Segment(0, 1)},
                    {segments.Segment(0, 1), segments.Segment(2, 3)})
    _sort_and_merge({segments.Segment(0, 1), segments.Segment(1, 2)},
                    {segments.Segment(0, 2)})
    _sort_and_merge({segments.Segment(0, 3), segments.Segment(1, 5)},
                    {segments.Segment(0, 5)})


def _find_matching(text, keywords, ignore_case, expected):
    actual = segments.find_matching(text, keywords, ignore_case)
    assert actual[0] == expected[0]
    assert actual[1] == expected[1]


def test_find_matching():
    '''Test segments.find_matching()'''
    no_match = (False, [])
    # Checking matching empty line works
    _find_matching('\n', ['^\n'], False, (True, [(0, 1)]))
    # Checking matching null string does not crash program
    _find_matching('012345', ['^'], False, no_match)
    _find_matching('012345', ['$'], False, no_match)
    # Basic non matching cases
    _find_matching('Some text', {'Not matching'}, False, no_match)
    _find_matching('abcde', {'cdefgh'}, False, no_match)
    _find_matching('abcde', {'0123abc'}, False, no_match)
    # Checking case sensitive matching
    _find_matching('a', ['a'], False, (True, [(0, 1)]))
    _find_matching('a', ['A'], True, (True, [(0, 1)]))
    _find_matching('a', ['A'], False, no_match)
    # Basic matching
    _find_matching('abcde', {'abcde'}, False, (True, [(0, 5)]))
    _find_matching('abcde', {'bcd'}, False, (True, [(1, 4)]))
    _find_matching('abcde', {'a', 'c', 'e'}, False, (True, [(0, 1), (2, 3), (4, 5)]))
    _find_matching('abcde', {'b', 'd'}, False, (True, [(1, 2), (3, 4)]))
    # Overlapping matches
    _find_matching('abcdef', {'bcd', 'cde'}, False, (True, [(1, 5)]))
