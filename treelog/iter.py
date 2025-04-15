import itertools
import functools
import warnings
import inspect
import typing
import types
from . import proto, _state

T = typing.TypeVar('T')
T0 = typing.TypeVar('T0')
T1 = typing.TypeVar('T1')
T2 = typing.TypeVar('T2')
T3 = typing.TypeVar('T3')
T4 = typing.TypeVar('T4')
T5 = typing.TypeVar('T5')
T6 = typing.TypeVar('T6')
T7 = typing.TypeVar('T7')
T8 = typing.TypeVar('T8')
T9 = typing.TypeVar('T9')


class wrap(typing.Generic[T]):
    '''Wrap iterable in consecutive title contexts.

    The wrapped iterable is identical to the original, except that prior to every
    next item a new log context is opened taken from the ``titles`` iterable. The
    wrapped object should be entered before use in order to ensure that this
    context is properly closed in case the iterator is prematurely abandoned.'''

    def __init__(self, titles: typing.Union[typing.Iterable[str], typing.Generator[str, T, None]], iterable: typing.Iterable[T]) -> None:
        self._titles = iter(titles)
        self._iterable = iter(iterable)
        self._log = None  # type: typing.Optional[proto.Log]
        self._warn = False

    def __enter__(self) -> typing.Iterator[T]:
        if self._log is not None:
            raise Exception('iter.wrap is not reentrant')
        self._log = _state.current
        self._log.pushcontext(next(self._titles))
        return iter(self)

    def __iter__(self) -> typing.Generator[T, None, None]:
        if self._log is not None:
            cansend = inspect.isgenerator(self._titles)
            for value in self._iterable:
                self._log.recontext(typing.cast(typing.Generator[str, T, None], self._titles).send(
                    value) if cansend else next(self._titles))
                yield value
        else:
            with self:
                self._warn = True
                yield from self

    def __exit__(self, exctype: typing.Optional[typing.Type[BaseException]], excvalue: typing.Optional[BaseException], tb: typing.Optional[types.TracebackType]) -> None:
        if self._log is None:
            raise Exception('iter.wrap has not yet been entered')
        if self._warn and exctype is GeneratorExit:
            warnings.warn('unclosed iter.wrap', ResourceWarning)
        self._log.popcontext()
        self._log = None


@typing.overload
def plain(title: str, __arg0: typing.Iterable[T0]) -> wrap[T0]: ...


@typing.overload
def plain(title: str, __arg0: typing.Iterable[T0],
          __arg1: typing.Iterable[T1]) -> wrap[typing.Tuple[T0, T1]]: ...


@typing.overload
def plain(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1],
          __arg2: typing.Iterable[T2]) -> wrap[typing.Tuple[T0, T1, T2]]: ...


@typing.overload
def plain(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1],
          __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3]) -> wrap[typing.Tuple[T0, T1, T2, T3]]: ...


@typing.overload
def plain(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2],
          __arg3: typing.Iterable[T3], __arg4: typing.Iterable[T4]) -> wrap[typing.Tuple[T0, T1, T2, T3, T4]]: ...


@typing.overload
def plain(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3],
          __arg4: typing.Iterable[T4], __arg5: typing.Iterable[T5]) -> wrap[typing.Tuple[T0, T1, T2, T3, T4, T5]]: ...


@typing.overload
def plain(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3],
          __arg4: typing.Iterable[T4], __arg5: typing.Iterable[T5], __arg6: typing.Iterable[T6]) -> wrap[typing.Tuple[T0, T1, T2, T3, T4, T5, T6]]: ...


@typing.overload
def plain(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3], __arg4: typing.Iterable[T4],
          __arg5: typing.Iterable[T5], __arg6: typing.Iterable[T6], __arg7: typing.Iterable[T7]) -> wrap[typing.Tuple[T0, T1, T2, T3, T4, T5, T6, T7]]: ...


@typing.overload
def plain(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3], __arg4: typing.Iterable[T4],
          __arg5: typing.Iterable[T5], __arg6: typing.Iterable[T6], __arg7: typing.Iterable[T7], __arg8: typing.Iterable[T8]) -> wrap[typing.Tuple[T0, T1, T2, T3, T4, T5, T6, T7, T8]]: ...


@typing.overload
def plain(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3], __arg4: typing.Iterable[T4], __arg5: typing.Iterable[T5],
          __arg6: typing.Iterable[T6], __arg7: typing.Iterable[T7], __arg8: typing.Iterable[T8], __arg9: typing.Iterable[T9]) -> wrap[typing.Tuple[T0, T1, T2, T3, T4, T5, T6, T7, T8, T9]]: ...


@typing.overload
def plain(title: str, *args: typing.Any) -> wrap[typing.Any]: ...


def plain(title: str, *args: typing.Any) -> wrap[typing.Any]:
    '''Wrap arguments in simple enumerated contexts.

    Example: my context 1, my context 2, etc.
    '''

    titles = map((_escape(title) + ' {}').format, itertools.count())
    return wrap(titles, zip(*args) if len(args) > 1 else args[0])


@typing.overload
def fraction(title: str, __arg0: typing.Iterable[T0], *,
             length: typing.Optional[int] = ...) -> wrap[T0]: ...


@typing.overload
def fraction(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1],
             *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1]]: ...


