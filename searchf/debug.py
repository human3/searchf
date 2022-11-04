'''Module exporting a function to output a debug string.'''

from typing import Any

OUT_FUNC: Any = None


def out(*argv) -> None:
    '''Outputs the given arguments.'''
    if OUT_FUNC:
        OUT_FUNC(*argv)
