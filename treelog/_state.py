from typing import Generator, ContextManager, Any, Optional, Callable, TypeVar
import operator
import contextlib
import functools
import io
import tempfile

from ._data import DataLog
from ._stdout import StdoutLog
from ._tee import TeeLog
from ._filter import FilterLog
from ._null import NullLog
from .proto import Level, Log, Data

current = FilterLog(TeeLog(StdoutLog(), DataLog()), minlevel=Level.info)


@contextlib.contextmanager
def set(logger: Log) -> Generator[Log, None, None]:
    '''Set logger as current.'''

    global current
    old = current
    try:
        current = logger
        yield logger
    finally:
        current = old


def add(logger: Log) -> ContextManager[Log]:
    '''Add logger to current.'''

    return set(TeeLog(current, logger))


def disable() -> ContextManager[Log]:
    '''Disable logger.'''

    return set(NullLog())


@contextlib.contextmanager
def context(title: str, *initargs: Any, **initkwargs: Any) -> Generator[Optional[Callable[..., None]], None, None]:
    '''Enterable context.

    Returns an enterable object which upon enter creates a context with a given
    title, to be automatically closed upon exit. In case additional arguments are
    given the title is used as a format string, and a callable is returned that
    allows for recontextualization from within the current with-block.'''

    log = current
    if initargs or initkwargs:
        format = title.format
        def reformat(*args, **kwargs):
            log.popcontext()
            log.pushcontext(format(*args, **kwargs))
        title = title.format(*initargs, **initkwargs)
    else:
        reformat = None
    log.pushcontext(title)
    try:
        yield reformat
    finally:
        log.popcontext()


def my_length_hint(iterable):
    if isinstance(iterable, (zip, map)):
        f, items = iterable.__reduce__()
        if f is map:
            items = items[1:]
        return min(filter(map(my_length_hint, items), lambda l: l != -1), default=-1)
    return operator.length_hint(iterable, -1)


def itercontext(title: str, iterable, length: Optional[int] = None):
    it = iter(iterable)
    try:
        item = next(it) # any emitted log events precede context
    except StopIteration:
        return # skip context if iterator is empty
    log = current
    log.pushcontext(title, my_length_hint(iterable) if length is None else length)
    try:
        log.nextiter()
        yield item
        for item in it:
            log.nextiter()
            yield item
    finally:
        log.popcontext()


T = TypeVar('T')

def withcontext(f: Callable[..., T]) -> Callable[..., T]:
    '''Decorator; executes the wrapped function in its own logging context.'''

    @functools.wraps(f)
    def wrapped(*args: Any, **kwargs: Any) -> T:
        with context(f.__name__):
            return f(*args, **kwargs)
    return wrapped


def write(level: Level, *args: Any, sep: str = ' ') -> None:
    '''Write message to log.

    Args
    ----
    *args : tuple of :class:`str`
        Values to be printed to the log.
    sep : :class:`str`
        String inserted between values, default a space.
    '''
    current.write(sep.join(map(str, args)), level)


@contextlib.contextmanager
def file(level: Level, name: str, mode: str, type: Optional[str] = None):
    '''Open file in logger-controlled directory.

    Args
    ----
    filename : :class:`str`
    mode : :class:`str`
        Should be either ``'w'`` (text) or ``'wb'`` (binary data).
    '''

    if mode == 'wb':
        binary = True
    elif mode == 'w':
        binary = False
    else:
        raise ValueError(f'invalid mode {mode!r}')
    logger = current
    with tempfile.TemporaryFile() as f, context(name):
        yield f if binary else io.TextIOWrapper(f, write_through=True)
        f.seek(0)
        data = f.read()
    current.write(Data(name, data, type), level)


def data(level: Level, name: str, data: bytes, type: Optional[str] = None):
    current.write(Data(name, data, type), level)


def partial(attr):
    if attr.endswith('file'):
        f = file
        level = attr[:-4]
    elif attr.endswith('data'):
        f = data
        level = attr[:-4]
    else:
        f = write
        level = attr
    return functools.partial(f, getattr(Level, level))
