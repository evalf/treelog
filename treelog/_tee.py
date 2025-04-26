import contextlib
import os
import tempfile

from .proto import Level, Log


class TeeLog:
    '''Forward messages to two underlying loggers.'''

    def __init__(self, baselog1: Log, baselog2: Log) -> None:
        self._baselog1 = baselog1
        self._baselog2 = baselog2

    def pushcontext(self, title: str) -> None:
        self._baselog1.pushcontext(title)
        self._baselog2.pushcontext(title)

    def popcontext(self) -> None:
        self._baselog1.popcontext()
        self._baselog2.popcontext()

    def recontext(self, title: str) -> None:
        self._baselog1.recontext(title)
        self._baselog2.recontext(title)

    def write(self, msg, level: Level) -> None:
        self._baselog1.write(msg, level)
        self._baselog2.write(msg, level)
