from __future__ import annotations

from dataclasses import dataclass

from core import Message, NodeId, Network, Dispatcher, InstanceId
from protocols.types import ConsistentBroadcast, BinaryConsensus


@dataclass
class ProtocolFactory:
    protocol_type: type
    node_id: NodeId
    network: Network
    dispatcher: Dispatcher

    def create(self, instance_id, **kwargs):
        return self.protocol_type(instance_id, self.node_id, self.network, self.dispatcher, **kwargs)


@dataclass
class EchoConsistentBroadcast(ConsistentBroadcast):
    def start(self):
        pass

    def deliver(self, msg: Message):
        pass


@dataclass
class BrachaBinaryConsensus(BinaryConsensus):
    broadcast_factory: ProtocolFactory

    def __post_init__(self):
        sender = NodeId(0)
        b = self.broadcast_factory.create(
            instance_id=InstanceId(("broadcast", 0)),
            sender=sender,
            value="v" if self.node_id == sender else False)

    def start(self):
        pass

    def deliver(self, msg: Message):
        pass

