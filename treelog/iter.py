# This entire module exists for backwards compatibility only.


from typing import Optional, Any

from . import _state


class _DummyContext:

    def __init__(self, it):
        self._it = it

    def __enter__(self):
        return self

    def __iter__(self):
        return self._it

    def __exit__(self, *args):
        del self._it


def fraction(title: str, *args: Any, length: Optional[int] = None):
    'Wrap arguments in enumerated contexts with length.'

    return _DummyContext(_state.itercontext(title, zip(*args) if len(args) > 1 else args[0], length=length))


def plain(title: str, *args: Any):
    'Wrap arguments in simple enumerated contexts.'

    return fraction(title, *args, length=-1)


percentage = fraction


def wrap(titles, iterable):
    return fraction(next(iter(titles)).rsplit(' ', 1)[0].strip(), iterable)
