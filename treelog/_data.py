import functools
import os
import typing

from ._path import makedirs, sequence
from .proto import Level, Data


class DataLog:
    '''Output only data.'''

    def __init__(self, dirpath: str = os.curdir, names: typing.Callable[[str], typing.Iterable[str]] = sequence) -> None:
        self._names = functools.lru_cache(maxsize=32)(names)
        self._path = makedirs(dirpath)

    def pushcontext(self, title: str) -> None:
        pass

    def popcontext(self) -> None:
        pass

    def recontext(self, title: str) -> None:
        pass

    def write(self, msg, level: Level) -> None:
        if isinstance(msg, Data):
            for filename in self._names(msg.name):
                try:
                    f = (self._path / filename).open('xb')
                except FileExistsError:
                    continue
                break
            else:
                raise ValueError('all filenames are in use')
            with f:
                f.write(msg.data)
