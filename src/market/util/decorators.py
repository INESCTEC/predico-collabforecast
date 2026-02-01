from functools import wraps
from time import time


def timeit(f):
    @wraps(f)
    def wrap(*args, **kw):
        ts = time()
        result = f(*args, **kw)
        print(f'Elapsed time - Func: {f.__name__} was {time() - ts:.2f}')
        return result
    return wrap