@typing.overload
def fraction(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1],
             __arg2: typing.Iterable[T2], *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1, T2]]: ...


@typing.overload
def fraction(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2],
             __arg3: typing.Iterable[T3], *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1, T2, T3]]: ...


@typing.overload
def fraction(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3],
             __arg4: typing.Iterable[T4], *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1, T2, T3, T4]]: ...


@typing.overload
def fraction(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3],
             __arg4: typing.Iterable[T4], __arg5: typing.Iterable[T5], *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1, T2, T3, T4, T5]]: ...


@typing.overload
def fraction(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3], __arg4: typing.Iterable[T4],
             __arg5: typing.Iterable[T5], __arg6: typing.Iterable[T6], *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1, T2, T3, T4, T5, T6]]: ...


@typing.overload
def fraction(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3], __arg4: typing.Iterable[T4],
             __arg5: typing.Iterable[T5], __arg6: typing.Iterable[T6], __arg7: typing.Iterable[T7], *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1, T2, T3, T4, T5, T6, T7]]: ...


@typing.overload
def fraction(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3], __arg4: typing.Iterable[T4], __arg5: typing.Iterable[T5],
             __arg6: typing.Iterable[T6], __arg7: typing.Iterable[T7], __arg8: typing.Iterable[T8], *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1, T2, T3, T4, T5, T6, T7, T8]]: ...


@typing.overload
def fraction(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3], __arg4: typing.Iterable[T4], __arg5: typing.Iterable[T5],
             __arg6: typing.Iterable[T6], __arg7: typing.Iterable[T7], __arg8: typing.Iterable[T8], __arg9: typing.Iterable[T9], *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1, T2, T3, T4, T5, T6, T7, T8, T9]]: ...


@typing.overload
def fraction(title: str, *args: typing.Any,
             length: typing.Optional[int] = ...) -> wrap[typing.Any]: ...


def fraction(title: str, *args: typing.Any, length: typing.Optional[int] = None) -> wrap[typing.Any]:
    '''Wrap arguments in enumerated contexts with length.

    Example: my context 1/5, my context 2/5, etc.
    '''

    if length is None:
        length = min(len(arg) for arg in args)
    titles = map((_escape(title) + ' {}/' + str(length)).format,
                 itertools.count())
    return wrap(titles, zip(*args) if len(args) > 1 else args[0])


@typing.overload
def percentage(title: str, __arg0: typing.Iterable[T0],
               *, length: typing.Optional[int] = ...) -> wrap[T0]: ...


@typing.overload
def percentage(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1],
               *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1]]: ...


@typing.overload
def percentage(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1],
               __arg2: typing.Iterable[T2], *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1, T2]]: ...


@typing.overload
def percentage(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2],
               __arg3: typing.Iterable[T3], *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1, T2, T3]]: ...


@typing.overload
def percentage(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3],
               __arg4: typing.Iterable[T4], *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1, T2, T3, T4]]: ...


@typing.overload
def percentage(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3],
               __arg4: typing.Iterable[T4], __arg5: typing.Iterable[T5], *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1, T2, T3, T4, T5]]: ...


@typing.overload
def percentage(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3], __arg4: typing.Iterable[T4],
               __arg5: typing.Iterable[T5], __arg6: typing.Iterable[T6], *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1, T2, T3, T4, T5, T6]]: ...


@typing.overload
def percentage(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3], __arg4: typing.Iterable[T4],
               __arg5: typing.Iterable[T5], __arg6: typing.Iterable[T6], __arg7: typing.Iterable[T7], *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1, T2, T3, T4, T5, T6, T7]]: ...


@typing.overload
def percentage(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3], __arg4: typing.Iterable[T4], __arg5: typing.Iterable[T5],
               __arg6: typing.Iterable[T6], __arg7: typing.Iterable[T7], __arg8: typing.Iterable[T8], *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1, T2, T3, T4, T5, T6, T7, T8]]: ...


@typing.overload
def percentage(title: str, __arg0: typing.Iterable[T0], __arg1: typing.Iterable[T1], __arg2: typing.Iterable[T2], __arg3: typing.Iterable[T3], __arg4: typing.Iterable[T4], __arg5: typing.Iterable[T5],
               __arg6: typing.Iterable[T6], __arg7: typing.Iterable[T7], __arg8: typing.Iterable[T8], __arg9: typing.Iterable[T9], *, length: typing.Optional[int] = ...) -> wrap[typing.Tuple[T0, T1, T2, T3, T4, T5, T6, T7, T8, T9]]: ...


@typing.overload
def percentage(title: str, *args: typing.Any,
               length: typing.Optional[int] = ...) -> wrap[typing.Any]: ...


def percentage(title: str, *args: typing.Any, length: typing.Optional[int] = None) -> wrap[typing.Any]:
    '''Wrap arguments in contexts with percentage counter.

    Example: my context 5%, my context 10%, etc.
    '''

    if length is None:
        length = min(len(arg) for arg in args)
    if length:
        # type: typing.Iterable[str]
        titles = map(
            (_escape(title) + ' {:.0f}%').format, itertools.count(step=100/length))
    else:
        titles = title + ' 100%',
    return wrap(titles, zip(*args) if len(args) > 1 else args[0])


def _escape(s: str) -> str:
    return s.replace('{', '{{').replace('}', '}}')
