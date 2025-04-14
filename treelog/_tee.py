import contextlib
import os
import tempfile
import typing

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

    def write(self, text: str, level: Level) -> None:
        self._baselog1.write(text, level)
        self._baselog2.write(text, level)

    @contextlib.contextmanager
    def open(self, filename: str, mode: str, level: Level) -> typing.Generator[typing.IO[typing.Any], None, None]:
        with self._baselog1.open(filename, mode, level) as f1, self._baselog2.open(filename, mode, level) as f2:
            if f1.name == os.devnull:
                yield f2
            elif f2.name == os.devnull:
                yield f1
            elif f2.seekable() and f2.readable():
                yield f2
                f2.seek(0)
                f1.write(f2.read())
            elif f1.seekable() and f1.readable():
                yield f1
                f1.seek(0)
                f2.write(f1.read())
            else:
                with tempfile.TemporaryFile(mode+'+') as tmp:
                    yield tmp
                    tmp.seek(0)
                    data = tmp.read()
                f1.write(data)
                f2.write(data)
