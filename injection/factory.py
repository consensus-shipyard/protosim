from dataclasses import dataclass
from typing import Generic, Callable, Any, TypeVar

T = TypeVar("T")


@dataclass
class Factory(Generic[T]):
    constructor: Callable[..., T]
    default_args: dict[str, Any]

    def create(self, **kwargs):
        return self.constructor(**(self.default_args | kwargs))
