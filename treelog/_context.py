from typing import Optional


class Iter:

    def __init__(self, text):
        self.text = text
        self.index = 0

    def next(self):
        self.index += 1

    def __str__(self):
        return f'{self.text} {self.index}'


class LengthIter(Iter):

    def __init__(self, text, length):
        self.length = length
        super().__init__(text)

    def __str__(self):
        return f'{super()}/{self.length}'


class ContextLog:
    '''Base class for loggers that keep track of the current list of contexts.

    The base class implements :meth:`context` and :meth:`open` which keep the
    attribute :attr:`currentcontext` up-to-date.

    .. attribute:: currentcontext

       A :class:`list` of contexts (:class:`str`\\s) that are currently active.
    '''

    def __init__(self) -> None:
        self.currentcontext = []

    def pushcontext(self, title: str, length: Optional[int] = None) -> None:
        self.currentcontext.append(title if length is None else Iter(title) if length == -1 else LengthIter(title, length))
        self.contextchangedhook()

    def popcontext(self) -> None:
        self.currentcontext.pop()
        self.contextchangedhook()

    def nextiter(self) -> None:
        self.currentcontext[-1].next()
        self.contextchangedhook()

    def contextchangedhook(self) -> None:
        pass
