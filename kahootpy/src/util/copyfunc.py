import types

# Thanks https://stackoverflow.com/questions/6527633/how-can-i-make-a-deepcopy-of-a-function-in-python
def copy_func(f, name=None):
    '''
    return a function with same code, globals, defaults, closure, and
    name (or provide a new name)
    '''
    fn = types.FunctionType(f.__code__, f.__globals__, name or f.__name__,
        f.__defaults__, f.__closure__)
    # in case f was given attrs (note this dict is a shallow copy):
    fn.__dict__.update(f.__dict__)
    return fn
