# Copyright (c) 2018 Evalf
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import os, random, functools, typing, types, sys

supports_fd = os.supports_dir_fd >= {os.open, os.rename, os.stat, os.unlink}

_devnull = os.open(os.devnull, os.O_WRONLY)
_opener = lambda path, flags: os.dup(_devnull)
devnull = functools.partial(open, os.devnull, opener=_opener)

class directory:
  '''Directory with support for dir_fd.'''

  def __init__(self, path: str) -> None:
    os.makedirs(path, exist_ok=True)
    if supports_fd:
      # convert to file descriptor
      self._fd = os.open(path, flags=os.O_RDONLY) # type: typing.Optional[int]
      self._path = None # type: typing.Optional[str]
    else:
      self._fd = None
      self._path = path
    self._rng = randomnames()

  def _join(self, name: str) -> str:
    return name if self._path is None else os.path.join(self._path, name)

  def open(self, filename: str, mode: str, *, encoding: typing.Optional[str] = None, umask: int = 0o666) -> typing.IO[typing.Any]:
    if mode not in ('w', 'wb'):
      raise ValueError('invalid mode: {!r}'.format(mode))
    return open(self._join(filename), mode+'+', encoding=encoding, opener=lambda name, flags: os.open(name, flags|os.O_CREAT|os.O_EXCL, mode=umask, dir_fd=self._fd))

  def unlink(self, filename: str) -> None:
    os.unlink(self._join(filename), dir_fd=self._fd)

  def stat(self, filename: str) -> os.stat_result:
    return os.stat(self._join(filename), dir_fd=self._fd)

  def rename(self, src: str, dst: str) -> None:
    os.rename(self._join(src), self._join(dst), src_dir_fd=self._fd, dst_dir_fd=self._fd)

  def openfirstunused(self, filenames: typing.Iterable[str], mode: str, *, encoding: typing.Optional[str] = None, umask: int = 0o666) -> typing.Tuple[typing.IO[typing.Any], str]:
    for filename in filenames:
      try:
        return self.open(filename, mode, encoding=encoding, umask=umask), filename
      except FileExistsError:
        pass
    raise ValueError('all filenames are in use')

  def openrandom(self, mode: str) -> typing.Tuple[typing.IO[typing.Any], str]:
    return self.openfirstunused(self._rng, mode)

  def __del__(self) -> None:
    if os and os.close and self._fd is not None:
      os.close(self._fd)

def sequence(filename: str) -> typing.Generator[str, None, None]:
  '''Generate file names a.b, a-1.b, a-2.b, etc.'''

  yield filename
  splitext = os.path.splitext(filename)
  i = 1
  while True:
    yield '-{}'.format(i).join(splitext)
    i += 1

def randomnames(characters: str = 'abcdefghijklmnopqrstuvwxyz0123456789_', length: int = 8) -> typing.Generator[str, None, None]:
  rng = random.Random()
  while True:
    yield ''.join(rng.choice(characters) for dummy in range(length))

def set_ansi_console() -> None:
  if sys.platform == "win32":
    import platform
    if platform.version() < '10.':
      raise RuntimeError('ANSI console mode requires Windows 10 or higher, detected {}'.format(platform.version()))
    import ctypes
    handle = ctypes.windll.kernel32.GetStdHandle(-11) # https://docs.microsoft.com/en-us/windows/console/getstdhandle
    mode = ctypes.c_uint32() # https://docs.microsoft.com/en-us/windows/desktop/WinProg/windows-data-types#lpdword
    ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)) # https://docs.microsoft.com/en-us/windows/console/getconsolemode
    mode.value |= 4 # add ENABLE_VIRTUAL_TERMINAL_PROCESSING
    ctypes.windll.kernel32.SetConsoleMode(handle, mode) # https://docs.microsoft.com/en-us/windows/console/setconsolemode

# vim:sw=2:sts=2:et
