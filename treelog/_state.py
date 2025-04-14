import contextlib
import functools
import typing

from ._data import DataLog
from ._stdout import StdoutLog
from ._tee import TeeLog
from ._filter import FilterLog
from ._null import NullLog
from .proto import Level, Log

current = FilterLog(TeeLog(StdoutLog(), DataLog()), minlevel=Level.info)


@contextlib.contextmanager
def set(logger: Log) -> typing.Generator[Log, None, None]:
    '''Set logger as current.'''

    global current
    old = current
    try:
        current = logger
        yield logger
    finally:
        current = old


def add(logger: Log) -> typing.ContextManager[Log]:
    '''Add logger to current.'''

    return set(TeeLog(current, logger))


def disable() -> typing.ContextManager[Log]:
    '''Disable logger.'''

    return set(NullLog())


@contextlib.contextmanager
def context(title: str, *initargs: typing.Any, **initkwargs: typing.Any) -> typing.Generator[typing.Optional[typing.Callable[..., None]], None, None]:
    '''Enterable context.

    Returns an enterable object which upon enter creates a context with a given
    title, to be automatically closed upon exit. In case additional arguments are
    given the title is used as a format string, and a callable is returned that
    allows for recontextualization from within the current with-block.'''

    log = current
    if initargs or initkwargs:
        format = title.format
        # type: typing.Optional[typing.Callable[..., None]]
        reformat = lambda *args, **kwargs: log.recontext(
            format(*args, **kwargs))
        title = title.format(*initargs, **initkwargs)
    else:
        reformat = None
    log.pushcontext(title)
    try:
        yield reformat
    finally:
        log.popcontext()


T = typing.TypeVar('T')

def withcontext(f: typing.Callable[..., T]) -> typing.Callable[..., T]:
    '''Decorator; executes the wrapped function in its own logging context.'''

    @functools.wraps(f)
    def wrapped(*args: typing.Any, **kwargs: typing.Any) -> T:
        with context(f.__name__):
            return f(*args, **kwargs)
    return wrapped


class Print:

    def __init__(self, level: Level) -> None:
        self._level = level  # type: typing.Final[Level]

    def __call__(self, *args: typing.Any, sep: str = ' ') -> None:
        '''Write message to log.

        Args
        ----
        *args : tuple of :class:`str`
            Values to be printed to the log.
        sep : :class:`str`
            String inserted between values, default a space.
        '''
        current.write(sep.join(map(str, args)), self._level)

    @typing.overload
    def open(self, name: str, mode: typing.Literal['w']
             ) -> typing.ContextManager[typing.IO[str]]: ...

    @typing.overload
    def open(self, name: str, mode: typing.Literal['wb']
             ) -> typing.ContextManager[typing.IO[bytes]]: ...

    @typing.overload
    def open(self, name: str,
             mode: str) -> typing.ContextManager[typing.IO[typing.Any]]: ...

    def open(self, name: str, mode: str) -> typing.ContextManager[typing.IO[typing.Any]]:
        '''Open file in logger-controlled directory.

        Args
        ----
        filename : :class:`str`
        mode : :class:`str`
            Should be either ``'w'`` (text) or ``'wb'`` (binary data).
        '''
        if mode not in ('w', 'wb'):
            raise ValueError(
                "expected mode 'w' or 'wb' but got {!r}".format(mode))
        return current.open(name, mode, self._level)
