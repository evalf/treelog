import contextlib
import functools
import io
import tempfile
import typing
import warnings

from ._data import DataLog
from ._stdout import StdoutLog
from ._tee import TeeLog
from ._filter import FilterLog
from ._null import NullLog
from .proto import Level, Log, Data, Iter

current = FilterLog(TeeLog(StdoutLog(), DataLog()), minlevel=Level.info)


@contextlib.contextmanager
def set(logger: Log) -> typing.Generator[Log, None, None]:
    """Set logger as current."""

    global current
    old = current
    try:
        current = logger
        yield logger
    finally:
        current = old


def add(logger: Log) -> typing.ContextManager[Log]:
    """Add logger to current."""

    return set(TeeLog(current, logger))


def disable() -> typing.ContextManager[Log]:
    """Disable logger."""

    return set(NullLog())


@contextlib.contextmanager
def context(
    title: str, *initargs: typing.Any, **initkwargs: typing.Any
) -> typing.Generator[typing.Optional[typing.Callable[..., None]], None, None]:
    """Enterable context.

    Returns an enterable object which upon enter creates a context with a given
    title, to be automatically closed upon exit. In case additional arguments are
    given the title is used as a format string, and a callable is returned that
    allows for recontextualization from within the current with-block."""

    log = current
    if initargs or initkwargs:
        format = title.format

        def reformat(*args, **kwargs):
            log.recontext(format(*args, **kwargs))

        title = title.format(*initargs, **initkwargs)
    else:
        reformat = None
    log.pushcontext(title)
    try:
        yield reformat
    finally:
        log.popcontext()


T = typing.TypeVar("T")


def withcontext(f: typing.Callable[..., T]) -> typing.Callable[..., T]:
    """Decorator; executes the wrapped function in its own logging context."""

    @functools.wraps(f)
    def wrapped(*args: typing.Any, **kwargs: typing.Any) -> T:
        with context(f.__name__):
            return f(*args, **kwargs)

    return wrapped


class itercontext:
    def __init__(self, title, items):
        self._log = current
        self._title = title
        self._length = len(items)
        self._items = iter(items)
        self._index = 0
        self._open = False

    def __enter__(self):
        return self

    def __exit__(self, exctype, excvalue, tb):
        self.close()

    def __iter__(self):
        return self

    @property
    def _iter(self):
        return Iter(self._title, self._index, self._length)

    def __next__(self):
        if self._index == self._length:
            self.close()
            raise StopIteration
        if not self._open:
            self._log.pushcontext(self._iter)
            self._open = True
        else:
            self._log.recontext(self._iter)
        self._index += 1
        return next(self._items)

    def close(self):
        if self._open:
            self._log.popcontext()
            self._open = False

    def __del__(self):
        if self._open:
            warnings.warn(
                "destructing unclosed itercontext, consider entering it before iterating",
                ResourceWarning,
            )
            self.close()


def write(level: Level, *args: typing.Any, sep: str = " ") -> None:
    """Write message to log.

    Args
    ----
    *args : tuple of :class:`str`
        Values to be printed to the log.
    sep : :class:`str`
        String inserted between values, default a space.
    """
    current.write(sep.join(map(str, args)), level)


@contextlib.contextmanager
def file(level: Level, name: str, mode: str, type: typing.Optional[str] = None):
    """Open file in logger-controlled directory.

    Args
    ----
    filename : :class:`str`
    mode : :class:`str`
        Should be either ``'w'`` (text) or ``'wb'`` (binary data).
    """

    if mode == "wb":
        binary = True
    elif mode == "w":
        binary = False
    else:
        raise ValueError(f"invalid mode {mode!r}")
    with tempfile.TemporaryFile() as f, context(name):
        yield f if binary else io.TextIOWrapper(f, write_through=True)
        f.seek(0)
        data = f.read()
    current.write(Data(name, data, type), level)


def data(level: Level, name: str, data: bytes, type: typing.Optional[str] = None):
    current.write(Data(name, data, type), level)


def partial(attr):
    if attr.endswith("file"):
        f = file
        level = attr[:-4]
    elif attr.endswith("data"):
        f = data
        level = attr[:-4]
    else:
        f = write
        level = attr
    return functools.partial(f, getattr(Level, level))
