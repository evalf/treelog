from typing import TypeVar, Generic, Union, Iterable, Iterator, Generator, Optional, Type, Any, cast
import itertools
import functools
import warnings
import inspect
import types
from . import proto, _state

T = TypeVar('T')


class wrap(Generic[T]):
    '''Wrap iterable in consecutive title contexts.

    The wrapped iterable is identical to the original, except that prior to every
    next item a new log context is opened taken from the ``titles`` iterable. The
    wrapped object should be entered before use in order to ensure that this
    context is properly closed in case the iterator is prematurely abandoned.'''

    def __init__(self, titles: Union[Iterable[str], Generator[str, T, None]], iterable: Iterable[T]) -> None:
        self._titles = iter(titles)
        self._iterable = iter(iterable)
        self._log = None
        self._warn = False

    def __enter__(self) -> Iterator[T]:
        if self._log is not None:
            raise Exception('iter.wrap is not reentrant')
        self._log = _state.current
        self._log.pushcontext(next(self._titles))
        return iter(self)

    def __iter__(self) -> Generator[T, None, None]:
        if self._log is not None:
            cansend = inspect.isgenerator(self._titles)
            for value in self._iterable:
                self._log.recontext(cast(Generator[str, T, None], self._titles).send(
                    value) if cansend else next(self._titles))
                yield value
        else:
            with self:
                self._warn = True
                yield from self

    def __exit__(self, exctype: Optional[Type[BaseException]], excvalue: Optional[BaseException], tb: Optional[types.TracebackType]) -> None:
        if self._log is None:
            raise Exception('iter.wrap has not yet been entered')
        if self._warn and exctype is GeneratorExit:
            warnings.warn('unclosed iter.wrap', ResourceWarning)
        self._log.popcontext()
        self._log = None


def plain(title: str, *args: Any) -> wrap[Any]:
    '''Wrap arguments in simple enumerated contexts.

    Example: my context 1, my context 2, etc.
    '''

    titles = map((_escape(title) + ' {}').format, itertools.count())
    return wrap(titles, zip(*args) if len(args) > 1 else args[0])


def fraction(title: str, *args: Any, length: Optional[int] = None) -> wrap[Any]:
    '''Wrap arguments in enumerated contexts with length.

    Example: my context 1/5, my context 2/5, etc.
    '''

    if length is None:
        length = min(len(arg) for arg in args)
    titles = map((_escape(title) + ' {}/' + str(length)).format,
                 itertools.count())
    return wrap(titles, zip(*args) if len(args) > 1 else args[0])


def percentage(title: str, *args: Any, length: Optional[int] = None) -> wrap[Any]:
    '''Wrap arguments in contexts with percentage counter.

    Example: my context 5%, my context 10%, etc.
    '''

    if length is None:
        length = min(len(arg) for arg in args)
    if length:
        titles = map(
            (_escape(title) + ' {:.0f}%').format, itertools.count(step=100/length))
    else:
        titles = title + ' 100%',
    return wrap(titles, zip(*args) if len(args) > 1 else args[0])


def _escape(s: str) -> str:
    return s.replace('{', '{{').replace('}', '}}')
