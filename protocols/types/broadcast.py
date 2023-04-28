from abc import ABC
from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

from injector import inject

from core import Protocol, NodeId, node

V = TypeVar('V')


@dataclass
class ReliableBroadcast(Protocol, Generic[V], ABC):
    sender: NodeId
    value: Optional[V]


@node
@inject
@dataclass
class ConsistentBroadcast(Protocol, Generic[V], ABC):
    sender: NodeId
    value: Optional[V]
