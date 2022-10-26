'''Module exporting a function to output a debug string.'''
# pylint: disable=global-statement

OUT_FUNC = None

def set_output(output_func):
    '''Sets the global function that is handling output.'''
    global OUT_FUNC
    OUT_FUNC = output_func

def out(*argv) -> None:
    '''Outputs the given arguments.'''
    if OUT_FUNC:
        OUT_FUNC(*argv)
