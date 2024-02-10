'''Unit tests for segments'''

from .. import segments


def _iterate(start, end, test_segments, expected_segments):
    actual_segments = list(segments.iterate(start, end, test_segments))
    assert len(actual_segments) == len(expected_segments)
    for actual, expected in zip(actual_segments, expected_segments):
        _, start, end, _ = actual
        assert start < end, f'{start} {end} not a segment!'
        assert actual == expected, f'{actual} != {expected}'


def test_iterate():
    '''Test segments.iterate()'''
    _iterate(0, 20,
             {segments.Segment(11, 12, -1), segments.Segment(20, 21, -1)},
             [(False, 0, 11, -1), (True, 11, 12, -1), (False, 12, 20, -1)])
    seg = {segments.Segment(5, 15, -1), segments.Segment(25, 35, -1)}
    _iterate(0, 50, seg,
             [(False, 0, 5, -1), (True, 5, 15, -1), (False, 15, 25, -1),
              (True, 25, 35, -1), (False, 35, 50, -1)])
    _iterate(10, 20, seg,
             [(True, 10, 15, -1), (False, 15, 20, -1)])
    _iterate(0, 4, seg,
             [(False, 0, 4, -1)])
    _iterate(7, 12, seg,
             [(True, 7, 12, -1)])
    _iterate(17, 20, seg,
             [(False, 17, 20, -1)])
    _iterate(10, 50, seg,
             [(True, 10, 15, -1), (False, 15, 25, -1), (True, 25, 35, -1),
              (False, 35, 50, -1)])
    _iterate(0, 10, {segments.Segment(5, 15, -1)},
             [(False, 0, 5, -1), (True, 5, 10, -1)])


def _sort_and_merge(test_segments, expected_segments):
    count = 0
    for actual, expected in zip(
            segments.sort_and_merge(test_segments), expected_segments):
        assert actual[0] < actual[1]
        assert actual == expected, f'{actual} != {expected}'
        count += 1
    assert count == len(expected_segments)


def test_sort_and_merge():
    '''Test segments.sort_and_merge()'''
    seg = {segments.Segment(0, 1, -1), segments.Segment(2, 3, -1)}
    _sort_and_merge(seg, seg)
    _sort_and_merge({segments.Segment(2, 3, -1), segments.Segment(0, 1, -1)},
                    {segments.Segment(0, 1, -1), segments.Segment(2, 3, -1)})
    _sort_and_merge({segments.Segment(0, 1, -1), segments.Segment(1, 2, -1)},
                    {segments.Segment(0, 2, -1)})
    _sort_and_merge({segments.Segment(0, 3, -1), segments.Segment(1, 5, -1)},
                    {segments.Segment(0, 5, -1)})


def _find_matching(text, keywords, ignore_case, expected):
    actual = segments.find_matching(text, keywords, ignore_case, -1)
    assert actual[0] == expected[0]
    assert actual[1] == expected[1]


def test_find_matching():
    '''Test segments.find_matching()'''
    no_match = (False, [])
    # Checking matching empty line works
    _find_matching('\n', ['^\n'], False, (True, [(0, 1, -1)]))
    # Checking matching null string does not crash program
    _find_matching('012345', ['^'], False, no_match)
    _find_matching('012345', ['$'], False, no_match)
    # Basic non matching cases
    _find_matching('Some text', {'Not matching'}, False, no_match)
    _find_matching('abcde', {'cdefgh'}, False, no_match)
    _find_matching('abcde', {'0123abc'}, False, no_match)
    # Checking case sensitive matching
    _find_matching('a', ['a'], False, (True, [(0, 1, -1)]))
    _find_matching('a', ['A'], True, (True, [(0, 1, -1)]))
    _find_matching('a', ['A'], False, no_match)
    # Basic matching
    _find_matching('abcde', {'abcde'}, False, (True, [(0, 5, -1)]))
    _find_matching('abcde', {'bcd'}, False, (True, [(1, 4, -1)]))
    _find_matching('abcde', {'a', 'c', 'e'}, False,
                   (True, [(0, 1, -1), (2, 3, -1), (4, 5, -1)]))
    _find_matching('abcde', {'b', 'd'}, False,
                   (True, [(1, 2, -1), (3, 4, -1)]))
    # Overlapping matches
    _find_matching('abcdef', {'bcd', 'cde'}, False,
                   (True, [(1, 5, -1)]))


