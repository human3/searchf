'''Unit tests for models'''

# pylint: disable=invalid-name
# pylint: disable=protected-access

from .. import models

def test_matching_mode():
    '''Test models.MatchingMode'''
    assert models.MatchingMode.ALL_LINES.get_next() == models.MatchingMode.ONLY_MATCHING_LINES
    assert models.MatchingMode.ALL_LINES == models.MatchingMode.ONLY_MATCHING_LINES.get_prev()
    assert models.MatchingMode.ONLY_NOT_MATCHING.get_next() == models.MatchingMode.ALL_LINES
    assert models.MatchingMode.ONLY_NOT_MATCHING == models.MatchingMode.ALL_LINES.get_prev()

    actual = None
    try:
        models.MatchingMode._from_int(12)
    except ValueError as ex:
        actual = ex
    assert actual

def test_filter():
    '''Test models.Filter'''
    f = models.Filter()
    f.add('Keyword')
    f.pop()

def test_digit_count():
    '''Test models._digit_count()'''
    assert 1 == models._digits_count(0)
    assert 1 == models._digits_count(9)
    assert 2 == models._digits_count(10)
    assert 2 == models._digits_count(99)
    assert 6 == models._digits_count(123456)

def test_model():
    '''Test models.Model'''
    m = models.Model()
    assert 0 == m.line_count()
    assert 0 == m.hits_count()

    m.set_lines([])
    assert 0 == m.line_count()
    assert 1 == m.line_number_length()

    m.set_lines(['A very simple first line', 'Another line', 'And a third one'])
    assert 3 == m.line_count()
    assert 1 == m.line_number_length()

    m.sync([], False)
    assert 0 == m.hits_count()

    f = models.Filter()
    f.add('not match')
    m.sync([f], False)
    assert 0 == m.hits_count()
    assert 3 == m.line_count()

    f.pop()
    f.add('line')
    m.sync([f], False)
    assert 2 == m.hits_count()
    assert 3 == m.line_count()
    m.sync([f], True)
    assert 2 == m.hits_count()

def test_view_model():
    '''Test models.ViewModel'''
    vm = models.ViewModel()

    m = models.Model()
    m.set_lines(['A very simple first line', 'Another line', 'And a third one'])
    m.sync([], False)

    vm.layout(1, 1, m.data, True)
    vm.layout(1, 1, m.data, False)

    vm.reset_offsets()
    vm.set_h_offset(0)
    vm.set_h_offset(100)
    vm.set_v_offset(0)
    vm.set_v_offset(1)
    vm.set_v_offset(100)
