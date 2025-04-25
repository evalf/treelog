import typing

from ._io import devnull
from .proto import Log, Level


class FilterLog:
    '''Filter messages based on level.'''

    def __init__(self, baselog: Log, minlevel: typing.Optional[Level] = None, maxlevel: typing.Optional[Level] = None) -> None:
        self._baselog = baselog
        self._minlevel = minlevel
        self._maxlevel = maxlevel

    def pushcontext(self, title: str) -> None:
        self._baselog.pushcontext(title)

    def popcontext(self) -> None:
        self._baselog.popcontext()

    def recontext(self, title: str) -> None:
        self._baselog.recontext(title)

    def _passthrough(self, level: Level) -> bool:
        '''Return True if messages of the given level should pass through.'''
        if self._minlevel is not None and level.value < self._minlevel.value:
            return False
        if self._maxlevel is not None and level.value > self._maxlevel.value:
            return False
        return True

    def write(self, text: str, level: Level) -> None:
        if self._passthrough(level):
            self._baselog.write(text, level)

    def open(self, filename: str, mode: str, level: Level) -> typing.ContextManager[typing.IO[typing.Any]]:
        return self._baselog.open(filename, mode, level) if self._passthrough(level) else devnull(mode)
