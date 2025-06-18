import contextlib
import tempfile
import typing

from .proto import Level, Log


def RecordLog(simplify: bool = True):
    return _RecordLog()


class _RecordLog(list):
    '''Record log events.

    The recorded events can be replayed to the logs that are currently active
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

    def branch(self, title: str):
        ctx = self.__class__()
        self.append((title, ctx))
        return ctx

    def write(self, msg, level: Level):
        self.append((msg, level))

    def close(self):
        pass

    def replay(self, log: typing.Optional[Log] = None) -> None:
        if log is None:
            from ._state import current as log
        for text, arg in self:
            if isinstance(arg, Level):
                log.write(text, arg)
            elif isinstance(arg, self.__class__):
                ctx = log.branch(text)
                arg.replay(ctx)
                ctx.close()
            else:
                raise ValueError(arg)