def make_s(args):
    '''Helper function to make segment'''
    return segments.Segment._make(args)


def test_merge():
    '''Test segments.merge()'''

    merged = segments.merge([], [])
    assert len(merged) == 0

    merged = segments.merge([make_s((1, 2, 3))], [])
    assert len(merged) == 1
    assert merged[0] == (1, 2, 3)

    merged = segments.merge([], [make_s((1, 2, 3))])
    assert len(merged) == 1
    assert merged[0] == (1, 2, 3)

    # bottom clear ahead
    merged = segments.merge([make_s((1, 2, 0))], [make_s((10, 20, 1))])
    assert len(merged) == 2
    assert merged[0] == (1, 2, 0)
    assert merged[1] == (10, 20, 1)

    # top covers whole bottom
    merged = segments.merge([make_s((10, 20, 0))], [make_s((0, 30, 1))])
    assert len(merged) == 1
    assert merged[0] == (0, 30, 1)

    # top covers middle of bottom
    merged = segments.merge([make_s((0, 30, 0))], [make_s((10, 20, 1))])
    assert len(merged) == 3
    assert merged[0] == (0, 10, 0)
    assert merged[1] == (10, 20, 1)
    assert merged[2] == (20, 30, 0)

    # top covers only start of bottom
    merged = segments.merge([make_s((10, 20, 0))], [make_s((5, 15, 1))])
    assert len(merged) == 2
    assert merged[0] == (5, 15, 1)
    assert merged[1] == (15, 20, 0)

    # top covers only end of bottom
    merged = segments.merge([make_s((10, 20, 0))], [make_s((15, 25, 1))])
    assert len(merged) == 2
    assert merged[0] == (10, 15, 0)
    assert merged[1] == (15, 25, 1)

    # multiple tops that only covers middle of bottom
    merged = segments.merge(
        [make_s((10, 30, 0))],
        [make_s((12, 20, 1)), make_s((25, 28, 1))])
    assert len(merged) == 5
    assert merged[0] == (10, 12, 0)
    assert merged[1] == (12, 20, 1)
    assert merged[2] == (20, 25, 0)
    assert merged[3] == (25, 28, 1)
    assert merged[4] == (28, 30, 0)

    # Overlap start
    merged = segments.merge(
        [make_s((10, 20, 0))],
        [make_s((0, 1, 1)), make_s((2, 3, 1))])
    assert len(merged) == 3
    assert merged[0] == (0, 1, 1)
    assert merged[1] == (2, 3, 1)
    assert merged[2] == (10, 20, 0)


def test_flatten():
    '''Test segments.flatten()'''

    merged = segments.flatten(
        [
            [make_s((0, 30, 0))],
            [make_s((5, 25, 1))],
            [make_s((10, 20, 2))]
        ]
    )
    assert len(merged) == 5
    assert merged[0] == (0, 5, 0)
    assert merged[1] == (5, 10, 1)
    assert merged[2] == (10, 20, 2)
    assert merged[3] == (20, 25, 1)
    assert merged[4] == (25, 30, 0)

    merged = segments.flatten(
        [
            [make_s((0, 5, 1))],
            [
                make_s((3, 4, 0)),
                make_s((10, 11, 0))
            ]
        ]
    )
    assert len(merged) == 4, merged
    assert merged[0] == (0, 3, 1)
    assert merged[1] == (3, 4, 0)
    assert merged[2] == (4, 5, 1)
    assert merged[3] == (10, 11, 0)
