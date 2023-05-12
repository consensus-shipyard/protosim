from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Annotated

from core import Message, NodeId, Network, Dispatcher, InstanceId, Protocol, Path, Group, PathSegment, EventQueue
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


@dataclass
class BroadcastPing(Protocol):
    group: Group
    pinger: Annotated[NodeId, 'pinger']
    event_queue: EventQueue

    def start(self):
        if self.node_id == self.pinger:
            self.subscribe(self.path.append(name="pong"), self.deliver_pong)
            # TODO: this construction is too low-level. Abstract details from the protocol implementer.
            self.broadcast(Message(path=self.path.append(name="ping"), sender=self.node_id, payload="ping"), destination=self.group)
        else:
            self.subscribe(self.path.append(name="ping"), self.deliver_ping)

    def deliver_ping(self, msg: Message):
        logging.info(f"Node {self.node_id} received ping from {msg.sender} at {self.event_queue.clock} ms")
        self.send(Message(path=self.path.append(name="pong"), sender=self.node_id, payload="pong"), destination=msg.sender)

    def deliver_pong(self, msg: Message):
        logging.info(f"Node {self.node_id} received pong from {msg.sender} at {self.event_queue.clock} ms")
