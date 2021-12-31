'''Unit tests for searchf.models'''

# pylint: disable=invalid-name
# pylint: disable=protected-access

import searchf.models

def test_filter():
    '''Test searchf.models.Filter'''
    f = searchf.models.Filter()
    f.add('Keyword')
    f.pop()

def test_digit_count():
    '''Test searchf.models._digit_count()'''
    assert 1 == searchf.models._digits_count(0)
    assert 1 == searchf.models._digits_count(9)
    assert 2 == searchf.models._digits_count(10)
    assert 2 == searchf.models._digits_count(99)
    assert 6 == searchf.models._digits_count(123456)

def test_model():
    '''Test searchf.models.Model'''
    m = searchf.models.Model()
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

    f = searchf.models.Filter()
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
    '''Test searchf.models.ViewModel'''
    vm = searchf.models.ViewModel()

    m = searchf.models.Model()
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
