from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Optional

from core import Protocol, NodeId


@dataclass
class ConsistentBroadcast(Protocol, ABC):
    sender: NodeId
    value: Optional[str] = None


@dataclass
class BinaryConsensus(Protocol, ABC):
    value: bool
