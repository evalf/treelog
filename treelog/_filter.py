import typing

from .proto import Log, Level


class FilterLog:
    '''Filter messages based on level.'''

    def __init__(self, baselog: Log, minlevel: typing.Optional[Level] = None, maxlevel: typing.Optional[Level] = None) -> None:
        self._baselog = baselog
        self._minlevel = minlevel
        self._maxlevel = maxlevel

    def branch(self, title: str) -> None:
        return FilterLog(self._baselog.branch(title), self._minlevel, self._maxlevel)

    def _passthrough(self, level: Level) -> bool:
        '''Return True if messages of the given level should pass through.'''
        if self._minlevel is not None and level.value < self._minlevel.value:
            return False
        if self._maxlevel is not None and level.value > self._maxlevel.value:
            return False
        return True

    def write(self, msg, level: Level) -> None:
        if self._passthrough(level):
            self._baselog.write(msg, level)

    def close(self) -> None:
        self._baselog.close()
