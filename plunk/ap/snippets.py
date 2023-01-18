import timeit
from functools import partial
from collections import deque


def only_if(locals_condition, sentinel=None):
    """Taken from: from know.examples.keyboard_and_audio import only_if

    Convenience wrapper to condition a function call on some function of its inputs.

    Important: The signature of locals_condition matter: It's through the names of its arguments that ``only_if``
    knows what values to extract from the inputs to compute the condition.

    >>> @only_if(lambda x: x > 0)
    ... def foo(x, y=1):
    ...     return x + y
    >>>
    >>> foo(1, y=2)
    3
    >>> assert foo(-1, 2) is None

    ``None`` is just the default sentinel. You can specify your own:

    >>> @only_if(lambda y: (y % 2) == 0, sentinel='y_is_not_even')
    ... def foo(x, y=1):
    ...     return x + y
    >>> foo(x=1, y=2)
    3
    >>> foo(1, y=3)
    'y_is_not_even'

    """
    from functools import wraps
    from i2 import Sig, call_forgivingly

    def wrapper(func):
        sig = Sig(func)

        @wraps(func)
        def locals_conditioned_func(*args, **kwargs):
            _kwargs = sig.kwargs_from_args_and_kwargs(args, kwargs)
            if call_forgivingly(locals_condition, **_kwargs):
                return func(*args, **kwargs)
            else:
                return sentinel

        return locals_conditioned_func

    return wrapper


def if_not_none(func, sentinel=None, search=None):
    """Return sentinel value if ALL func kwargs are None value"""

    def _is_not_none_dict(**kw):
        return not all(v is search for k, v in kw.items())

    return only_if(_is_not_none_dict, sentinel=sentinel)(func)


def if_no_none(func, sentinel=None, search=None):
    """Return sentinel value if ANY func kwargs are None value"""

    def _has_no_none_dict(**kw):
        return not any(v is search for k, v in kw.items())

    return only_if(_has_no_none_dict, sentinel=sentinel)(func)


def prefill_deque_with_value(value=None, maxlen: int = 10) -> deque:
    """Initialize deque prefilled with selected value

    >>> prefill_deque_with_value(-1, 10)
    deque([-1, -1, -1, -1, -1, -1, -1, -1, -1, -1], maxlen=10)

    :param value: Any value
    :param maxlen: Integer greater than zero
    :return:
    """

    d = deque((value,) * maxlen, maxlen=maxlen)
    return d


def _run_and_test_prefill_deque_with_value():
    print(f'{prefill_deque_with_value(0, 10)=}')
    t_prefill_deque_with_value = timeit.Timer(
        partial(prefill_deque_with_value, 0, int(1e6))
    )
    print(f'{t_prefill_deque_with_value.timeit(100)=}')


if __name__ == '__main__':
    _run_and_test_prefill_deque_with_value()
