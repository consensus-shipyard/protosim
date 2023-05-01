from __future__ import annotations
from typing import Optional

from dataclasses import dataclass

from injector import inject, ClassAssistedBuilder

# All these imports are necessary even if the IDE says otherwise!
# This what was causing that  annoying bug, not having these imports.
# The injector has a dynamic dependency on them.
from core import Message, InstanceId, NodeId, Network, Dispatcher
from protocols.types import ConsistentBroadcast, BinaryConsensus


@inject
@dataclass
class EchoConsistentBroadcast(ConsistentBroadcast):
    def start(self):
        pass

    def deliver(self, msg: Message):
        pass


@inject
@dataclass
class BrachaBinaryConsensus(BinaryConsensus):
    cb_builder: ClassAssistedBuilder[ConsistentBroadcast]

    def __post_init__(self):
        self._cb = self.cb_builder.build()

    def start(self):
        pass

    def deliver(self, msg: Message):
        pass

