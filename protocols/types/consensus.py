from abc import ABC
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from core import Protocol

V = TypeVar('V')


@dataclass
class BinaryConsensus(Protocol, ABC):
    proposal: bool


@dataclass
class MultivaluedConsensus(Protocol, Generic[V], ABC):
    proposal: V
