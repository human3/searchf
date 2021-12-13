import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import searchf

def test_iter_segments(start, end, segments, expected_segments):
    actual_segments = list(searchf.iter_segments(start, end, segments))
    assert len(actual_segments) == len(expected_segments)
    for actual, expected in zip(actual_segments, expected_segments):
        _, start, end = actual
        assert start < end, f'{start} {end} not a segment!'
        assert actual == expected, f'{actual} != {expected}'

def test_sort_and_merge_segments(segments, expected_segments):
    count = 0
    for actual, expected in zip(searchf.sort_and_merge_segments(segments), expected_segments):
        assert actual[0] < actual[1]
        assert actual == expected, f'{actual} != {expected}'
        count += 1
    assert count == len(expected_segments)

def tests():
    segments = {(5, 15), (25, 35)}

    print('test_iter_segments')
    test_iter_segments(0, 20, {(11, 12), (20, 21)},
                       [(False, 0, 11), (True, 11, 12), (False, 12, 20)])
    test_iter_segments(0, 50, segments,
                       [(False, 0, 5), (True, 5, 15), (False, 15, 25), (True, 25, 35), (False, 35, 50)])
    test_iter_segments(10, 20, segments,
                       [(True, 10, 15), (False, 15, 20)])
    test_iter_segments(0, 4, segments,
                       [(False, 0, 4)])
    test_iter_segments(7, 12, segments,
                       [(True, 7, 12)])
    test_iter_segments(17, 20, segments,
                       [(False, 17, 20)])
    test_iter_segments(10, 50, segments,
                       [(True, 10, 15), (False, 15, 25), (True, 25, 35), (False, 35, 50)])
    test_iter_segments(0, 10, {(5, 15)},
                       [(False, 0, 5), (True, 5, 10)])

    print('test_sort_and_merge_segments')
    segments = {(0,1), (2,3)}
    test_sort_and_merge_segments(segments, segments)
    test_sort_and_merge_segments({(2,3),(0,1)}, {(0,1),(2,3)})
    test_sort_and_merge_segments({(0,1),(1,2)}, {(0,2)})
    test_sort_and_merge_segments({(0,3),(1,5)}, {(0,5)})

if __name__ == '__main__':
    tests()
