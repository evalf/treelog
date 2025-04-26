import functools
import os
import typing

from ._io import sequence, directory
from .proto import Level, Data


class DataLog:
    '''Output only data.'''

    def __init__(self, dirpath: str = os.curdir, names: typing.Callable[[str], typing.Iterable[str]] = sequence) -> None:
        self._names = functools.lru_cache(maxsize=32)(names)
        self._dir = directory(dirpath)

    def pushcontext(self, title: str) -> None:
        pass

    def popcontext(self) -> None:
        pass

    def recontext(self, title: str) -> None:
        pass

    def write(self, msg, level: Level) -> None:
        if isinstance(msg, Data):
            f, name = self._dir.openfirstunused(self._names(msg.name), 'wb')
            f.write(msg.data)
