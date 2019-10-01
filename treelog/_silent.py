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

import os, contextlib, functools, typing, typing_extensions, tempfile
from . import proto, _io

class NullLog:

  def pushcontext(self, title: str) -> None:
    pass

  def popcontext(self) -> None:
    pass

  def recontext(self, title: str) -> None:
    pass

  def write(self, text: str , level: proto.Level) -> None:
    pass

  def open(self, filename: str, mode: str, level: proto.Level, id: typing.Optional[bytes]) -> typing_extensions.ContextManager[proto.IO]:
    return _io.devnull()

class DataLog:
  '''Output only data.'''

  def __init__(self, dirpath: str = os.curdir, names=_io.sequence) -> None:
    self._names = functools.lru_cache(maxsize=32)(names)
    self._dir = _io.directory(dirpath)

  @contextlib.contextmanager
  def open(self, filename: str, mode: str, level: proto.Level, id: typing.Optional[bytes]) -> typing.Generator[proto.IO, None, None]:
    f = None
    try:
      if id is None:
        f, fname = self._dir.temp(mode)
      else:
        self._dir.mkdir('.id')
        fname = os.path.join('.id', id.hex())
        f = self._dir.open(fname, mode)
      with f:
        yield f
    except:
      if f:
        self._dir.unlink(fname)
      raise
    self._dir.linkfirstunused(fname, self._names(filename))
    if id is None:
      self._dir.unlink(fname)

  def pushcontext(self, title: str) -> None:
    pass

  def popcontext(self) -> None:
    pass

  def recontext(self, title: str) -> None:
    pass

  def write(self, text: str, level: proto.Level) -> None:
    pass

class RecordLog:
  '''Record log messages.

  The recorded messages can be replayed to the logs that are currently active
  by :meth:`replay`. Typical usage is caching expensive operations::

      # compute
      with RecordLog() as record:
        result = compute_something_expensive()
      raw = pickle.dumps((record, result))
      # reuse
      record, result = pickle.loads(raw)
      record.replay()

  .. Note::
     Exceptions raised while in a :meth:`Log.context` are not recorded.
  '''

  def __init__(self, simplify: bool = True):
    # Replayable log messages.  Each entry is a tuple of `(cmd, *args)`, where
    # `cmd` is either 'pushcontext', 'popcontext', 'open',
    # 'close' or 'write'.  See `self.replay` below.
    self._simplify = simplify
    self._messages = [] # type: typing.List[typing.Any]
    self._fid = 0 # internal file counter
    self._seen = {} # type: typing.Dict[bytes, typing.Union[str, bytes]]

  def pushcontext(self, title: str) -> None:
    if self._simplify and self._messages and self._messages[-1][0] == 'popcontext':
      self._messages[-1] = 'recontext', title
    else:
      self._messages.append(('pushcontext', title))

  def recontext(self, title: str) -> None:
    if self._simplify and self._messages and self._messages[-1][0] in ('pushcontext', 'recontext'):
      self._messages[-1] = self._messages[-1][0], title
    else:
      self._messages.append(('recontext', title))

  def popcontext(self) -> None:
    if not self._simplify or not self._messages or self._messages[-1][0] not in ('pushcontext', 'recontext') or self._messages.pop()[0] == 'recontext':
      self._messages.append(('popcontext',))

  @contextlib.contextmanager
  def open(self, filename: str, mode: str, level: proto.Level, id: typing.Optional[bytes]) -> typing.Generator[proto.IO, None, None]:
    fid = self._fid
    self._fid += 1
    self._messages.append(('open', fid, filename, mode, level, id))
    try:
      data = self._seen.get(id) if id else None # type: typing.Optional[typing.Union[str, bytes]]
      if data is not None:
        with _io.devnull() as f:
          yield f
      else:
        with tempfile.TemporaryFile(mode+'+') as g:
          yield g
          g.seek(0)
          data = g.read()
        if id:
          self._seen[id] = data
    finally:
      self._messages.append(('close', fid, data))

  def write(self, text: str, level: proto.Level) -> None:
    self._messages.append(('write', text, level))

  def replay(self, log: typing.Optional[proto.Log] = None) -> None:
    '''Replay this recorded log.

    All recorded messages and files will be written to the log that is either
    directly specified or currently active.'''

    files = {}
    if log is None:
      from . import current
      log = current
    for cmd, *args in self._messages:
      if cmd == 'pushcontext':
        title, = args
        log.pushcontext(title)
      elif cmd == 'recontext':
        title, = args
        log.recontext(title)
      elif cmd == 'popcontext':
        log.popcontext()
      elif cmd == 'open':
        fid, filename, mode, level, id = args
        ctx = log.open(filename, mode, level=level, id=id)
        files[fid] = ctx, ctx.__enter__()
      elif cmd == 'close':
        fid, data = args
        ctx, f = files.pop(fid)
        if data is not None:
          f.write(data)
        ctx.__exit__(None, None, None)
      elif cmd == 'write':
        text, level = args
        log.write(text, level=level)
