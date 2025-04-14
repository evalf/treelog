import contextlib
import functools
import os
import typing

from ._io import sequence, directory
from .proto import Level


class DataLog:
    '''Output only data.'''

    def __init__(self, dirpath: str = os.curdir, names: typing.Callable[[str], typing.Iterable[str]] = sequence) -> None:
        self._names = functools.lru_cache(maxsize=32)(names)
        self._dir = directory(dirpath)

    @contextlib.contextmanager
    def open(self, filename: str, mode: str, level: Level) -> typing.Generator[typing.IO[typing.Any], None, None]:
        f, name = self._dir.openfirstunused(self._names(filename), mode)
        try:
            with f:
                yield f
        except:
            self._dir.unlink(name)
            raise

    def pushcontext(self, title: str) -> None:
        pass

    def popcontext(self) -> None:
        pass

    def recontext(self, title: str) -> None:
        pass

    def write(self, text: str, level: Level) -> None:
        pass
