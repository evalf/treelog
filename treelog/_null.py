from .proto import Level, oldproto


@oldproto.fromnew
class NullLog:

    def branch(self, title: str):
        return self

    def write(self, msg, level: Level) -> None:
        pass

    def close(self) -> None:
        pass
