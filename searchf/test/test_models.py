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


SGR_MODE = enums.SgrMode.REMOVE


def test_model():
    '''Test models.RawContent'''
    rc = models.RawContent()
    assert rc.line_count() == 0

    rc.set_lines([])
    assert rc.line_count() == 0
    assert rc.line_number_length() == 1

    all_lines = [
        'A very simple first line',
        'Another line',
        'And a third one',
        'A fourth',
        'And finally the very last one']
    rc.set_lines(all_lines)
    assert rc.line_count() == len(all_lines)
    assert rc.line_number_length() == 1

    sc = rc.filter([], enums.LineVisibility.ALL, SGR_MODE)
    assert sc.hits_count() == 0

    f = models.Filter()
    f.add('not match')
    sc = rc.filter([f], enums.LineVisibility.ALL, SGR_MODE)
    assert sc.hits_count() == 0

    f.pop()
    f.add('simple')
    sc = rc.filter([f], enums.LineVisibility.ALL, SGR_MODE)
    assert sc.hits_count() == 1
    assert sc.visible_line_count() == len(all_lines)
    sc = rc.filter([f], enums.LineVisibility.CONTEXT_1, SGR_MODE)
    assert sc.visible_line_count() == 2
    sc = rc.filter([f], enums.LineVisibility.ONLY_MATCHING, SGR_MODE)
    assert sc.visible_line_count() == 1

    f.pop()
    f.add('line')
    sc = rc.filter([f], enums.LineVisibility.ALL, SGR_MODE)
    assert sc.hits_count() == 2
    assert sc.visible_line_count() == len(all_lines)
    sc = rc.filter([f], enums.LineVisibility.ONLY_MATCHING, SGR_MODE)
    assert sc.visible_line_count() == 2

    f.pop()
    f.add('Another')
    sc = rc.filter([f], enums.LineVisibility.ALL, SGR_MODE)
    assert sc.hits_count() == 1
    assert sc.visible_line_count() == len(all_lines)
    sc = rc.filter([f], enums.LineVisibility.CONTEXT_1, SGR_MODE)
    assert sc.visible_line_count() == 3
    sc = rc.filter([f], enums.LineVisibility.CONTEXT_2, SGR_MODE)
    assert sc.visible_line_count() == 4
    sc = rc.filter([f], enums.LineVisibility.CONTEXT_5, SGR_MODE)
    assert sc.visible_line_count() == 5
    sc = rc.filter([f], enums.LineVisibility.ONLY_MATCHING, SGR_MODE)
    assert sc.visible_line_count() == 1

    # Add a ruler
    f.pop()
    f.add('very')
    sc = rc.filter([f], enums.LineVisibility.CONTEXT_1, SGR_MODE)
    assert sc.hits_count() == 2


def test_display_content():
    '''Test models.DisplayContent'''
    dc = models.DisplayContent()

    rc = models.RawContent()
    rc.set_lines([
        'A very simple first line',
        'Another line',
        'And a third one'])
    sc = rc.filter([], enums.LineVisibility.ALL, SGR_MODE)

    dc = sc.layout(1, 1, True)
    assert dc
    dc = sc.layout(1, 1, False)
    assert dc

    f = models.Filter()
    f.add('third')
    sc = rc.filter([f], enums.LineVisibility.CONTEXT_1, SGR_MODE)
    dc = sc.layout(1, 1, True)
    assert dc


def test_offsets():
    '''Test models.Offsets'''

    co = models.Offsets()
    co.layout(10, 100)

    co.set_h_offset(0)
    co.set_h_offset(100)

    co.set_v_offset(0)
    assert co.voffset == 0
    co.set_v_offset(1)
    assert co.voffset == 1
    co.set_v_offset(200)
    assert co.voffset == 90


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
