import functools
import os
import pathlib
import typing


supports_fd = os.open in os.supports_dir_fd


def makedirs(*pathsegments):
    path = pathlib.Path(*pathsegments)
    path.mkdir(parents=True, exist_ok=True)
    if not supports_fd:
        return path
    dir_fd = os.open(path, flags=os.O_RDONLY)
    return _FDDirPath(dir_fd)


def sequence(filename: str) -> typing.Generator[str, None, None]:
    '''Generate file names a.b, a-1.b, a-2.b, etc.'''

    yield filename
    splitext = os.path.splitext(filename)
    i = 1
    while True:
        yield '-{}'.format(i).join(splitext)
        i += 1


def non_existent(path, names, f):
    if isinstance(path, str):
        path = pathlib.Path(path)
    for name in names:
        try:
            return name, f(path / name)
        except FileExistsError:
            pass
        except PermissionError:
            # On Windows, trying to open a path that exists as a directory
            # triggers a permission error. To avoid a runaway iteration, we
            # continue to the next name only if the path indeed exists.
            if not isinstance(path, pathlib.Path) or not (path / name).exists():
                raise
    raise Exception('names exhausted')


class _FDDirPath:

    def __init__(self, dir_fd: int) -> None:
        self._opener = functools.partial(os.open, dir_fd=dir_fd)
        self._close = functools.partial(os.close, dir_fd)
        # by holding on to os.close we make sure it is still available during destruction

    def __truediv__(self, filename: str):
        return _FDFilePath(self, filename)

    def __del__(self) -> None:
        self._close()


class _FDFilePath:

    def __init__(self, directory, filename):
        self._directory = directory
        self._filename = filename

    def open(self, mode: str, *, encoding: typing.Optional[str] = None) -> typing.IO[typing.Any]:
        return open(self._filename, mode, encoding=encoding, opener=self._directory._opener)
