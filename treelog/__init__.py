import typing
import contextlib
import functools
import sys
from ._html import HtmlLog
from ._text import StdoutLog, StderrLog, RichOutputLog, LoggingLog
from ._silent import NullLog, DataLog, RecordLog
from ._forward import TeeLog, FilterLog
from . import iter, proto
version = '1.0'


for _log in TeeLog, FilterLog, NullLog, DataLog, RecordLog, StdoutLog, StderrLog, RichOutputLog, LoggingLog, HtmlLog:
    _log.__module__ = __name__
del _log

Log = None  # For backwards compatibility.

current = FilterLog(TeeLog(StdoutLog(), DataLog()),
                    minlevel=proto.Level.info)  # type: proto.Log


@contextlib.contextmanager
def set(logger: proto.Log) -> typing.Generator[proto.Log, None, None]:
    '''Set logger as current.'''

    global current
    old = current
    try:
        current = logger
        yield logger
    finally:
        current = old


def add(logger: proto.Log) -> typing.ContextManager[proto.Log]:
    '''Add logger to current.'''

    return set(TeeLog(current, logger))


def disable() -> typing.ContextManager[proto.Log]:
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


class _Print:

    def __init__(self, level: proto.Level) -> None:
        self._level = level  # type: typing.Final[proto.Level]

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


debug, info, user, warning, error = map(_Print, proto.Level)
debugfile, infofile, userfile, warningfile, errorfile = debug.open, info.open, user.open, warning.open, error.open
