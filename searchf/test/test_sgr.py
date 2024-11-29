'''Unit tests for segments'''

from .. import enums
from .. import colors
from .. import sgr

# When running test with pytest, curses is not initialized and actual
# color pairs are not available. We just pretend that color pair id
# are actual valid color pair (both types resolving to int)
sgr.FG_BG_TO_COLOR_PAIR_FUNC = colors.get_color_pair_id


def test_processor():
    '''Test sgr.Processor()'''
    p = sgr.Processor()

    line = 'Some dummy line'
    a, new_line = p.filter(line, enums.SgrMode.NONE)
    assert len(a) == 0
    assert new_line == line
    a, new_line = p.filter(line, enums.SgrMode.REMOVE)
    assert len(a) == 0
    assert new_line == line
    a, new_line = p.filter(line, enums.SgrMode.PROCESS)
    assert len(a) == 0
    assert new_line == line

    line = '\x1B[30m30 \
Black\x1B[0m \
\x1B[30;1mbold\x1B[0m \
\x1B[30;2mdim\x1B[0m \
\x1B[30;4munderline\x1B[0m \
\x1B[40mreverse\x1B[0m \
\x1B[40;97mreverse\x1B[0m \
\x1B[40;30mreverse\x1B[0m'
    line_bare = '30 Black bold dim underline reverse reverse reverse'

    a, new_line = p.filter(line, enums.SgrMode.NONE)
    assert len(a) == 0
    assert new_line == line
    a, new_line = p.filter(line, enums.SgrMode.REMOVE)
    assert len(a) == 0
    assert new_line == line_bare
    a, new_line = p.filter(line, enums.SgrMode.PROCESS)
    assert len(a) == 6, a
    assert new_line == line_bare

    # Support for i18n and UTF8 encoding
    line = '\x1B[31m|아파트---|\x1B[0m*****\x1B[31m'
    line_bare = '|아파트---|*****'
    assert len(line_bare) == 13
    a, new_line = p.filter(line, enums.SgrMode.NONE)
    assert len(a) == 0
    assert new_line == line
    a, new_line = p.filter(line, enums.SgrMode.REMOVE)
    assert len(a) == 0
    assert new_line == line_bare
    a, new_line = p.filter(line, enums.SgrMode.PROCESS)
    assert len(a) == 1, a
    assert new_line == line_bare

    # Attributes carry over properly accross multiple lines
    a, new_line = p.filter('\x1B[31mSomething red', enums.SgrMode.PROCESS)
    assert len(a) == 1
    a, new_line = p.filter('still red\x1B[0m', enums.SgrMode.PROCESS)
    assert len(a) == 1
