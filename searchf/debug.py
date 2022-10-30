'''Module exporting a function to output a debug string.'''

OUT_FUNC = None


def out(*argv) -> None:
    '''Outputs the given arguments.'''
    if OUT_FUNC:
        OUT_FUNC(*argv)
