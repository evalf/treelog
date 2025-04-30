from .proto import Level


class NullLog:

    def pushcontext(self, title: str) -> None:
        pass

    def popcontext(self) -> None:
        pass

    def recontext(self, title: str) -> None:
        pass

    def write(self, msg, level: Level) -> None:
        pass
