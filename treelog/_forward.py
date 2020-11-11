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

import contextlib, typing, typing_extensions, tempfile, warnings, os
from . import proto, _io

class TeeLog:
  '''Forward messages to two underlying loggers.'''

  def __init__(self, *baselogs: proto.Log) -> None:
    self._baselogs = baselogs

  def pushcontext(self, title: str) -> None:
    for log in self._baselogs:
      log.pushcontext(title)

  def popcontext(self) -> None:
    for log in self._baselogs:
      log.popcontext()

  def recontext(self, title: str) -> None:
    for log in self._baselogs:
      log.recontext(title)

  def write(self, text: str, level: proto.Level) -> None:
    for log in self._baselogs:
      log.write(text, level)

  @contextlib.contextmanager
  def open(self, filename: str, mode: str, level: proto.Level) -> typing.Generator[typing.IO[typing.Any], None, None]:
    with contextlib.ExitStack() as stack:
      files = [stack.enter_context(log.open(filename, mode, level)) for log in self._baselogs]

      # Remove null files
      files = [f for f in files if f.name != os.devnull]
      if not files:
        with _io.devnull(mode) as f:
          yield f
        return

      # If only one file remains, use it and do nothing
      if len(files) == 1:
        yield files[0]
        return

      # If at least one file is seekable and readable, use it
      # and copy its data to the others
      try:
        i, src = next((i, f) for i, f in enumerate(files) if f.seekable() and f.readable())
      except StopIteration:
        pass
      else:
        del files[i]
        yield src
        src.seek(0)
        data = src.read()
        for tgt in files:
          tgt.write(data)
        return

      # Write to a temporary file then copy its data to the others
      with tempfile.TemporaryFile(mode + '+') as tmp:
        yield tmp
        tmp.seek(0)
        data = tmp.read()
      for f in files:
        f.write(data)

class FilterLog:
  '''Filter messages based on level.'''

  def __init__(self, baselog: proto.Log, minlevel: typing.Optional[proto.Level] = None, maxlevel: typing.Optional[proto.Level] = None) -> None:
    self._baselog = baselog
    self._minlevel = minlevel
    self._maxlevel = maxlevel

  def pushcontext(self, title: str) -> None:
    self._baselog.pushcontext(title)

  def popcontext(self) -> None:
    self._baselog.popcontext()

  def recontext(self, title: str) -> None:
    self._baselog.recontext(title)

  def _passthrough(self, level: proto.Level) -> bool:
    '''Return True if messages of the given level should pass through.'''
    if self._minlevel is not None and level.value < self._minlevel.value:
      return False
    if self._maxlevel is not None and level.value > self._maxlevel.value:
      return False
    return True

  def write(self, text: str, level: proto.Level) -> None:
    if self._passthrough(level):
      self._baselog.write(text, level)

  def open(self, filename: str, mode: str, level: proto.Level) -> typing_extensions.ContextManager[typing.IO[typing.Any]]:
    return self._baselog.open(filename, mode, level) if self._passthrough(level) else _io.devnull(mode)

# vim:sw=2:sts=2:et
