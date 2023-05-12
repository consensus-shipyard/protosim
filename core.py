from __future__ import annotations

import heapq
import json
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import SimpleNamespace
from typing import NewType, Annotated, Any, Optional, Callable

import geopy.distance


@dataclass
class Event:
    delay: int  # The delay relative to the current instant with which the event will be processed.
    node_id: NodeId  # The id of the node that will process the event.
    message: Message  # The message that will be delivered to the node.

    def __lt__(self, other: Event):
        return self.node_id < other.node_id


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
        (instant, event) = heapq.heappop(self._events)
        self.clock = instant
        return event

    def __len__(self) -> int:
        return len(self._events)


class PathSegment(SimpleNamespace):
    def __hash__(self):
        return hash(tuple(self.__dict__.values()))


class Path(tuple[PathSegment, ...]):
    def append(self, segment: Optional[PathSegment] = None, **kwargs) -> Path:
        segment = PathSegment(**segment.__dict__, **kwargs) if segment else PathSegment(**kwargs)
        return Path(self + (segment,))


class InstanceId(PathSegment):
    pass


@dataclass
class Message:
    path: Path
    sender: NodeId   # The id of the node that sent the message.
    payload: Any = None  # The payload of the message.


@dataclass
class Network:
    event_queue: EventQueue
    latency_model: LatencyModel

    def send(self, msg: Message, dst_node_id: NodeId):
        delay = self.latency_model.get_latency(msg.sender, dst_node_id)
        self.event_queue.push(Event(delay, dst_node_id, msg))

    def broadcast(self, msg: Message, dst_node_ids: list[NodeId]):
        for node_id in dst_node_ids:
            self.send(msg, node_id)


@dataclass(kw_only=True)
class Protocol(ABC):
    instance_id: InstanceId
    node_id: NodeId
    network: Network
    dispatcher: Dispatcher
    parent: Optional[Protocol] = None
    path: Optional[Path] = None

    def __post_init__(self):
        parent_path = self.parent.path if self.parent else Path()
        self.path = parent_path.append(self.instance_id)

    def subscribe(self, path: Path, callback: Callable[[Message], None]):
        self.dispatcher.subscribe(path, callback)

    def send(self, msg: Message, destination: NodeId):
        self.network.send(msg, destination)

    def broadcast(self, msg: Message, destination: list[NodeId]):
        self.network.broadcast(msg, destination)

    # Method that is executed when the protocol is started.
    def start(self):
        raise NotImplementedError


@dataclass
class Node:
    id: NodeId  # The id of the node.
    root_protocol: Annotated[Protocol, 'root']  # The root protocol of the node.
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
        self._subscriptions: dict[Path, Callable[[Message], None]] = {}
        self._backlog: dict[Path, list[Message]] = {}

    # Delivers a message to the node for processing.
    def deliver(self, msg: Message):
        if msg.path in self._subscriptions:
            self._subscriptions[msg.path](msg)
        else:
            self._backlog.setdefault(msg.path, []).append(msg)
            logging.warning(f"Node {self.node_id} does not have a subscription for path {msg.path}")

    def subscribe(self, path: Path, callback: Callable[[Message], None]):
        if path in self._subscriptions:
            raise ValueError(f"Node {self.node_id} already has a subscription for path {path}")
        self._subscriptions[path] = callback
        if path in self._backlog:
            for msg in self._backlog[path]:
                self.deliver(msg)
            del self._backlog[path]


class NodeId(int):
    pass


Group = NewType('Group', list[NodeId])


@dataclass
class Simulator:
    nodes: list[Node]
    event_queue: EventQueue
    network: Network

    # Runs the simulation until there are no more events to execute.
    def run(self):
        logging.info("Starting simulation")

        for node in self.nodes:
            node.start()

        while self.event_queue:
            logging.debug(f"There are {len(self.event_queue)} event(s) in the queue")
            event = self.event_queue.pop()
            logging.debug(f"Node {event.node_id} processing message {event.message} at instant {self.event_queue.clock}")
            self.nodes[event.node_id].deliver(event.message)


class LatencyModel(ABC):
    @abstractmethod
    def get_latency(self, src: NodeId, dst: NodeId) -> int:
        pass


@dataclass
class GeoLatencyModel(LatencyModel):
    group: Group
    geo_data_file_path: str = "resources/lotus_geo_20231105.json"

    def __post_init__(self):
        with open(self.geo_data_file_path) as f:
            data = json.load(f)
            # The geographical locations of the population.
            population = [
                SimpleNamespace(
                    latitude=float(peer['latitude']),
                    longitude=float(peer['longitude']),
                    city=peer['city'],
                    country=peer['country'],
                ) for peer in data
            ]
            self._node_locations = {}
            for node_id in self.group:
                loc = random.choice(population)
                self._node_locations[node_id] = loc
                logging.info(f"Node {node_id} is located in {loc.city}, {loc.country}")

    def get_location(self, node_id: NodeId):
        return self._node_locations[node_id]

    def get_distance(self, src: NodeId, dst: NodeId) -> float:
        src_loc = self._node_locations[src].latitude, self._node_locations[src].longitude
        dst_loc = self._node_locations[dst].latitude, self._node_locations[dst].longitude
        return geopy.distance.distance(src_loc, dst_loc).km

    # Returns the latency in ms
    # 1.5 ms per 200 km
    def get_latency(self, src: NodeId, dst: NodeId) -> float:
        return self.get_distance(src, dst) / 200 * 1.5
