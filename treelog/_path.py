import functools
import os
import pathlib
import typing


supports_fd = os.supports_dir_fd.issuperset((os.open, os.mkdir))


def makedirs(*pathsegments, exist_ok=True):
    path = pathlib.Path(*pathsegments)
    path.mkdir(parents=True, exist_ok=exist_ok)
    if not supports_fd:
        return path
    dir_fd = os.open(path, flags=os.O_RDONLY)
    return FDPath(dir_fd, '')


class FDPath:

    def __init__(self, dir_fd: int, path: str) -> None:
        self.dir_fd = dir_fd
        self.path = path

    @property
    def parent(self):
        return FDPath(self.dir_fd, os.path.dirname(self.path))

    def __truediv__(self, path: str) -> 'FDPath':
        return FDPath(self.dir_fd, os.path.join(self.path, path))

    def mkdir(self, mode=0o777, parents=False, exist_ok=False):
        try:
            os.mkdir(self.path, mode, dir_fd=self.dir_fd)
        except FileExistsError:
            if not exist_ok:
                raise
        except FileNotFoundError:
            if not parents:
                raise
            self.parent.mkdir(mode, parents=True, exist_ok=True)
            self.mkdir(mode)

    def open(self, mode: str, *, encoding: typing.Optional[str] = None) -> typing.IO[typing.Any]:
        return open(self.path, mode, encoding=encoding, opener=functools.partial(os.open, dir_fd=self.dir_fd))


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
