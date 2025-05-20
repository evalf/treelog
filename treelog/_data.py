import functools
import os
import typing

from ._path import makedirs, sequence, non_existent
from .proto import Level, Data, oldproto


@oldproto.fromnew
class DataLog:
    '''Output only data.'''

    def __init__(self, dirpath: str = os.curdir, names: typing.Callable[[str], typing.Iterable[str]] = sequence) -> None:
        self._names = functools.lru_cache(maxsize=32)(names)
        self._path = makedirs(dirpath)

    def branch(self, title: str):
        return self

    def write(self, msg, level: Level):
        if isinstance(msg, Data):
            _, f = non_existent(self._path, self._names(msg.name), lambda p: p.open('xb'))
            with f:
                f.write(msg.data)

    def close(self):
        pass
