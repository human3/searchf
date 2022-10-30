'''Unit tests for models'''

from .. import enums
from .. import models


def test_filter():
    '''Test models.Filter'''
    f = models.Filter()
    f.add('Keyword')

    count, keyword = f.get_count_and_last_keyword()
    assert count == 1
    assert keyword == 'Keyword'

    f.pop()
    count, keyword = f.get_count_and_last_keyword()
    assert count == 0
    assert not keyword


def test_digit_count():
    '''Test models.digit_count()'''
    assert models.digits_count(0) == 1
    assert models.digits_count(9) == 1
    assert models.digits_count(10) == 2
    assert models.digits_count(99) == 2
    assert models.digits_count(123456) == 6


def test_model():
    '''Test models.Model'''
    m = models.Model()
    assert m.line_count() == 0
    assert m.hits_count() == 0

    m.set_lines([])
    assert m.line_count() == 0
    assert m.line_number_length() == 1

    all_lines = [
        'A very simple first line',
        'Another line',
        'And a third one',
        'A fourth',
        'And finally the very last one']
    m.set_lines(all_lines)
    assert m.line_number_length() == 1

    m.sync([], enums.LineVisibility.ALL)
    assert m.hits_count() == 0

    f = models.Filter()
    f.add('not match')
    m.sync([f], enums.LineVisibility.ALL)
    assert m.hits_count() == 0
    assert m.line_count() == len(all_lines)

    f.pop()
    f.add('simple')
    m.sync([f], enums.LineVisibility.ALL)
    assert m.hits_count() == 1
    assert m.visible_line_count() == len(all_lines)
    m.sync([f], enums.LineVisibility.CONTEXT_1)
    assert m.visible_line_count() == 2
    m.sync([f], enums.LineVisibility.ONLY_MATCHING)
    assert m.visible_line_count() == 1

    f.pop()
    f.add('line')
    m.sync([f], enums.LineVisibility.ALL)
    assert m.hits_count() == 2
    assert m.visible_line_count() == len(all_lines)
    m.sync([f], enums.LineVisibility.ONLY_MATCHING)
    assert m.visible_line_count() == 2

    f.pop()
    f.add('Another')
    m.sync([f], enums.LineVisibility.ALL)
    assert m.hits_count() == 1
    assert m.visible_line_count() == len(all_lines)
    m.sync([f], enums.LineVisibility.CONTEXT_1)
    assert m.visible_line_count() == 3
    m.sync([f], enums.LineVisibility.CONTEXT_2)
    assert m.visible_line_count() == 4
    m.sync([f], enums.LineVisibility.CONTEXT_5)
    assert m.visible_line_count() == 5
    m.sync([f], enums.LineVisibility.ONLY_MATCHING)
    assert m.visible_line_count() == 1

    # Add a ruler
    f.pop()
    f.add('very')
    m.sync([f], enums.LineVisibility.CONTEXT_1)
    assert m.hits_count() == 2


def test_view_model():
    '''Test models.ViewModel'''
    vm = models.ViewModel()

    m = models.Model()
    m.set_lines([
        'A very simple first line',
        'Another line',
        'And a third one'])
    m.sync([], enums.LineVisibility.ALL)

    vm.layout(1, 1, m.data, True)
    vm.layout(1, 1, m.data, False)

    vm.set_h_offset(0)
    vm.set_h_offset(100)
    vm.set_v_offset(0)
    vm.set_v_offset(1)
    vm.set_v_offset(100)


def test_view_config():
    '''Test models.ViewConfig'''
    vc = models.ViewConfig()
    assert not vc.has_filters()

    last = models.Filter()
    vc.push_filter(last)
    assert vc.has_filters()
    assert vc.get_filters_count() == 1
    assert last == vc.top_filter()

    last = models.Filter()
    vc.push_filter(last)
    assert vc.get_filters_count() == 2
    assert last == vc.top_filter()
    vc.swap_filters(0, 1)
    assert last != vc.top_filter()

    vc.rotate_filters(False)
    assert last == vc.top_filter()
    vc.rotate_filters(True)
    assert last != vc.top_filter()

    vc.set_palette(1)
