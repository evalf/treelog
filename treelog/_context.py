import contextlib
import typing

from ._io import devnull
from .proto import Level


class ContextLog:
    '''Base class for loggers that keep track of the current list of contexts.

    The base class implements :meth:`context` and :meth:`open` which keep the
    attribute :attr:`currentcontext` up-to-date.

    .. attribute:: currentcontext

       A :class:`list` of contexts (:class:`str`\\s) that are currently active.
    '''

    def __init__(self) -> None:
        self.currentcontext = []  # type: typing.List[str]

    def pushcontext(self, title: str) -> None:
        self.currentcontext.append(title)
        self.contextchangedhook()

    def popcontext(self) -> None:
        self.currentcontext.pop()
        self.contextchangedhook()

    def recontext(self, title: str) -> None:
        self.currentcontext[-1] = title
        self.contextchangedhook()

    def contextchangedhook(self) -> None:
        pass

    def write(self, text: str, level: Level) -> None:
        # This function exists solely to make mypy happy.
        raise NotImplementedError

    @contextlib.contextmanager
    def open(self, filename: str, mode: str, level: Level) -> typing.Generator[typing.IO[typing.Any], None, None]:
        with devnull(mode) as f:
            yield f
        self.write(filename, level=level)
