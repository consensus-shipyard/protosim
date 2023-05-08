from enum import Enum, auto


class Scope(Enum):
    NODE = auto()
    SINGLETON = auto()
    UNSCOPED = auto()
