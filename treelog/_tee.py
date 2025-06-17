import contextlib
import os
import tempfile

from .proto import Level, Log


class TeeLog:
    '''Forward messages to two underlying loggers.'''

    def __init__(self, baselog1: Log, baselog2: Log) -> None:
        self._baselog1 = baselog1
        self._baselog2 = baselog2

    def branch(self, title: str) -> None:
        return TeeLog(self._baselog1.branch(title), self._baselog2.branch(title))

    def write(self, msg, level: Level) -> None:
        self._baselog1.write(msg, level)
        self._baselog2.write(msg, level)

    def close(self) -> None:
        self._baselog1.close()
        self._baselog2.close()
