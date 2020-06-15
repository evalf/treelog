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

import contextlib, logging, sys, typing
from . import proto, _io

class ContextLog:
  '''Base class for loggers that keep track of the current list of contexts.

  The base class implements :meth:`context` and :meth:`open` which keep the
  attribute :attr:`currentcontext` up-to-date.

  .. attribute:: currentcontext

     A :class:`list` of contexts (:class:`str`\\s) that are currently active.
  '''

  def __init__(self) -> None:
    self.currentcontext = [] # type: typing.List[str]

  def pushcontext(self, title: str) -> None:
    self.currentcontext.append(title)
    self.contextchangedhook()

  def popcontext(self) -> None:
    self.currentcontext.pop()
    self.contextchangedhook()

  def recontext(self, title: str) -> None:
    self.currentcontext[-1] = title
    self.contextchangedhook()

  def contextchangedhook(self) -> None:
    pass

  def write(self, text: str, level: proto.Level) -> None:
    # This function exists solely to make mypy happy.
    raise NotImplementedError

  @contextlib.contextmanager
  def open(self, filename: str, mode: str, level: proto.Level) -> typing.Generator[typing.IO[typing.Any], None, None]:
    with _io.devnull(mode) as f:
      yield f
    self.write(filename, level=level)

class StdoutLog(ContextLog):
  '''Output plain text to stream.'''

  def write(self, text: str, level: proto.Level) -> None:
    print(' > '.join((*self.currentcontext, text)))

class StderrLog(ContextLog):
  '''Output plain text to stream.'''

  def write(self, text: str, level: proto.Level) -> None:
    print(' > '.join((*self.currentcontext, text)), file=sys.stderr)

class RichOutputLog(ContextLog):
  '''Output rich (colored,unicode) text to stream.'''

  _cmap = (
    '\033[1;30m', # debug: bold gray
    '\033[1m', # info: bold
    '\033[1;34m', # user: bold blue
    '\033[1;35m', # warning: bold purple
    '\033[1;31m') # error: bold red

  def __init__(self) -> None:
    super().__init__()
    self._current = '' # currently printed context
    _io.set_ansi_console()

  def contextchangedhook(self) -> None:
    _current = ''.join(item + ' > ' for item in self.currentcontext)
    if _current == self._current:
      return
    n = _first(c1 != c2 for c1, c2 in zip(_current, self._current))
    items = []
    if n == 0 and self._current:
      items.append('\r')
    elif n < len(self._current):
      items.append('\033[{}D'.format(len(self._current)-n))
    if n < len(_current):
      items.append(_current[n:])
    if len(_current) < len(self._current):
      items.append('\033[K')
    sys.stdout.write(''.join(items))
    sys.stdout.flush()
    self._current = _current

  def write(self, text: str, level: proto.Level) -> None:
    sys.stdout.write(''.join([self._cmap[level.value], text, '\033[0m\n', self._current]))

class LoggingLog(ContextLog):
  '''Log to Python's built-in logging facility.'''

  _levels = logging.DEBUG, logging.INFO, 25, logging.WARNING, logging.ERROR # type: typing.ClassVar[typing.Tuple[int, int, int, int, int]]

  def __init__(self, name: str = 'nutils') -> None:
    self._logger = logging.getLogger(name)
    super().__init__()

  def write(self, text: str, level: proto.Level) -> None:
    self._logger.log(self._levels[level.value], ' > '.join((*self.currentcontext, text)))

def _first(items: typing.Iterable[bool]) -> int:
  'return index of first truthy item, or len(items) of all items are falsy'
  i = 0
  for item in items:
    if item:
      break
    i += 1
  return i
