from typing import Optional

from .proto import Level


class NullLog:

    def pushcontext(self, title: str, length: Optional[int] = None) -> None:
        pass

    def popcontext(self) -> None:
        pass

    def nextiter(self) -> None:
        pass

    def write(self, msg, level: Level) -> None:
        pass
