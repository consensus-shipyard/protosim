from dataclasses import dataclass
import logging
import unittest
from typing import Annotated

from core import EventQueue, Network, NodeId, Dispatcher, Node, Protocol, InstanceId, Group, Simulator
from injector import Injector, Scope, Factory
from protocols.implementations import EchoConsistentBroadcast

logging.basicConfig(level=logging.DEBUG)


@dataclass
class A:
    pass


def provide_group(injector: Injector, group_size: Annotated[int, 'group_size']) -> Group:
    group = Group([])
    for i in range(group_size):
        injector.enter_node_scope(NodeId(i))
        group.append(injector.get(Node))
        injector.exit_node_scope()
    return group


class TestInjector(unittest.TestCase):
    def setUp(self):
        self.injector = Injector()

    def test_simulator(self):
        injector = self.injector

        injector.provide(EventQueue, scope=Scope.SINGLETON)
        injector.provide(Network, scope=Scope.SINGLETON)
        injector.provide(Dispatcher, scope=Scope.NODE)

        injector.supply(InstanceId, instance=InstanceId(("root", 0)))
        injector.provide(Annotated[Protocol, 'root'], constructor=EchoConsistentBroadcast, scope=Scope.NODE)

        injector.supply(Annotated[int, 'group_size'], 2)
        injector.provide(Group, constructor=provide_group, scope=Scope.SINGLETON)

        injector.provide(Simulator, constructor=Simulator, scope=Scope.SINGLETON)

        self.assertIs(injector.get(EventQueue), injector.get(EventQueue))
        self.assertIs(injector.get(Network), injector.get(Network))

        simulator = injector.get(Simulator)
        self.assertIs(simulator, injector.get(Simulator))
        print("=====================================")
        print(simulator)
        simulator.run()

    def test_provide_unscoped(self):
        self.assertIs(type(self.injector.get(A)), A)
        self.assertIsNot(self.injector.get(A), self.injector.get(A))

    def test_provide_singleton(self):
        self.injector.provide(A, constructor=A, scope=Scope.SINGLETON)
        self.assertIs(self.injector.get(A), self.injector.get(A))

    def test_supply(self):
        self.injector.supply(int, 666)
        self.assertEqual(self.injector.get(int), 666)

    def test_annotated(self):
        self.injector.provide(int, constructor=lambda: 1, scope=Scope.SINGLETON)
        self.injector.provide(Annotated[int, 'me'], constructor=lambda: 666, scope=Scope.SINGLETON)
        self.assertEqual(self.injector.get(int), 1)
        self.assertEqual(self.injector.get(Annotated[int, 'me']), 666)

    def test_provide_event_queue(self):
        self.injector.provide(EventQueue, constructor=EventQueue, scope=Scope.SINGLETON)
        self.assertIs(self.injector.get(EventQueue), self.injector.get(EventQueue))
        self.assertEqual(self.injector.get(EventQueue), EventQueue())

    def test_factory(self):
        factory = self.injector.get(Factory[EventQueue])
        self.assertIs(type(factory.create()), EventQueue)
