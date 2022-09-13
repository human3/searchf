'''Unit tests for enums'''

from .. import enums

class DummyEnum(enums.AutoEnum):
    '''Test enum.'''
    FIRST_VALUE = ('First')
    MIDDLE_VALUE = ('Middle')
    LAST_VALUE = ('Last')

def test_get_next_prev():
    '''Test enums.get_next and enums.get_prev'''
    assert DummyEnum.LAST_VALUE.get_next() \
        == DummyEnum.FIRST_VALUE
    assert DummyEnum.LAST_VALUE \
        == DummyEnum.FIRST_VALUE.get_prev()

def test_from_int():
    '''Test enums can be converted from int.'''
    actual = None
    try:
        DummyEnum.from_int(12)
    except ValueError as ex:
        actual = ex
    assert actual
