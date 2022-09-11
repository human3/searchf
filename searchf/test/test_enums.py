'''Unit tests for enums'''

from .. import enums


def test_visibility_mode():
    '''Test enums.LineVisibility'''
    assert enums.LineVisibility.HIDE_MATCHING.get_next() \
        == enums.LineVisibility.ONLY_MATCHING
    assert enums.LineVisibility.HIDE_MATCHING \
        == enums.LineVisibility.ONLY_MATCHING.get_prev()

def test_from_int():
    '''Test enums can be converted from int.'''
    actual = None
    try:
        enums.LineVisibility.from_int(12)
    except ValueError as ex:
        actual = ex
    assert actual
