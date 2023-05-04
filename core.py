from __future__ import annotations

import heapq
import logging
import random
from abc import ABC
from dataclasses import dataclass
from typing import NewType


@dataclass
class Event:
    delay: int  # The delay relative to the current instant with which the event will be processed.
    node_id: NodeId  # The id of the node that will process the event.
    message: Message  # The message that will be delivered to the node.


@dataclass
class EventQueue:
    clock: int = 0

    def __post_init__(self):
        self._events: list[tuple[int, Event]] = []

    # TODO: rename these
    def push(self, event: Event):
        instant = self.clock + event.delay
        heapq.heappush(self._events, (instant, event))

    def pop(self) -> Event:
        (delay, event) = heapq.heappop(self._events)
        self.clock += delay
        return event

    def __len__(self) -> int:
        return len(self._events)


InstanceId = NewType('InstanceId', tuple[str, int])
Path = NewType('Path', tuple[InstanceId, ...])


@dataclass
class Message:
    path: Path
    sender: NodeId   # The id of the node that sent the message.


@dataclass
class Network:
    event_queue: EventQueue

    def send(self, msg: Message, dst_node_id: NodeId):
        delay = self._latency()
        self.event_queue.push(Event(delay, dst_node_id, msg))

    def broadcast(self, msg: Message, dst_node_ids: list[NodeId]):
        for node_id in dst_node_ids:
            self.send(msg, node_id)

    @staticmethod
    def _latency():
        return random.choice([5, 50, 100])


# class NodeScope(Scope):
#     current_node_id: Optional[NodeId] = None
#     _node_context: dict[NodeId, dict[type, Provider]] = {}
#
#     def configure(self) -> None:
#         self._node_context = {}
#
#     def get(self, key, provider):
#         assert(self.current_node_id is not None)
#         context = self._node_context.setdefault(self.current_node_id, {})
#         return context.setdefault(key, InstanceProvider(provider.get(self.injector)))
#
#     def set_node(self, node_id: NodeId):
#         self.current_node_id = node_id
#
#
# # The @node decorator is used to mark a type with NodeScope
# node = ScopeDecorator(NodeScope)


@dataclass
class Protocol(ABC):
    instance_id: InstanceId
    node_id: NodeId
    network: Network
    dispatcher: Dispatcher
    # parent: Optional[Protocol] = None

    def subscribe(self, path: Path):
        self.dispatcher.subscribe(path, self)

    def send(self, msg: Message, destination: NodeId):
        self.network.send(msg, destination)

    def broadcast(self, msg: Message, destination: list[NodeId]):
        self.network.broadcast(msg, destination)

    # Method that is executed when the protocol is started.
    def start(self):
        raise NotImplementedError

    # Abstract method that should be overridden by subclasses.
    def deliver(self, msg: Message):
        raise NotImplementedError


@dataclass
class Node:
    id: NodeId  # The id of the node.
    root_protocol: Protocol  # The root protocol of the node.
    dispatcher: Dispatcher  # The dispatcher that will deliver messages to the node.

    def start(self):
        self.root_protocol.start()

    # Delivers a message to the node for processing.
    def deliver(self, msg: Message):
        self.dispatcher.deliver(msg)


@dataclass
class Dispatcher:
    node_id: NodeId

    def __post_init__(self):
        self._subscriptions: dict[Path, Protocol] = {}
        self._backlog: dict[Path, list[Message]] = {}

    # Delivers a message to the node for processing.
    def deliver(self, msg: Message):
        if msg.path in self._subscriptions:
            self._subscriptions[msg.path].deliver(msg)
        else:
            self._backlog.setdefault(msg.path, []).append(msg)
            logging.warning(f"Node {self.node_id} does not have a subscription for path {msg.path}")

    def subscribe(self, path: Path, protocol: Protocol):
        if path in self._subscriptions:
            raise ValueError(f"Node {self.node_id} already has a subscription for path {path}")
        self._subscriptions[path] = protocol
        if path in self._backlog:
            for msg in self._backlog[path]:
                self.deliver(msg)
            del self._backlog[path]


Group = NewType('Group', list[Node])


class NodeId(int):
    pass


@dataclass
class Simulator:
    nodes: Group
    event_queue: EventQueue
    network: Network

    # Runs the simulation until there are no more events to execute.
    def run(self):
        logging.info("Starting simulation")
        while self.event_queue:
            logging.debug(f"There are {len(self.event_queue)} event(s) in the queue")
            event = self.event_queue.pop()
            logging.debug(f"Node {event.node_id} processing message {event.message} at instant {self.event_queue.clock}")
            self.nodes[event.node_id].deliver(event.message)
