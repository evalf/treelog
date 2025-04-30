from typing import Optional
import contextlib
import tempfile

from .proto import Level, Log


class RecordLog:
    '''Record log messages.

    The recorded messages can be replayed to the logs that are currently active
    by :meth:`replay`. Typical usage is caching expensive operations:

    >>> import treelog, pickle
    >>> # compute
    >>> record = treelog.RecordLog()
    >>> with treelog.add(record):
    ...   treelog.info('computing something expensive')
    ...   result = 'my expensive result'
    computing something expensive
    >>> raw = pickle.dumps((record, result))
    >>> # reuse
    >>> record, result = pickle.loads(raw)
    >>> record.replay()
    computing something expensive

    .. Note::
       Exceptions raised while in a :meth:`Log.context` are not recorded.
    '''

    def __init__(self, simplify: bool = True):
        # Replayable log messages.  Each entry is a tuple of `(cmd, *args)`, where
        # `cmd` is either 'pushcontext', 'popcontext', 'open',
        # 'close' or 'write'.  See `self.replay` below.
        self._simplify = simplify
        self._messages = []
        self._fid = 0  # internal file counter

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

    def write(self, msg, level: Level) -> None:
        self._messages.append(('write', msg, level))

    def replay(self, log: Optional[Log] = None) -> None:
        '''Replay this recorded log.

        All recorded messages and files will be written to the log that is either
        directly specified or currently active.'''

        files = {}
        if log is None:
            from ._state import current as log
        for cmd, *args in self._messages:
            if cmd == 'pushcontext':
                title, = args
                log.pushcontext(title)
            elif cmd == 'recontext':
                title, = args
                log.recontext(title)
            elif cmd == 'popcontext':
                log.popcontext()
            elif cmd == 'write':
                msg, level = args
                log.write(msg, level)
